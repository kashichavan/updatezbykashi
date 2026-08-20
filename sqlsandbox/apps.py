from django.apps import AppConfig

class SqlSandboxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sqlsandbox'
    verbose_name = 'SQL Execution Sandbox & Database Studio'
