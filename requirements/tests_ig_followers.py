import io
import json
import zipfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from requirements.models import IGFollowSnapshot, IGUnfollowMark
from requirements.services import ig_followers


def make_zip(followers, following, old_format=False):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('connections/followers_and_following/followers_1.json', json.dumps([
            {"title": "", "string_list_data": [{"href": f"https://www.instagram.com/{u}", "value": u, "timestamp": 1700000000}]}
            for u in followers]))
        if old_format:
            ing = {"relationships_following": [
                {"string_list_data": [{"href": f"https://www.instagram.com/{u}", "value": u, "timestamp": 1600000000 + i}]}
                for i, u in enumerate(following)]}
        else:
            ing = {"relationships_following": [
                {"title": u, "string_list_data": [{"href": f"https://www.instagram.com/_u/{u}", "timestamp": 1600000000 + i}]}
                for i, u in enumerate(following)]}
        z.writestr('connections/followers_and_following/following.json', json.dumps(ing))
    return buf.getvalue()


@override_settings(INSTAGRAM_ACCOUNT_HANDLE='tester')
@mock.patch('requirements.services.ig_followers.live_counts', return_value=None)
class IGFollowersTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user('own', password='pw-123456', is_staff=True)
        self.client.force_login(self.owner)
        self.following = [f"acct_{i:03d}" for i in range(80)]

    def upload(self, data):
        return self.client.post('/api/owner/ig-followers/import/',
                                {'file': SimpleUploadedFile('ig.zip', data, content_type='application/zip')})

    def test_parses_both_formats(self, _live):
        for old in (False, True):
            f, g = ig_followers.parse_export(io.BytesIO(make_zip(['acct_000', 'fan'], self.following[:3], old)))
            self.assertEqual(f, {'acct_000', 'fan'})
            self.assertEqual(list(g), ['acct_000', 'acct_001', 'acct_002'])

    def test_daily_batch_is_capped_at_50_and_oldest_first(self, _live):
        res = self.upload(make_zip(self.following[:10], self.following))
        self.assertEqual(res.status_code, 200)
        s = res.json()
        self.assertEqual(s['snapshot']['not_following_back'], 70)
        self.assertEqual(len(s['batch']), 50)
        self.assertEqual(s['batch'][0]['username'], 'acct_010')
        # Unfollowing one keeps it in today's list as done and does not pull in a 51st.
        s = self.client.post('/api/owner/ig-followers/mark/', {'username': 'acct_010', 'action': 'done'},
                             content_type='application/json').json()
        self.assertEqual(len(s['batch']), 50)
        self.assertEqual(s['done_today'], 1)
        self.assertTrue(s['batch'][0]['done'])
        # Keep removes it and the next account fills the slot.
        s = self.client.post('/api/owner/ig-followers/mark/', {'username': 'acct_011', 'action': 'keep'},
                             content_type='application/json').json()
        names = [r['username'] for r in s['batch']]
        self.assertNotIn('acct_011', names)
        self.assertEqual(len(names), 50)
        self.assertEqual(s['kept'], ['acct_011'])

    def test_reimport_requeues_fake_done_and_lists_unfollowers(self, _live):
        self.upload(make_zip(self.following[:10], self.following))
        ig_followers.mark('acct_010', 'done')   # marked, but never actually unfollowed
        ig_followers.mark('acct_012', 'done')   # really unfollowed
        following2 = [u for u in self.following if u != 'acct_012']
        s = self.upload(make_zip(self.following[:8], following2)).json()
        self.assertEqual(s['imported']['requeued'], 1)
        self.assertFalse(IGUnfollowMark.objects.filter(username='acct_010').exists())
        self.assertEqual(s['lost'], ['acct_008', 'acct_009'])

    def test_bad_uploads(self, _live):
        self.assertEqual(self.upload(b'not a zip').status_code, 400)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as z:
            z.writestr('connections/followers_and_following/followers_1.html', '<html>')
            z.writestr('connections/followers_and_following/following.html', '<html>')
        res = self.upload(buf.getvalue())
        self.assertIn('HTML', res.json()['error'])
        self.assertEqual(self.client.post('/api/owner/ig-followers/mark/', {'username': '../x', 'action': 'done'},
                                          content_type='application/json').status_code, 400)

    def test_old_snapshots_pruned(self, _live):
        data = make_zip(['a'], ['b'])
        for _ in range(ig_followers.KEEP_SNAPSHOTS + 3):
            self.upload(data)
        self.assertEqual(IGFollowSnapshot.objects.count(), ig_followers.KEEP_SNAPSHOTS)

    def test_requires_owner(self, _live):
        self.client.logout()
        self.assertEqual(self.client.get('/api/owner/ig-followers/').status_code, 401)
        self.assertEqual(self.upload(make_zip(['a'], ['b'])).status_code, 401)
