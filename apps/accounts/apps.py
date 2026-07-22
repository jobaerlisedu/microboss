from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'অ্যাকাউন্ট'

    def ready(self):
        import apps.accounts.signals  # noqa
