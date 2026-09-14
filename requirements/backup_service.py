import time
import logging
import threading
from datetime import datetime
from django.core.management import call_command
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)

_backup_lock = threading.Lock()
_last_backup_time = 0
_MIN_BACKUP_INTERVAL = 300  # Debounce: at most 1 auto-backup every 5 minutes

def _execute_backup():
    global _last_backup_time
    if not _backup_lock.acquire(blocking=False):
        logger.info("[Auto-Backup] Backup is already running in background, skipping redundant trigger.")
        return

    try:
        logger.info(f"[Auto-Backup] Starting auto-triggered database backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
        call_command('auto_backup', format='all')
        _last_backup_time = time.time()
        logger.info("[Auto-Backup] Auto-triggered database backup completed successfully.")
    except Exception as e:
        logger.error(f"[Auto-Backup] Auto-triggered backup error: {str(e)}")
    finally:
        _backup_lock.release()

def trigger_auto_backup_async(force=False):
    """
    Triggers an asynchronous database backup (both JSON & CSV) in a detached background thread.
    Throttled to avoid overwhelming the database during rapid operations.
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
    Starts a background daemon thread that executes full database backup every 24 hours.
    """
    def _daemon_loop():
        logger.info("[Auto-Backup Daemon] Background daily backup scheduler initialized.")
        # Initial delayed backup on startup (wait 30s for database connections to settle)
        time.sleep(30)
        trigger_auto_backup_async(force=True)

        INTERVAL = 24 * 60 * 60  # 24 Hours
        while True:
            try:
                time.sleep(INTERVAL)
                logger.info("[Auto-Backup Daemon] Scheduled 24-hour interval elapsed. Triggering backup...")
                trigger_auto_backup_async(force=True)
            except Exception as e:
                logger.error(f"[Auto-Backup Daemon] Error in scheduler loop: {e}")
                time.sleep(60)

    t = threading.Thread(target=_daemon_loop, daemon=True, name="DailyAutoBackupDaemon")
    t.start()

def setup_backup_signals():
    """
    Registers Django signals to automatically trigger backup when jobs/groups/categories are modified.
    """
    from .models import JobPosting, JobGroup, Category

    @receiver(post_save, sender=JobPosting)
    @receiver(post_delete, sender=JobPosting)
    @receiver(post_save, sender=JobGroup)
    @receiver(post_delete, sender=JobGroup)
    @receiver(post_save, sender=Category)
    @receiver(post_delete, sender=Category)
    def handle_db_change(sender, **kwargs):
        trigger_auto_backup_async(force=False)
