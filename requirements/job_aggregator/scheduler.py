"""
Background Periodic Job Aggregation Scheduler.
Executes multi-source job ingestion at a configurable interval (default: 5 minutes)
without exceeding permitted request frequency or overloading resources on Render.
"""

import os
import time
import random
import threading
import logging
from django.utils import timezone
from .orchestrator import orchestrator

logger = logging.getLogger(__name__)

_SCHEDULER_RUNNING = False
_SCHEDULER_LOCK = threading.Lock()
_FLOCK_HANDLE = None


def _try_acquire_scheduler_lock() -> bool:
    """Acquires a non-blocking process lock to ensure single-worker execution."""
    global _FLOCK_HANDLE
    try:
        import fcntl
        lock_path = os.path.join('/tmp', 'kashii_job_aggregator.lock')
        _FLOCK_HANDLE = open(lock_path, 'a')
        fcntl.flock(_FLOCK_HANDLE, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except Exception:
        return False


def _background_aggregation_loop():
    """Periodic worker loop running India-wide ingestion."""
    global _SCHEDULER_RUNNING
    interval_minutes = int(os.getenv("JOB_AGGREGATION_INTERVAL_MINUTES", "5"))
    interval_seconds = interval_minutes * 60

    logger.info(f"⚡ [India Job Aggregator] Daemon started. Cycle interval: {interval_minutes} minutes.")

    # Graceful initial warm-up delay
    time.sleep(30)

    while _SCHEDULER_RUNNING:
        try:
            from django.db import close_old_connections, reset_queries
            reset_queries()
            close_old_connections()

            logger.info("⚡ [India Job Aggregator] Starting automated ingestion cycle...")
            result = orchestrator.run_aggregation(limit_per_source=8, last_hours=1)

            if result.get("total_imported", 0) > 0:
                logger.info(f"✅ [India Job Aggregator] Imported {result['total_imported']} fresh jobs! (Batch: {result.get('batch_id')})")
            else:
                logger.info(f"ℹ️ [India Job Aggregator] Ingestion cycle complete. 0 new jobs, {result.get('total_duplicates', 0)} active observed.")

        except Exception as e:
            logger.warning(f"Notice in Job Aggregator scheduler cycle: {e}")
        finally:
            try:
                from django.db import close_old_connections, reset_queries
                reset_queries()
                close_old_connections()
                import gc
                gc.collect()
            except Exception:
                pass

        time.sleep(interval_seconds + random.randint(5, 20))


def start_job_aggregation_daemon():
    """Starts the background aggregation daemon if not already running."""
    global _SCHEDULER_RUNNING
    with _SCHEDULER_LOCK:
        if not _SCHEDULER_RUNNING:
            if not _try_acquire_scheduler_lock():
                return False
            _SCHEDULER_RUNNING = True
            t = threading.Thread(target=_background_aggregation_loop, daemon=True, name="IndiaJobAggregatorWorker")
            t.start()
            return True
    return False
