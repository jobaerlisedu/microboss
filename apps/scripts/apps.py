from django.apps import AppConfig


class ScriptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scripts'
    verbose_name = 'স্ক্রিপ্ট'

    def ready(self):
        import apps.scripts.signals  # noqa
