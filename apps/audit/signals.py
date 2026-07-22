from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import AuditLog
from infrastructure.middleware.request_context import get_current_request

AUDIT_MODELS = {}


def register_audit_models():
    from apps.content.models import ContentEntry
    from apps.assignments.models import Assignment
    from apps.scripts.models import Script
    from apps.audio.models import AudioItem
    from apps.contentlist.models import ContentListItem
    from apps.finalpackage.models import FinalPackage
    from apps.sponsors.models import Sponsor
    from apps.notices.models import Notice
    models = [ContentEntry, Assignment, Script, AudioItem, ContentListItem, FinalPackage, Sponsor, Notice]
    for model in models:
        key = f'{model.__module__}.{model.__qualname__}'
        AUDIT_MODELS[key] = model
    return models


def _safe_log(sender, instance, action, created=False):
    try:
        request = get_current_request()
        user = getattr(request, 'user', None) if request else None
        if not user or not user.is_authenticated:
            user = None
        if user and not user.pk:
            user = None

        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(instance)

        if action in ('deleted',):
            changes = {'_deleted': True}
        elif created:
            changes = {'_created': True}
        else:
            try:
                old = instance.__class__.objects.get(pk=instance.pk)
                changes = {}
                for field in instance._meta.concrete_fields:
                    fn = field.name
                    if fn in ('updated_at', 'updated_by', 'last_login'):
                        continue
                    ov = getattr(old, fn)
                    nv = getattr(instance, fn)
                    if ov != nv:
                        changes[fn] = {'old': str(ov), 'new': str(nv)}
            except instance.__class__.DoesNotExist:
                changes = {'_note': 'compare failed'}

        if not changes:
            return

        with transaction.atomic():
            AuditLog.objects.create(
                user=user,
                username=user.username if user else 'system',
                action=action,
                content_type=f'{ct.app_label}.{ct.model}',
                object_id=str(instance.pk),
                object_repr=str(instance)[:255],
                changes=changes,
                ip_address=getattr(request, 'META', {}).get('REMOTE_ADDR', None) if request else None,
                user_agent=getattr(request, 'META', {}).get('HTTP_USER_AGENT', '')[:500] if request else '',
            )
    except Exception:
        pass


def _bind_audit_signals():
    from django.db.models import Model
    for model in register_audit_models():
        if not issubclass(model, Model):
            continue
        pre_save.connect(_audit_pre_save, sender=model, dispatch_uid=f'audit_pre_save_{model.__name__}')
        post_delete.connect(_audit_post_delete, sender=model, dispatch_uid=f'audit_post_delete_{model.__name__}')


def _audit_pre_save(sender, **kwargs):
    instance = kwargs['instance']
    created = instance.pk is None
    _safe_log(sender, instance, 'created' if created else 'updated', created=created)


def _audit_post_delete(sender, **kwargs):
    _safe_log(sender, kwargs['instance'], 'deleted')


_bind_audit_signals()
