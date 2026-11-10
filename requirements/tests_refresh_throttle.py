"""Regression: homepage traffic must never stack background scraper threads."""
import threading
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from requirements import views

_RealThread = threading.Thread


@override_settings(ALLOWED_HOSTS=["testserver"])
class RefreshThrottleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.started = []
        self.release = threading.Event()

    def tearDown(self):
        self.release.set()
        for t in self.started:
            t.join(timeout=5)
        cache.clear()

    def _fake_thread(self, *args, **kwargs):
        real = _RealThread(*args, **kwargs)
        self.started.append(real)
        return real

    def test_many_homepage_hits_start_at_most_one_india_refresh(self):
        block = mock.Mock(side_effect=lambda **kw: self.release.wait(5))
        with mock.patch("requirements.job_aggregator.orchestrator.orchestrator.run_aggregation", block), \
             mock.patch("requirements.views.auto_import_from_jobdexo", return_value={}), \
             mock.patch("requirements.views.threading.Thread", side_effect=self._fake_thread):
            for _ in range(10):
                self.assertEqual(self.client.get("/").status_code, 200)
        india = [t for t in self.started if t.name == "AsyncIndiaJobsRefresh"]
        self.assertEqual(len(india), 1)

    def test_force_refresh_does_not_stack_while_one_is_running(self):
        block = mock.Mock(side_effect=lambda **kw: self.release.wait(5))
        with mock.patch("requirements.job_aggregator.orchestrator.orchestrator.run_aggregation", block), \
             mock.patch("requirements.views.auto_import_from_jobdexo", side_effect=lambda **kw: self.release.wait(5) and {}), \
             mock.patch("requirements.views.threading.Thread", side_effect=self._fake_thread):
            for _ in range(5):
                views.trigger_async_india_jobs_refresh(force=True)
                views.trigger_async_jobdexo_refresh(force=True)
        names = [t.name for t in self.started]
        self.assertEqual(names.count("AsyncIndiaJobsRefresh"), 1)
        self.assertEqual(names.count("AsyncJobdexoRefresh"), 1)

    def test_lock_is_released_after_refresh_finishes(self):
        with mock.patch("requirements.job_aggregator.orchestrator.orchestrator.run_aggregation", return_value={}):
            views.trigger_async_india_jobs_refresh(force=True)
            for t in threading.enumerate():
                if t.name == "AsyncIndiaJobsRefresh":
                    t.join(timeout=5)
        self.assertFalse(views._INDIA_REFRESH_LOCK.locked())
