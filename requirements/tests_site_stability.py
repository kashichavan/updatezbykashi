import time
from unittest import mock

from django.test import SimpleTestCase, override_settings

from requirements import ai_engine, backup_service


class FakeResponse:
    headers = {}

    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


BROKEN_JSON = {"error": {"code": "json_validate_failed", "failed_generation": "Asha Rao private resume"}}
GOOD_REPLY = {"choices": [{"message": {"content": "{}"}}]}


class HealthCheckTests(SimpleTestCase):
    @override_settings(ALLOWED_HOSTS=["kashiiupdatez.online"], SECURE_SSL_REDIRECT=True)
    def test_answers_without_host_match_or_redirect(self):
        response = self.client.get('/healthz', HTTP_HOST='10.0.0.1:10000')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')


class RobotsTests(SimpleTestCase):
    def test_debugger_links_with_queries_are_blocked_but_the_page_is_not(self):
        lines = self.client.get('/robots.txt').content.decode().splitlines()
        self.assertIn('Disallow: /debugger/?', lines)
        self.assertNotIn('Disallow: /debugger/', lines)


class BackupThrottleTests(SimpleTestCase):
    def setUp(self):
        patcher = mock.patch.object(backup_service, 'sys')
        self.sys = patcher.start()
        self.sys.argv = ['gunicorn']
        self.addCleanup(patcher.stop)

    def test_job_saves_do_not_start_a_backup_soon_after_the_last_one(self):
        with mock.patch.object(backup_service, '_last_backup_at', return_value=time.time() - 3600), \
                mock.patch.object(backup_service.threading, 'Thread') as thread:
            backup_service.trigger_auto_backup_async()
        thread.assert_not_called()

    def test_backup_starts_once_the_interval_has_passed(self):
        with mock.patch.object(backup_service, '_last_backup_at', return_value=time.time() - 7 * 3600), \
                mock.patch.object(backup_service.threading, 'Thread') as thread:
            backup_service.trigger_auto_backup_async()
        thread.assert_called_once()

    def test_backup_runs_outside_the_web_process(self):
        with mock.patch.object(backup_service.subprocess, 'run') as run:
            backup_service._execute_backup()
        command = run.call_args.args[0]
        self.assertEqual(command[:3], ['nice', '-n', '19'])
        self.assertIn('auto_backup', command)


class GroqErrorTests(SimpleTestCase):
    def setUp(self):
        for name, value in (('get_groq_api_key', 'key'), ('_groq_models_to_try', ['first', 'second'])):
            patcher = mock.patch.object(ai_engine, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_broken_json_moves_to_the_next_model(self):
        replies = [FakeResponse(400, BROKEN_JSON), FakeResponse(200, GOOD_REPLY)]
        with mock.patch.object(ai_engine.requests, 'post', side_effect=replies) as post:
            result = ai_engine._call_groq_chat([], 0.2, 100, True, 5, 3)
        self.assertEqual(result, '{}')
        self.assertEqual(post.call_count, 2)

    def test_resume_text_stays_out_of_logs_and_errors(self):
        with mock.patch.object(ai_engine.requests, 'post', return_value=FakeResponse(400, BROKEN_JSON)), \
                self.assertLogs('requirements.ai_engine', level='WARNING') as logs, \
                self.assertRaises(RuntimeError) as caught:
            ai_engine._call_groq_chat([], 0.2, 100, True, 5, 2)
        self.assertNotIn('Asha', ' '.join(logs.output))
        self.assertNotIn('Asha', str(caught.exception))
