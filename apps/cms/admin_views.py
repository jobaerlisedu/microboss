import csv, io, json
from functools import wraps
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from apps.accounts.models import User, UserSession
from apps.accounts.utils.config import get_config, set_config
from apps.content.models import ContentEntry
from apps.audit.models import AuditLog
from .views import _csv_response, _toast_response, _htmx_response, PLATFORMS


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponse('Unauthorized', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapper


@admin_required
def admin_audit_log(request):
    action = request.GET.get('action', '')
    content_type = request.GET.get('type', '')
    logs = AuditLog.objects.all().select_related('user')
    if action:
        logs = logs.filter(action=action)
    if content_type:
        logs = logs.filter(content_type=content_type)
    logs = logs[:200]
    content_types = AuditLog.objects.values_list('content_type', flat=True).distinct().order_by('content_type')

    processed_logs = []
    for log in logs:
        changes = log.changes or {}
        log.is_created = bool(changes.get('_created'))
        log.is_deleted = bool(changes.get('_deleted'))
        log.change_fields = {k: v for k, v in changes.items() if not k.startswith('_')}
        processed_logs.append(log)

    return render(request, 'cms/admin_audit_log.html', {
        'logs': processed_logs,
        'content_types': content_types,
        'selected_action': action,
        'selected_type': content_type,
        'user': request.user,
    })


@admin_required
def admin_system_health(request):
    from django.db import connection
    db_ok = True
    try:
        with connection.cursor() as c:
            c.execute('SELECT 1')
    except Exception:
        db_ok = False
    now = timezone.now()
    today = now.date()
    stats = {
        'total_users': User.objects.filter(is_active=True).count(),
        'pending_users': User.objects.filter(is_active=False, pending_approval=True).count(),
        'total_entries': ContentEntry.objects.filter(deleted_at__isnull=True).count(),
        'today_entries': ContentEntry.objects.filter(deleted_at__isnull=True, entry_date=today).count(),
        'audit_log_count': AuditLog.objects.count(),
        'recent_audit': AuditLog.objects.filter(created_at__gte=now - timezone.timedelta(hours=24)).count(),
    }
    return render(request, 'cms/admin_system_health.html', {
        'stats': stats,
        'db_ok': db_ok,
        'user': request.user,
    })


@admin_required
def admin_settings(request):
    if request.method == 'POST':
        reg_enabled = '1' if request.POST.get('registration_enabled') else '0'
        reg_message = request.POST.get('registration_message', '').strip()
        set_config('registration_enabled', reg_enabled, 'Registration system on/off')
        set_config('registration_message', reg_message, 'Message shown on registration form')
        return _toast_response('Settings saved successfully.', '/cms/admin-panel/settings/')
    reg_enabled = get_config('registration_enabled', '1')
    reg_message = get_config('registration_message', '')
    return render(request, 'cms/admin_settings.html', {
        'registration_enabled': reg_enabled,
        'registration_message': reg_message,
        'user': request.user,
    })


@admin_required
def admin_activity_timeline(request):
    user_id = request.GET.get('user_id', '')
    now = timezone.now()
    entries = []
    if user_id:
        target = get_object_or_404(User, id=user_id)
        for e in ContentEntry.objects.filter(member=target, deleted_at__isnull=True).order_by('-created_at')[:30]:
            entries.append({'time': e.created_at, 'text': f'Entry added: {e.headline}', 'type': 'entry'})
        for log in AuditLog.objects.filter(user=target).order_by('-created_at')[:30]:
            entries.append({'time': log.created_at, 'text': f'[{"created" if log.action=="created" else "updated" if log.action=="updated" else "deleted"}] {log.content_type}: {log.object_repr}', 'type': 'audit'})
        entries.sort(key=lambda x: x['time'], reverse=True)
        entries = entries[:50]
    users = User.objects.filter(is_active=True).order_by('full_name')
    return render(request, 'cms/admin_activity.html', {
        'entries': entries,
        'users': users,
        'selected_user_id': user_id,
        'user': request.user,
    })


@admin_required
def admin_bulk_delete(request):
    if request.method != 'POST':
        return HttpResponse('Unauthorized', status=403)
    model_name = request.POST.get('model', '')
    ids = request.POST.getlist('ids[]')
    if not ids:
        return _toast_response('No items selected.', '', 'error')
    now = timezone.now()
    count = 0
    if model_name == 'entry':
        count = ContentEntry.objects.filter(id__in=ids, deleted_at__isnull=True).update(deleted_at=now, updated_by=request.user)
    return _toast_response(f'{count} item(s) deleted successfully.')


@admin_required
def admin_csv_import(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            return _toast_response('No CSV file selected.', '', 'error')
        if not csv_file.name.endswith('.csv'):
            return _toast_response('Only CSV files are accepted.', '', 'error')
        if csv_file.size > 5 * 1024 * 1024:
            return _toast_response('File size exceeds 5MB limit.', '', 'error')
        decoded = csv_file.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        errors = []
        for i, row in enumerate(reader, start=1):
            try:
                headline = row.get('headline', '').strip()
                slug = row.get('slug', '').strip()
                if not headline or not slug:
                    errors.append(f'Row {i}: Headline and slug are required')
                    continue
                entry_date = row.get('entry_date', '').strip()
                entry_time = row.get('entry_time', '').strip()
                links = {}
                for key in ['fb', 'yt', 'ig', 'tt', 'linkedin', 'threads', 'bsky', 'dm', 'reddit']:
                    val = row.get(key, '').strip()
                    if val:
                        links[key] = val
                sponsor_name = row.get('sponsor', '').strip()
                sponsor_id = None
                if sponsor_name:
                    from apps.sponsors.models import Sponsor
                    sponsor = Sponsor.objects.filter(name__iexact=sponsor_name, deleted_at__isnull=True).first()
                    if sponsor:
                        sponsor_id = sponsor.id
                member_username = row.get('member', '').strip()
                member = request.user
                if member_username:
                    member_user = User.objects.filter(username=member_username, is_active=True).first()
                    if member_user:
                        member = member_user
                ContentEntry.objects.create(
                    entry_date=entry_date or timezone.now().date(),
                    entry_time=entry_time or timezone.now().time(),
                    headline=headline,
                    slug=slug,
                    member=member,
                    links=links,
                    sponsor_id=sponsor_id,
                    comment=row.get('comment', ''),
                    created_by=request.user,
                )
                created += 1
            except (IntegrityError, ValidationError, KeyError, ValueError) as e:
                errors.append(f'Row {i}: {str(e)}')
        msg = f'{created} entries imported successfully'
        if errors:
            msg += f'. {len(errors)} error(s): {"; ".join(errors[:5])}'
            if len(errors) > 5:
                msg += f'... and {len(errors) - 5} more'
        return _toast_response(msg, reverse('cms:cms-all-entries'))
    return render(request, 'cms/admin_csv_import.html', {'user': request.user})
