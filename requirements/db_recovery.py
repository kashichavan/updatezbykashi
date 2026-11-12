"""
Runtime recovery for a corrupt production SQLite file.

The build saves a checked copy of the database as db.sqlite3.release (see
build.sh). If the live file ever becomes unreadable ("file is not a database",
"database disk image is malformed"), the worker puts that copy back and then
exits, so gunicorn starts a fresh worker. Exiting matters: every thread that
still holds the broken file open is dropped with the process, so nothing can
keep writing into the replaced file.

Two things this module deliberately never does, because SQLite documents both
as causes of corruption (https://sqlite.org/howtocorrupt.html):
  * delete a -journal / -wal file while the database may still be in use;
  * open() and close() the database file with plain file I/O inside this
    process, which silently drops SQLite's POSIX locks for every connection.
"""

import logging
import os
import shutil
import sqlite3
import sys
import threading
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

_RECOVERY_LOCK = threading.Lock()
_CORRUPT_MARKERS = (
    'file is not a database',
    'database disk image is malformed',
    'malformed database schema',
    'unsupported file format',
)
_SIDECARS = ('-journal', '-wal', '-shm')


def db_path() -> Path:
    return Path(settings.BASE_DIR) / 'db.sqlite3'


def release_copy_path() -> Path:
    return Path(f"{db_path()}.release")


def is_database_corrupt_error(exc: Exception) -> bool:
    """True if the exception means the database file itself is unusable."""
    if not exc:
        return False
    msg = str(exc).lower()
    return any(marker in msg for marker in _CORRUPT_MARKERS)


def check_database_health(path: Path = None) -> tuple:
    """
    (True, 'ok') if the file opens as SQLite, passes quick_check and has the
    Django schema; otherwise (False, reason). Uses SQLite only, never raw I/O.
    """
    path = Path(path or db_path())
    if not path.exists():
        return False, f'{path.name} does not exist'
    try:
        conn = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=5)
        try:
            res = conn.execute('PRAGMA quick_check;').fetchone()
            if not res or res[0] != 'ok':
                return False, f'quick_check failed: {res}'
            conn.execute('SELECT 1 FROM django_migrations LIMIT 1;')
        finally:
            conn.close()
        return True, 'ok'
    except Exception as e:
        return False, str(e)


def _restart_worker():
    """End this worker so gunicorn starts a clean one. Never under tests or manage.py."""
    if 'test' in sys.argv or 'gunicorn' not in os.path.basename(sys.argv[0] if sys.argv else ''):
        return
    logger.warning("[DB Recovery] Restarting the worker so no thread keeps the old file open.")
    logging.shutdown()
    os._exit(3)


def _restore_release_copy() -> bool:
    live, release = db_path(), release_copy_path()
    healthy, reason = check_database_health(release)
    if not healthy:
        logger.error(f"[DB Recovery] No usable release copy ({reason}).")
        return False
    tmp = Path(f"{live}.restoring")
    shutil.copyfile(release, tmp)
    os.replace(tmp, live)  # atomic: readers see the old file or the new one, never half of each
    # The old file's journals belong to the discarded file; left behind they
    # would be replayed into the restored one.
    for ext in _SIDECARS:
        Path(f"{live}{ext}").unlink(missing_ok=True)
    logger.warning("[DB Recovery] Restored the database from the build's release copy.")
    return True


def _rebuild_from_snapshot() -> bool:
    """Last resort when there is no release copy: fresh schema plus the JSON snapshot."""
    from django.core.management import call_command
    from django.db import connections

    for conn in connections.all():
        conn.close()
    live = db_path()
    for ext in ('',) + _SIDECARS:
        Path(f"{live}{ext}").unlink(missing_ok=True)
    call_command('migrate', interactive=False, verbosity=0)
    snapshot = Path(settings.BASE_DIR) / 'backups' / 'kashii_full_snapshot_latest.json'
    if snapshot.exists():
        call_command('restore_snapshot', file=str(snapshot), verbosity=0)
    logger.warning("[DB Recovery] Rebuilt the database from the JSON snapshot.")
    return True


def auto_repair_database() -> bool:
    """
    Replace a corrupt live database and restart the worker. Returns False if
    the database turns out to be healthy or nothing could be restored.
    """
    if not _RECOVERY_LOCK.acquire(blocking=False):
        return False  # another thread is already repairing; this worker is about to restart
    try:
        healthy, reason = check_database_health()
        if healthy:
            return False  # transient error, the file is fine: leave it alone
        logger.error(f"[DB Recovery] Live database is corrupt ({reason}). Repairing...")
        try:
            repaired = _restore_release_copy() or _rebuild_from_snapshot()
        except Exception as e:
            logger.error(f"[DB Recovery] Repair failed: {e}", exc_info=True)
            return False
        if repaired:
            _restart_worker()
        return repaired
    finally:
        _RECOVERY_LOCK.release()
