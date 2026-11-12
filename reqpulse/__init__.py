from django.db.backends.signals import connection_created
from django.dispatch import receiver


@receiver(connection_created)
def configure_sqlite_pragmas(sender, connection, **kwargs):
    """
    SQLite pragmas for one web process running request threads plus
    background writers (scrapers, visit logging).

    Journal mode is DELETE, SQLite's default. WAL mode was tried and the
    production file was corrupted twice within a day each time, while DELETE
    mode had run for weeks without that. Lock waits are handled by
    busy_timeout plus IMMEDIATE transactions (settings._SQLITE_OPTIONS).
    """
    if connection.vendor != 'sqlite':
        return
    try:
        cursor = connection.cursor()
        cursor.execute('PRAGMA busy_timeout = 20000;')
        try:
            # Journal mode is stored in the file, so a file left in WAL mode
            # is switched back here; it can fail while another connection is busy.
            cursor.execute('PRAGMA journal_mode = DELETE;')
        except Exception:
            pass
        cursor.execute('PRAGMA synchronous = FULL;')
        cursor.execute('PRAGMA cache_size = -16000;')  # 16MB cache
        cursor.execute('PRAGMA temp_store = MEMORY;')
        cursor.execute('PRAGMA foreign_keys = ON;')
    except Exception as e:
        from requirements.db_recovery import is_database_corrupt_error, auto_repair_database
        if is_database_corrupt_error(e):
            auto_repair_database()
