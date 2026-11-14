"""Who doesn't follow back, from the owner's Instagram data download.

Instagram's API gives follower counts but never the list of usernames, so the
owner uploads "Download your information → Followers and following" (JSON).
Nothing here logs in to Instagram or unfollows anyone: the owner gets a daily
list of 50 and taps Unfollow in the app.
"""
import json
import logging
import re
import zipfile

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

DAILY_LIMIT = 50
KEEP_SNAPSHOTS = 10
MAX_MEMBER_BYTES = 40 * 1024 * 1024  # uncompressed size cap per JSON file (zip-bomb guard)
USERNAME_RE = re.compile(r'^[A-Za-z0-9._]{1,30}$')
FOLLOWERS_RE = re.compile(r'(^|/)followers(_\d+)?\.json$')
FOLLOWING_RE = re.compile(r'(^|/)following\.json$')


class ExportError(ValueError):
    pass


def account_handle():
    return (getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', '') or 'instagram').lstrip('@').lower()


# --------------------------------------------------------------------------- parsing

def _username(entry):
    """Instagram has shipped several shapes; take the first usable name."""
    if not isinstance(entry, dict):
        return None, 0
    sld = (entry.get('string_list_data') or [{}])[0] or {}
    ts = sld.get('timestamp') or 0
    for cand in (sld.get('value'), entry.get('title')):
        if isinstance(cand, str) and USERNAME_RE.match(cand):
            return cand.lower(), ts
    tail = str(sld.get('href') or '').rstrip('/').split('/')[-1]
    if USERNAME_RE.match(tail) and tail != '_u':
        return tail.lower(), ts
    return None, 0


def _entries(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for v in obj.values():  # {"relationships_following": [...]}
            if isinstance(v, list):
                return v
    return []


def parse_export(fileobj):
    """Read a zip upload. Returns (followers: set, following: {user: ts})."""
    try:
        zf = zipfile.ZipFile(fileobj)
    except zipfile.BadZipFile:
        raise ExportError("That file isn't a zip. Upload the .zip Instagram emailed you, without unzipping it.")
    with zf:
        infos = zf.infolist()
        fol = [i for i in infos if FOLLOWERS_RE.search(i.filename)]
        ing = [i for i in infos if FOLLOWING_RE.search(i.filename)]
        if not fol or not ing:
            if any(i.filename.endswith(('followers_1.html', 'following.html')) for i in infos):
                raise ExportError("This download is in HTML format. Request it again and choose JSON.")
            raise ExportError("No followers/following lists in this zip. Request 'Followers and following' in JSON format.")

        def load(info):
            if info.file_size > MAX_MEMBER_BYTES:
                raise ExportError(f"{info.filename} is unexpectedly large; not reading it.")
            try:
                return json.loads(zf.read(info))
            except ValueError:
                raise ExportError(f"{info.filename} isn't valid JSON.")

        followers = set()
        for info in fol:
            for e in _entries(load(info)):
                u, _ = _username(e)
                if u:
                    followers.add(u)
        following = {}
        for info in ing:
            for e in _entries(load(info)):
                u, ts = _username(e)
                if u:
                    following[u] = int(ts or 0)
    if not following:
        raise ExportError("The following list in this download is empty.")
    return followers, following


# --------------------------------------------------------------------------- import / state

def import_snapshot(fileobj, handle=None):
    from requirements.models import IGFollowSnapshot, IGUnfollowMark
    handle = handle or account_handle()
    followers, following = parse_export(fileobj)
    snap = IGFollowSnapshot.objects.create(
        handle=handle, followers=sorted(followers), following=following,
        followers_count=len(followers), following_count=len(following))
    # The download is the truth: anyone marked "unfollowed" who is still followed goes back in the queue.
    requeued = IGUnfollowMark.objects.filter(
        handle=handle, status=IGUnfollowMark.STATUS_DONE, username__in=list(following)).delete()[0]
    old = IGFollowSnapshot.objects.filter(handle=handle).values_list('id', flat=True)[KEEP_SNAPSHOTS:]
    IGFollowSnapshot.objects.filter(id__in=list(old)).delete()
    return snap, requeued


def _today_start():
    now = timezone.localtime()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def build_state(handle=None):
    from requirements.models import IGFollowSnapshot, IGUnfollowMark
    handle = handle or account_handle()
    snaps = list(IGFollowSnapshot.objects.filter(handle=handle)[:2])
    state = {'handle': handle, 'daily_limit': DAILY_LIMIT, 'snapshot': None, 'live': live_counts()}
    if not snaps:
        return state
    snap = snaps[0]
    marks = {m.username: m for m in IGUnfollowMark.objects.filter(handle=handle)}
    followers = set(snap.followers)
    not_back = [(ts, u) for u, ts in snap.following.items() if u not in followers]
    queue = [u for _, u in sorted(not_back) if u not in marks]

    start = _today_start()
    done_today = sorted(
        (m for m in marks.values() if m.status == IGUnfollowMark.STATUS_DONE and m.marked_at >= start),
        key=lambda m: m.marked_at)
    remaining_today = max(0, DAILY_LIMIT - len(done_today))
    batch = [{'username': m.username, 'done': True} for m in done_today] + \
            [{'username': u, 'done': False} for u in queue[:remaining_today]]

    lost = []
    lost_since = None
    if len(snaps) > 1:
        prev = snaps[1]
        lost = sorted(set(prev.followers) - followers)
        lost_since = timezone.localtime(prev.taken_at).strftime('%d %b %Y')

    state.update({
        'snapshot': {
            'taken_at': timezone.localtime(snap.taken_at).strftime('%d %b %Y, %I:%M %p'),
            'followers': snap.followers_count, 'following': snap.following_count,
            'not_following_back': len(not_back),
        },
        'batch': batch,
        'done_today': len(done_today),
        'left': len(queue),
        'unfollowed_total': sum(1 for m in marks.values() if m.status == IGUnfollowMark.STATUS_DONE),
        'kept': sorted(u for u, m in marks.items() if m.status == IGUnfollowMark.STATUS_KEEP),
        'lost_since': lost_since,
        'lost': lost[:500],
        'lost_count': len(lost),
    })
    return state


def mark(username, action, handle=None):
    from requirements.models import IGUnfollowMark
    handle = handle or account_handle()
    username = (username or '').lower()
    if not USERNAME_RE.match(username) or action not in ('done', 'keep', 'undo'):
        raise ValueError('Bad username or action.')
    if action == 'undo':
        IGUnfollowMark.objects.filter(handle=handle, username=username).delete()
    else:
        IGUnfollowMark.objects.update_or_create(
            handle=handle, username=username,
            defaults={'status': action, 'marked_at': timezone.now()})


# --------------------------------------------------------------------------- live counts

def live_counts():
    """Follower/following counts from the connected account (the API has no lists). Cached 10 min."""
    cached = cache.get('ig_follow_live_counts')
    if cached is not None:
        return cached or None
    result = {}
    try:
        from requirements.models import IGAccount
        from requirements.services.ig_graph import _base
        acct = IGAccount.primary()
        if acct and acct.access_token:
            r = requests.get(f"{_base()}/me", params={
                'fields': 'username,followers_count,follows_count', 'access_token': acct.access_token}, timeout=8)
            data = r.json() if r.ok else {}
            if 'followers_count' in data:
                result = {'username': data.get('username', acct.username),
                          'followers': data['followers_count'], 'following': data.get('follows_count')}
    except Exception as exc:  # counts are a nice-to-have; never break the page
        logger.info("IG live counts unavailable: %s", exc)
    cache.set('ig_follow_live_counts', result, 600)
    return result or None
