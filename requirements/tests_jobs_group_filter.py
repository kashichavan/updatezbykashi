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

