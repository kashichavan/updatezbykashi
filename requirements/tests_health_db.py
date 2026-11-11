from unittest.mock import patch

from django.db import DatabaseError, OperationalError
from django.test import TestCase


class HealthCheckDatabaseTests(TestCase):
    def test_healthy_database_returns_ok(self):
        res = self.client.get('/healthz')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b'ok')

    def test_corrupt_database_returns_503(self):
        with patch('django.db.backends.utils.CursorWrapper.execute',
                   side_effect=DatabaseError('file is not a database')):
            res = self.client.get('/healthz')
        self.assertEqual(res.status_code, 503)

    def test_locked_database_still_healthy(self):
        with patch('django.db.backends.utils.CursorWrapper.execute',
                   side_effect=OperationalError('database is locked')):
            res = self.client.get('/healthz')
        self.assertEqual(res.status_code, 200)
