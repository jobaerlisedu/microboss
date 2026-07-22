from django.apps import AppConfig


class AssignmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assignments'
    verbose_name = 'Assignment'

    def ready(self):
        import apps.assignments.signals  # noqa
