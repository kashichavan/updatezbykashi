"""Comment 'LINK' → must follow → DM the post's apply link (also for story replies).

Flow (Instagram only allows a follow check once the person has messaged us):
1. Comment containing LINK on a reel we posted → public reply + private reply with a
   "Send me the link" button (payload LINK:<media_id>).
2. They tap it (postback) → follow check → link DM, or "Follow first" with
   [Visit profile] and [I'm following ✅] (payload LINK:<media_id> again).
3. A reply to one of our stories goes straight to step 2.
"""
import logging
import random
import re

from django.db import IntegrityError

from . import ig_graph

logger = logging.getLogger(__name__)

KEYWORD_RE = re.compile(r'\blink\b', re.IGNORECASE)
PUBLIC_REPLIES = ['Sent! Check your DMs 📩', 'Link sent to your DMs ✅', 'Check your inbox 🚀']


def _first_time(key):
    from ..models import IGHandledEvent
    try:
        IGHandledEvent.objects.create(key=key[:200])
        return True
    except IntegrityError:
        return False


def _post_for(media_id):
    from ..models import IGPost
    return IGPost.objects.filter(media_id=str(media_id)).select_related('account', 'job').first()


def _account_for(ig_user_id):
    from ..models import IGAccount
    return IGAccount.objects.filter(ig_user_id=str(ig_user_id), is_active=True).first()


def deliver_or_gate(account, igsid, post):
    """Send the link if they follow, otherwise ask them to follow first."""
    if ig_graph.follows_us(account, igsid):
        title = f" for {post.job.title} at {post.job.company_name}" if post.job else ''
        ig_graph.send_message(account, {'id': igsid},
                              f"Here's your apply link{title} 👇\n{post.link_url}\n\nAll the best! 💼",
                              buttons=[{'title': 'Apply now', 'url': post.link_url}])
        return 'delivered'
    ig_graph.send_message(account, {'id': igsid},
                          "You're almost there 😊 Follow the page first, then tap “I'm following ✅” "
                          "and I'll send the apply link right away.",
                          buttons=[{'title': 'Visit profile', 'url': f"https://instagram.com/{account.username}"},
                                   {'title': "I'm following ✅", 'payload': f"LINK:{post.media_id}"}])
    return 'gated'


def handle_comment(account, value):
    comment_id = str(value.get('id', ''))
    text = value.get('text', '') or ''
    media_id = str((value.get('media') or {}).get('id', ''))
    sender = str((value.get('from') or {}).get('id', ''))
    if not comment_id or sender == account.ig_user_id or not KEYWORD_RE.search(text):
        return 'ignored'
    post = _post_for(media_id)
    if not post or not _first_time(f"comment:{comment_id}"):
        return 'ignored'
    try:
        ig_graph.reply_to_comment(account, comment_id, random.choice(PUBLIC_REPLIES))
    except ig_graph.IGError as exc:
        logger.warning("Public comment reply failed: %s", exc)
    ig_graph.send_message(account, {'comment_id': comment_id},
                          "Hey! 👋 Tap below and I'll send you the apply link ✨",
                          buttons=[{'title': 'Send me the link', 'payload': f"LINK:{post.media_id}"}])
    return 'prompted'


def handle_messaging(account, event):
    sender = str((event.get('sender') or {}).get('id', ''))
    if not sender or sender == account.ig_user_id:
        return 'ignored'
    msg = event.get('message') or {}
    if msg.get('is_echo'):
        return 'ignored'
    payload = (event.get('postback') or {}).get('payload') or (msg.get('quick_reply') or {}).get('payload') or ''
    media_id = ''
    if payload.startswith('LINK:'):
        media_id = payload[5:]
        key = f"postback:{(event.get('postback') or {}).get('mid') or event.get('timestamp')}:{sender}"
    else:
        media_id = str(((msg.get('reply_to') or {}).get('story') or {}).get('id', ''))
        key = f"message:{msg.get('mid', '')}"
    if not media_id:
        return 'ignored'
    post = _post_for(media_id)
    if not post or not _first_time(key):
        return 'ignored'
    return deliver_or_gate(account, sender, post)


def handle_webhook(payload):
    """Entry point for the Instagram webhook body. Errors are logged, never raised."""
    results = []
    for entry in payload.get('entry', []):
        account = _account_for(entry.get('id', ''))
        if not account:
            continue
        try:
            for change in entry.get('changes', []):
                if change.get('field') == 'comments':
                    results.append(handle_comment(account, change.get('value') or {}))
            for event in entry.get('messaging', []):
                results.append(handle_messaging(account, event))
        except Exception as exc:  # one bad event must not stop the rest
            logger.exception("Instagram webhook handling failed: %s", exc)
            results.append('error')
    return results
