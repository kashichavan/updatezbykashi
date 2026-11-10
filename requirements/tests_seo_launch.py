"""Launch-SEO regression tests: titles, descriptions, share tags, schema,
sitemap, redirects, 404s and env-driven analytics/verification tags."""
import json
import re
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from debugger.learn_curriculum import CURRICULUM
from requirements.models import Category, JobPosting


def _meta(html, attr, name):
    return re.findall(rf'<meta {attr}="{re.escape(name)}" content="([^"]*)"', html)


def _title(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1).strip() if m else ""


def _ld_types(html):
    types = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        data = json.loads(block)  # must parse
        for node in data.get("@graph", [data]):
            types.append(node.get("@type"))
    return types


PUBLIC_PAGES = ["/", "/debugger/", "/resume/", "/sql/", "/about/", "/youtube/",
                "/privacy-policy/", "/terms/", "/disclaimer/", "/contact/"]


@override_settings(ALLOWED_HOSTS=["testserver"])
class SeoLaunchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Software Engineering", slug="software-engineering")
        cls.job = JobPosting.objects.create(
            title="Senior Full-Stack Software Engineer",
            company_name="Dodge Construction Network",
            category=cls.category,
            location="Kochi, India",
            stipend_salary="Competitive Package",
            eligibility="Open to eligible candidates with strong production experience in Python, React and cloud platforms",
            description="Build things.",
            apply_url="https://example.com/apply",
            status="ACTIVE",
            deadline=timezone.now() + timezone.timedelta(days=7),
        )

    def get_ok(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, url)
        return r.content.decode()

    # --- every public page -------------------------------------------------
    def test_public_pages_have_unique_short_titles_and_descriptions(self):
        titles = {}
        for url in PUBLIC_PAGES:
            html = self.get_ok(url)
            title = _title(html)
            desc = _meta(html, "name", "description")
            self.assertTrue(title, url)
            self.assertLessEqual(len(title), 60, f"{url} title too long: {title}")
            self.assertEqual(len(desc), 1, url)
            self.assertLessEqual(len(desc[0]), 160, f"{url} description too long")
            self.assertNotIn(title, titles, f"duplicate title on {url} and {titles.get(title)}")
            titles[title] = url

    def test_public_pages_have_one_set_of_share_tags_and_big_image(self):
        for url in PUBLIC_PAGES:
            html = self.get_ok(url)
            for prop in ("og:title", "og:description", "og:image", "og:url"):
                self.assertEqual(len(_meta(html, "property", prop)), 1, f"{url} {prop}")
            self.assertIn("og-default", _meta(html, "property", "og:image")[0])
            self.assertEqual(_meta(html, "property", "og:image:width"), ["1200"])
            self.assertNotIn("noindex", html.split("</head>")[0], url)

    def test_share_titles_are_page_specific(self):
        og = {u: _meta(self.get_ok(u), "property", "og:title")[0] for u in PUBLIC_PAGES}
        self.assertEqual(len(set(og.values())), len(og), og)

    def test_faq_schema_only_on_homepage_and_visible(self):
        home = self.get_ok("/")
        self.assertIn("FAQPage", _ld_types(home))
        self.assertIn('id="faq"', home)
        self.assertIn("What is Kashii Update?", home.split('id="faq"')[1])
        # The homepage FAQ must not leak site-wide (pages may carry their own FAQ).
        for url in PUBLIC_PAGES[1:]:
            self.assertNotIn("What is Kashii Update?", self.get_ok(url), url)

    # --- job pages ---------------------------------------------------------
    def test_job_page_tags(self):
        url = f"/category/{self.category.slug}/job/{self.job.uuid}/"
        html = self.get_ok(url)
        self.assertEqual(_title(html), "Dodge Construction Network Hiring: Senior Full-Stack Software Engineer")
        desc = _meta(html, "name", "description")[0]
        self.assertLessEqual(len(desc), 160)
        self.assertEqual(_meta(html, "property", "og:title"),
                         ["Dodge Construction Network Hiring: Senior Full-Stack Software Engineer"])
        self.assertEqual(len(_meta(html, "property", "og:description")), 1)
        types = _ld_types(html)
        self.assertIn("JobPosting", types)
        self.assertNotIn("FAQPage", types)

    # --- learn academy -----------------------------------------------------
    def test_learn_index_redirects_permanently_to_first_lesson(self):
        for lang, data in CURRICULUM.items():
            r = self.client.get(f"/debugger/learn/{lang}/")
            self.assertEqual(r.status_code, 301, lang)
            self.assertEqual(r["Location"], f"/debugger/learn/{lang}/{data['topics'][0]['slug']}/")

    def test_learn_unknown_paths_are_real_404s(self):
        self.assertEqual(self.client.get("/debugger/learn/not-a-language/").status_code, 404)
        self.assertEqual(self.client.get("/debugger/learn/python/not-a-lesson/").status_code, 404)

    def test_learn_lesson_titles_unique(self):
        seen = set()
        for lang, data in CURRICULUM.items():
            for topic in data["topics"]:
                t = _title(self.get_ok(f"/debugger/learn/{lang}/{topic['slug']}/"))
                self.assertNotIn(t, seen)
                seen.add(t)

    # --- crawl infrastructure ----------------------------------------------
    def test_sitemap_lists_only_canonical_200_urls(self):
        xml = self.get_ok("/sitemap.xml")
        locs = re.findall(r"<loc>([^<]+)</loc>", xml)
        self.assertTrue(locs)
        for lang in CURRICULUM:
            self.assertNotIn(f"http://testserver/debugger/learn/{lang}/", locs)
        for loc in locs:
            path = loc.replace("http://testserver", "") or "/"
            if "/debugger/learn/" in path or path in PUBLIC_PAGES:
                self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_robots_allows_crawlers_and_points_to_sitemap(self):
        txt = self.get_ok("/robots.txt")
        self.assertIn("Sitemap:", txt)
        self.assertNotRegex(txt, r"(?m)^Disallow: /\s*$")

    def test_unknown_url_returns_404(self):
        self.assertEqual(self.client.get("/this-page-does-not-exist-123/").status_code, 404)

    # --- env-driven tags ---------------------------------------------------
    def test_tracking_tags_absent_without_env(self):
        html = self.get_ok("/")
        for needle in ("googletagmanager.com/gtag", "clarity.ms/tag", "google-site-verification", "msvalidate.01"):
            self.assertNotIn(needle, html)

    def test_tracking_tags_render_with_valid_env(self):
        env = {
            "GA_MEASUREMENT_ID": "G-AB12CD34EF",
            "CLARITY_PROJECT_ID": "k3x9abcd12",
            "GOOGLE_SITE_VERIFICATION": "abcDEF123_-abcDEF123_-xyz",
            "BING_SITE_VERIFICATION": "0123456789abcdef0123456789abcdef",
        }
        with mock.patch.dict("os.environ", env):
            html = self.get_ok("/")
        self.assertIn("gtag/js?id=G-AB12CD34EF", html)
        self.assertIn('"k3x9abcd12"', html)
        self.assertEqual(_meta(html, "name", "google-site-verification"), ["abcDEF123_-abcDEF123_-xyz"])
        self.assertEqual(_meta(html, "name", "msvalidate.01"), ["0123456789ABCDEF0123456789ABCDEF"])

    def test_tracking_env_values_are_validated(self):
        bad = {"GA_MEASUREMENT_ID": 'G-1"><script>alert(1)</script>', "CLARITY_PROJECT_ID": "x'</script>"}
        with mock.patch.dict("os.environ", bad):
            html = self.get_ok("/")
        self.assertNotIn("alert(1)", html)
        self.assertNotIn("gtag/js", html)
        self.assertNotIn("clarity.ms/tag", html)

    def test_csp_allows_analytics(self):
        csp = self.client.get("/")["Content-Security-Policy"]
        for host in ("www.googletagmanager.com", "www.clarity.ms", "scripts.clarity.ms"):
            self.assertIn(host, csp)
