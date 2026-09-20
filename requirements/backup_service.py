import time
import logging
import threading
import gc
from datetime import datetime
from django.core.management import call_command
from django.db import reset_queries, close_old_connections

logger = logging.getLogger(__name__)

_backup_lock = threading.Lock()
_last_backup_time = 0
_MIN_BACKUP_INTERVAL = 600  # Debounce: at most 1 manual/auto backup every 10 minutes

def _execute_backup():
    global _last_backup_time
    if not _backup_lock.acquire(blocking=False):
        logger.info("[Auto-Backup] Backup is already running in background, skipping redundant trigger.")
        return

    try:
        close_old_connections()
        reset_queries()
        logger.info(f"[Auto-Backup] Starting database backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
        call_command('auto_backup', format='all')
        _last_backup_time = time.time()
        logger.info("[Auto-Backup] Database backup completed successfully.")
    except Exception as e:
        logger.error(f"[Auto-Backup] Backup error: {str(e)}")
    finally:
        try:
            close_old_connections()
            reset_queries()
            gc.collect()
        except Exception:
            pass
        _backup_lock.release()

def trigger_auto_backup_async(force=False):
    """
    Triggers an asynchronous database backup in a detached background thread.
    Throttled to avoid overwhelming memory during rapid operations.
    """
    global _last_backup_time
    now = time.time()
    if not force and (now - _last_backup_time < _MIN_BACKUP_INTERVAL):
        logger.info(f"[Auto-Backup] Throttled: last backup was {int(now - _last_backup_time)}s ago (min interval: {_MIN_BACKUP_INTERVAL}s).")
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
