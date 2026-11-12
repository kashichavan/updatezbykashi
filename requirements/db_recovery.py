"""
Runtime Database Self-Healing and Recovery Engine.

Detects SQLite corruption (such as 'file is not a database', WAL salt mismatch,
or 'database disk image is malformed') and automatically heals the database
in-place at runtime without requiring container restarts or human intervention.
"""

import logging
import os
import sqlite3
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


def is_database_corrupt_error(exc: Exception) -> bool:
    """Checks if an exception message indicates physical database corruption."""
    if not exc:
        return False
    msg = str(exc).lower()
    return any(marker in msg for marker in _CORRUPT_MARKERS)


def check_database_health() -> tuple[bool, str]:
    """
    Directly checks the SQLite file integrity using standard sqlite3.
    Returns (True, 'ok') if healthy, or (False, error_reason) if corrupt.
    """
    db_path = settings.BASE_DIR / 'db.sqlite3'
    if not db_path.exists():
        return False, 'db.sqlite3 does not exist'

    try:
        size = db_path.stat().st_size
        if size == 0:
            return False, '0-byte empty file'

        with open(db_path, 'rb') as f:
            header = f.read(16)
        if header != b'SQLite format 3\x00':
            return False, f'invalid header: {header[:16]!r}'

        conn = sqlite3.connect(str(db_path), timeout=5)
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


def auto_repair_database() -> bool:
    """
    Self-healing routine. Thread-safe and process-safe.
    1. Closes Django connections.
    2. Clears stale -wal/-shm sidecar files to resolve salt mismatches.
    3. If db.sqlite3 is still corrupt or missing, rebuilds via migrate + restore_snapshot.
    """
    if not _RECOVERY_LOCK.acquire(blocking=False):
        logger.warning("[Self-Healing] Another recovery operation is already in progress, waiting...")
        with _RECOVERY_LOCK:
            # Check if previous recovery resolved it
            healthy, _ = check_database_health()
            return healthy

    try:
        logger.warning("🚨 [Self-Healing] Database corruption detected! Initiating automatic recovery...")

        # Step 1: Close all Django database connections cleanly
        try:
            from django.db import connections
            for conn in connections.all():
                conn.close()
        except Exception as e:
            logger.warning(f"[Self-Healing] Notice while closing connections: {e}")

        db_path = settings.BASE_DIR / 'db.sqlite3'

        # Step 2: Try lightweight sidecar purge (resolves WAL salt mismatch)
        for ext in ['-wal', '-shm', '-journal']:
            sidecar = Path(f"{db_path}{ext}")
            if sidecar.exists():
                try:
                    sidecar.unlink(missing_ok=True)
                    logger.info(f"[Self-Healing] Removed stale SQLite sidecar: {sidecar.name}")
                except Exception as del_err:
                    logger.warning(f"[Self-Healing] Could not delete {sidecar.name}: {del_err}")

        # Check if clearing sidecars was enough to restore database access
        healthy, reason = check_database_health()
        if healthy:
            logger.info("✅ [Self-Healing] Sidecar purge succeeded! Database is healthy.")
            # Reconnect WAL mode
            _reconnect_sqlite(db_path)
            return True

        logger.warning(f"[Self-Healing] Database file itself is damaged ({reason}). Rebuilding from snapshot...")

        # Step 3: Full restoration from backup snapshot
        for ext in ['', '-wal', '-shm', '-journal']:
            f = Path(f"{db_path}{ext}")
            if f.exists():
                try:
                    f.unlink(missing_ok=True)
                except Exception as del_err:
                    logger.warning(f"[Self-Healing] Could not remove {f.name}: {del_err}")

        from django.core.management import call_command

        # Run fresh migrations
        logger.info("[Self-Healing] Applying database schema migrations...")
        call_command('migrate', interactive=False, verbosity=0)

        # Restore from backup snapshot
        snapshot_path = settings.BASE_DIR / 'backups' / 'kashii_full_snapshot_latest.json'
        if snapshot_path.exists():
            logger.info(f"[Self-Healing] Restoring core data from snapshot: {snapshot_path.name}...")
            call_command('restore_snapshot', file=str(snapshot_path), verbosity=0)
        else:
            logger.warning("[Self-Healing] No snapshot file found; fresh empty database created.")

        # Seed production user and default categories
        try:
            seed_script = settings.BASE_DIR / 'requirements' / 'seed_prod.py'
            if seed_script.exists():
                import subprocess, sys
                subprocess.run([sys.executable, str(seed_script)], check=False, timeout=30)
        except Exception as seed_err:
            logger.warning(f"[Self-Healing] Notice running seed_prod: {seed_err}")

        _reconnect_sqlite(db_path)

        healthy, final_reason = check_database_health()
        if healthy:
            logger.info("🎉 [Self-Healing] SUCCESS: Database completely restored and healthy!")
            return True
        else:
            logger.error(f"❌ [Self-Healing] Recovery completed but check failed: {final_reason}")
            return False

    except Exception as exc:
        logger.error(f"❌ [Self-Healing] Fatal error during database recovery: {exc}", exc_info=True)
        return False
    finally:
        _RECOVERY_LOCK.release()


def _reconnect_sqlite(db_path: Path):
    """Checkpoints and configures clean WAL mode on repaired database."""
    try:
        conn = sqlite3.connect(str(db_path), timeout=30)
        conn.execute('PRAGMA busy_timeout = 20000;')
        conn.execute('PRAGMA journal_mode = WAL;')
        conn.execute('PRAGMA synchronous = NORMAL;')
        conn.execute('PRAGMA wal_autocheckpoint = 100;')
        conn.close()
    except Exception as e:
        logger.warning(f"[Self-Healing] Reconnect pragma warning: {e}")
