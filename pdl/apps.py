from django.apps import AppConfig


class PdlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pdl'

    def ready(self):
        import pdl.signals  # noqa: F401
