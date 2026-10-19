from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def configure_sqlite_pragmas(sender, connection, **kwargs):
    """
    Configure safe, robust SQLite pragmas.
    Uses safe journal mode, 30s busy timeout, and memory temp tables.
    Avoids WAL mode and excessive mmap which can corrupt ephemeral/container disks on restart.
    """
    if connection.vendor == 'sqlite':
        try:
            cursor = connection.cursor()
            cursor.execute('PRAGMA busy_timeout = 30000;')
            cursor.execute('PRAGMA synchronous = NORMAL;')
            cursor.execute('PRAGMA journal_mode = DELETE;')
            cursor.execute('PRAGMA cache_size = -16000;')  # 16MB cache
            cursor.execute('PRAGMA temp_store = MEMORY;')
            cursor.execute('PRAGMA foreign_keys = ON;')
        except Exception:
            pass

