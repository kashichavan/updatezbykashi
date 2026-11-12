from unittest.mock import patch

from django.db import DatabaseError, OperationalError
from django.test import TestCase
from requirements.db_recovery import check_database_health, is_database_corrupt_error


class HealthCheckDatabaseTests(TestCase):
    def test_healthy_database_returns_ok(self):
        res = self.client.get('/healthz')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b'ok')

    def test_corrupt_database_triggers_repair_and_returns_ok(self):
        with patch('requirements.middleware.database_is_corrupt', return_value=True), \
             patch('requirements.middleware.auto_repair_database', return_value=True):
            res = self.client.get('/healthz')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b'ok (repaired)')

    def test_corrupt_database_returns_503_if_repair_fails(self):
        with patch('requirements.middleware.database_is_corrupt', return_value=True), \
             patch('requirements.middleware.auto_repair_database', return_value=False):
            res = self.client.get('/healthz')
        self.assertEqual(res.status_code, 503)

    def test_locked_database_still_healthy(self):
        with patch('django.db.backends.utils.CursorWrapper.execute',
                   side_effect=OperationalError('database is locked')):
            res = self.client.get('/healthz')
        self.assertEqual(res.status_code, 200)

    def test_corrupt_error_detection(self):
        self.assertTrue(is_database_corrupt_error(DatabaseError('file is not a database')))
        self.assertTrue(is_database_corrupt_error(OperationalError('database disk image is malformed')))
        self.assertFalse(is_database_corrupt_error(OperationalError('database is locked')))

    def test_health_check_returns_healthy_on_clean_db(self):
        healthy, reason = check_database_health()
        self.assertTrue(healthy)
        self.assertEqual(reason, 'ok')
