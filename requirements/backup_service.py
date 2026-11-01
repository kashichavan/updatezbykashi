import time
import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

_backup_lock = threading.Lock()
_last_backup_time = 0
_MIN_BACKUP_INTERVAL = 6 * 60 * 60  # Job imports save all day, and a dump is heavy on 0.1 CPU.
_BACKUP_TIMEOUT = 15 * 60


def _last_backup_at() -> float:
    """Newest backup time. It reads the file too, because restarts clear the variable."""
    snapshot = Path(settings.BASE_DIR) / 'backups' / 'kashii_full_snapshot_latest.json'
    try:
        return max(_last_backup_time, snapshot.stat().st_mtime)
    except OSError:
        return _last_backup_time



def _execute_backup():
    global _last_backup_time
    if not _backup_lock.acquire(blocking=False):
        logger.info("[Auto-Backup] Backup is already running in background, skipping redundant trigger.")
        return

    try:
        logger.info(f"[Auto-Backup] Starting database backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
        # A separate low-priority process, so the dump cannot starve page requests.
        subprocess.run(
            ['nice', '-n', '19', sys.executable, 'manage.py', 'auto_backup', '--format', 'all'],
            cwd=settings.BASE_DIR,
            check=True,
            timeout=_BACKUP_TIMEOUT,
        )
        _last_backup_time = time.time()
        logger.info("[Auto-Backup] Database backup completed successfully.")
    except Exception as e:
        logger.error(f"[Auto-Backup] Backup error: {str(e)}")
    finally:
        _backup_lock.release()

import sys

def trigger_auto_backup_async(force=False):
    """
    Triggers an asynchronous database backup in a detached background thread.
    Throttled to avoid overwhelming memory during rapid operations.
    """
    if 'test' in sys.argv:
        return

    if not force and (time.time() - _last_backup_at() < _MIN_BACKUP_INTERVAL):
        return

    thread = threading.Thread(target=_execute_backup, daemon=True, name="AutoBackupThread")
    thread.start()

def start_daily_backup_daemon():
    """
    Starts a background daemon thread that executes database backup every 24 hours.
    Does not run on boot to protect startup memory.
    """
    def _daemon_loop():
        logger.info("[Auto-Backup Daemon] Background daily backup scheduler initialized.")
        INTERVAL = 24 * 60 * 60  # 24 Hours
        while True:
            try:
                time.sleep(INTERVAL)
                logger.info("[Auto-Backup Daemon] Scheduled 24-hour interval elapsed. Triggering backup...")
                trigger_auto_backup_async(force=True)
            except Exception as e:
                logger.error(f"[Auto-Backup Daemon] Error in scheduler loop: {e}")
                time.sleep(300)

    t = threading.Thread(target=_daemon_loop, daemon=True, name="DailyAutoBackupDaemon")
    t.start()

def setup_backup_signals():
    """
    No-op placeholder for backward compatibility.
    Database backups are handled on-demand and via scheduled tasks to preserve web memory.
    """
    pass
