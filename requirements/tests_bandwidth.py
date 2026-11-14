from django.test import TestCase


class BandwidthTests(TestCase):
    def test_pages_are_gzipped(self):
        res = self.client.get('/', HTTP_ACCEPT_ENCODING='gzip')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get('Content-Encoding'), 'gzip')

    def test_seo_scrapers_blocked_but_search_engines_allowed(self):
        bad = 'Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)'
        res = self.client.get('/api/jobs/', HTTP_USER_AGENT=bad)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.content, b'')
        # robots.txt stays readable so they learn to stop
        self.assertEqual(self.client.get('/robots.txt', HTTP_USER_AGENT=bad).status_code, 200)
        google = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        self.assertEqual(self.client.get('/api/jobs/', HTTP_USER_AGENT=google).status_code, 200)
        fb = 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)'
        self.assertEqual(self.client.get('/api/jobs/', HTTP_USER_AGENT=fb).status_code, 200)
