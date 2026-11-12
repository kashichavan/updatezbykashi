from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def configure_sqlite_pragmas(sender, connection, **kwargs):
    """
    SQLite pragmas for one web process running request threads plus
    background writers (scrapers, visit logging).

    WAL: readers never wait for a writer. The previous DELETE journal mode made
    every page read block behind any write and then fail with "database is
    locked", which is what took the site down. WAL is safe on Render's local
    instance disk; backups use `dumpdata` and restores use `restore_snapshot`,
    so nothing copies the raw .sqlite3 file (which would miss the -wal file).
    synchronous=NORMAL is corruption-safe in WAL mode (a crash can only lose
    the last few commits, never corrupt the file).
    """
    if connection.vendor != 'sqlite':
        return
    try:
        cursor = connection.cursor()
        cursor.execute('PRAGMA busy_timeout = 20000;')
        try:
            cursor.execute('PRAGMA journal_mode = WAL;')
        except Exception:
            pass  # another connection holds a lock; WAL persists once any connection sets it
        cursor.execute('PRAGMA synchronous = NORMAL;')
        cursor.execute('PRAGMA wal_autocheckpoint = 100;')  # Checkpoint frequently to keep WAL small and safe
        cursor.execute('PRAGMA cache_size = -16000;')  # 16MB cache
        cursor.execute('PRAGMA temp_store = MEMORY;')
        cursor.execute('PRAGMA foreign_keys = ON;')
    except Exception as e:
        from requirements.db_recovery import is_database_corrupt_error, auto_repair_database
        if is_database_corrupt_error(e):
            auto_repair_database()
