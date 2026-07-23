from django.apps import AppConfig


class FinalpackageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.finalpackage'
    verbose_name = 'Final Package'

    def ready(self):
        import apps.finalpackage.signals  # noqa
