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
    cursor = connection.cursor()
    # busy_timeout first, so the journal-mode switch can wait for a lock.
    cursor.execute('PRAGMA busy_timeout = 20000;')
    try:
        cursor.execute('PRAGMA journal_mode = WAL;')
    except Exception:
        pass  # another connection holds a lock; WAL persists once any connection sets it
    cursor.execute('PRAGMA synchronous = NORMAL;')
    cursor.execute('PRAGMA cache_size = -16000;')  # 16MB cache
    cursor.execute('PRAGMA temp_store = MEMORY;')
    cursor.execute('PRAGMA foreign_keys = ON;')
