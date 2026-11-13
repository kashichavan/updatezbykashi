from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from requirements.models import Category, JobGroup, JobPosting


class JobsApiGroupFilterTests(TestCase):
    def setUp(self):
        cache.clear()
        cat = Category.objects.create(name="Tech", slug="tech-filter")
        mk = lambda t: JobPosting.objects.create(
            title=t, company_name="Acme", category=cat, location="Pune",
            deadline=timezone.now() + timezone.timedelta(days=5))
        self.a, self.b, self.c = mk("Alpha"), mk("Beta"), mk("Gamma")
        self.group = JobGroup.objects.create(name="Drive One", slug="drive-one",
                                             deadline=timezone.now() + timezone.timedelta(days=5))
        self.group.jobs.add(self.a, self.b)

    def ids(self, **params):
        data = self.client.get("/api/jobs/", {"status": "ALL", **params}).json()
        return {j["id"] for j in data["jobs"]}, data

    def test_filter_by_group_and_no_group(self):
        in_group, data = self.ids(group=self.group.id)
        self.assertEqual(in_group, {self.a.id, self.b.id})
        self.assertEqual(data["jobs"][0]["groups"], [{"id": self.group.id, "name": "Drive One"}])
        no_group, _ = self.ids(group="none")
        self.assertEqual(no_group, {self.c.id})



class JobsFeedCacheInvalidationTests(TestCase):
    """A move between groups must show up on the next /api/jobs/ call, not five minutes later."""

    def setUp(self):
        from django.contrib.auth.models import User
        cache.clear()
        cat = Category.objects.create(name="Tech", slug="tech-cache")
        self.job = JobPosting.objects.create(
            title="Alpha", company_name="Acme", category=cat, location="Pune",
            deadline=timezone.now() + timezone.timedelta(days=5))
        dl = timezone.now() + timezone.timedelta(days=5)
        self.g1 = JobGroup.objects.create(name="One", slug="one-c", deadline=dl)
        self.g2 = JobGroup.objects.create(name="Two", slug="two-c", deadline=dl)
        self.g1.jobs.add(self.job)
        self.owner = User.objects.create_user("own", password="pw-123456", is_staff=True)

    def groups_of_job(self, **headers):
        data = self.client.get("/api/jobs/", {"status": "ALL"}, **headers).json()
        return [g["name"] for g in data["jobs"][0]["groups"]]

    def test_public_feed_sees_group_change_after_move(self):
        self.assertEqual(self.groups_of_job(), ["One"])  # now cached
        self.g1.jobs.remove(self.job)
        self.g2.jobs.add(self.job)
        self.assertEqual(self.groups_of_job(), ["Two"])

    def test_owner_request_skips_cache(self):
        from rest_framework_simplejwt.tokens import AccessToken
        auth = {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(self.owner)}"}
        self.assertEqual(self.groups_of_job(**auth), ["One"])
        res = self.client.get("/api/jobs/", {"status": "ALL"}, **auth)
        self.assertEqual(res["Cache-Control"], "no-store")

    def test_move_api_moves_and_copy_message(self):
        self.client.force_login(self.owner)
        res = self.client.post("/api/owner/groups/move-jobs/", {
            "job_ids": [self.job.id], "from_group_id": self.g1.id, "to_group_id": self.g2.id, "action": "move",
        }, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(self.job.groups.values_list("name", flat=True)), ["Two"])
        self.assertTrue(res.json()["message"].startswith("Moved 1 job"))
        res = self.client.post("/api/owner/groups/move-jobs/", {
            "job_ids": [self.job.id], "to_group_id": self.g1.id, "action": "copy",
        }, content_type="application/json")
        self.assertEqual(sorted(self.job.groups.values_list("name", flat=True)), ["One", "Two"])
        self.assertEqual(res.json()["message"], "Added 1 job to 'One'.")

    def test_group_list_returns_more_than_15_jobs(self):
        cat = Category.objects.first()
        for i in range(20):
            self.g2.jobs.add(JobPosting.objects.create(
                title=f"J{i}", company_name="Acme", category=cat,
                deadline=timezone.now() + timezone.timedelta(days=5)))
        self.client.force_login(self.owner)
        data = self.client.get("/api/owner/groups/", {"q": "Two"}).json()
        self.assertEqual(len(data["groups"][0]["jobs"]), 20)
