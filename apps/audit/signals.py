from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import IntegrityError, transaction
from .models import AuditLog
from infrastructure.middleware.request_context import get_current_request

AUDIT_MODELS = {
    'apps.content.ContentEntry',
    'apps.assignments.Assignment',
    'apps.scripts.Script',
    'apps.audio.AudioItem',
    'apps.contentlist.ContentListItem',
    'apps.finalpackage.FinalPackage',
    'apps.sponsors.Sponsor',
    'apps.notices.Notice',
}


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

        if action == 'deleted':
            changes = {'_deleted': True}
        else:
            try:
                old = instance.__class__.objects.get(pk=instance.pk) if not created else None
                changes = {'_created': True} if created else {}
                if not created and old:
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
            except Exception:
                changes = {'_note': 'compare error'}

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


def _should_audit(sender):
    key = f'{sender.__module__}.{sender.__qualname__}' if hasattr(sender, '__qualname__') else str(sender)
    return key in AUDIT_MODELS or key.replace('.models', '') in AUDIT_MODELS


@receiver(post_save)
def audit_post_save(sender, **kwargs):
    if not _should_audit(sender):
        return
    _safe_log(sender, kwargs['instance'], 'created' if kwargs.get('created') else 'updated', created=kwargs.get('created', False))


@receiver(post_delete)
def audit_post_delete(sender, **kwargs):
    if not _should_audit(sender):
        return
    _safe_log(sender, kwargs['instance'], 'deleted')
