from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def configure_sqlite_pragmas(sender, connection, **kwargs):
    """
    Optimize SQLite for ultra-high concurrency and fast writes/reads.
    Enables WAL mode, 10s busy timeout, and memory cache.
    """
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode = WAL;')
        cursor.execute('PRAGMA synchronous = NORMAL;')
        cursor.execute('PRAGMA busy_timeout = 10000;')
        cursor.execute('PRAGMA cache_size = -64000;')  # 64MB cache
        cursor.execute('PRAGMA temp_store = MEMORY;')   # Temp tables in RAM
        cursor.execute('PRAGMA mmap_size = 268435456;') # 256MB zero-copy memory mapping
        cursor.execute('PRAGMA foreign_keys = ON;')
