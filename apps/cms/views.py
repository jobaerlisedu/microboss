import csv
import io
import json
from datetime import date, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count, Q
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from apps.accounts.models import User, UserSession
from apps.content.models import ContentEntry
from apps.sponsors.models import Sponsor
from apps.contentlist.models import ContentListItem
from apps.assignments.models import Assignment
from apps.scripts.models import Script, ScriptEditHistory
from apps.notices.models import Notice
from apps.analytics.services import get_dashboard_data
from apps.audio.models import AudioItem
from apps.finalpackage.models import FinalPackage
from apps.reports.models import ReportConfig
from apps.reports.report_engine import ReportEngine

PLATFORMS = [
    {'key': 'fb', 'label': 'Facebook', 'color': '#3B82F6'},
    {'key': 'yt', 'label': 'YouTube', 'color': '#EF4444'},
    {'key': 'ig', 'label': 'Instagram', 'color': 'linear-gradient(135deg,#F58529,#DD2A7B,#8134AF)'},
    {'key': 'threads', 'label': 'Threads', 'color': '#111827'},
    {'key': 'tt', 'label': 'TikTok', 'color': '#000000'},
    {'key': 'linkedin', 'label': 'LinkedIn', 'color': '#0A66C2'},
    {'key': 'bsky', 'label': 'Bluesky', 'color': '#1185FE'},
    {'key': 'dm', 'label': 'Dailymotion', 'color': '#00A0DE'},
    {'key': 'reddit', 'label': 'Reddit', 'color': '#FF4500'},
]


def _is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


def _tab_response(request, template, ctx):
    return _htmx_response(request, template, ctx)


def _is_owner_or_admin(user, obj):
    if user.is_admin or user.is_superuser:
        return True
    for fk in ('member_id', 'writer_id', 'user_id'):
        if hasattr(obj, fk) and str(getattr(obj, fk)) == str(user.id):
            return True
    return False


def _today_str():
    return timezone.now().strftime('%Y-%m-%d')


def _csv_response(filename, header, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return response


def _toast_response(msg, redirect_url, type='success'):
    resp = HttpResponse()
    resp['HX-Trigger'] = json.dumps({
        'cms-toast': {'message': msg, 'type': type}
    })
    if redirect_url:
        resp['HX-Location'] = json.dumps({
            "path": redirect_url,
            "target": "#tab-content"
        })
    return resp


def _htmx_response(request, template, ctx=None, msg=None, msg_type='success', redirect_url=None):
    ctx = ctx or {}
    ctx['user'] = request.user
    if _is_htmx(request):
        resp = render(request, template, ctx)
        if msg:
            resp['HX-Trigger'] = json.dumps({
                'cms-toast': {'message': msg, 'type': msg_type}
            })
        if redirect_url:
            resp['HX-Redirect'] = redirect_url
        return resp
    tab_html = render(request, template, ctx).content.decode('utf-8')
    ctx['tab_content_rendered'] = tab_html
    resp = render(request, 'cms/dashboard.html', ctx)
    if msg:
        resp['HX-Trigger'] = json.dumps({
            'cms-toast': {'message': msg, 'type': msg_type}
        })
    if redirect_url:
        resp['HX-Redirect'] = redirect_url
    return resp


def _bengali_month(m):
    months = ['January', 'February', 'March', 'April', 'May', 'June',
              'July', 'August', 'September', 'October', 'November', 'December']
    return months[int(m) - 1]


def cms_register(request):
    from apps.accounts.utils.config import get_config
    if request.user.is_authenticated:
        return redirect('cms:cms-dashboard')
    reg_enabled = get_config('registration_enabled', '1')
    if reg_enabled != '1':
        reg_message = get_config('registration_message', 'Registration is currently closed.')
        return render(request, 'registration/cms_login.html', {
            'register_error': reg_message,
        })
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        full_name = request.POST.get('full_name', '').strip()
        office_id = request.POST.get('office_id', '').strip()
        designation = request.POST.get('designation', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        blood_group = request.POST.get('blood_group', 'B+')

        if not all([username, password, full_name, office_id, designation, email, phone]):
            return render(request, 'registration/cms_login.html', {
                'register_error': 'Please fill in all required fields.',
            })
        if len(password) < 4:
            return render(request, 'registration/cms_login.html', {
                'register_error': 'Password must be at least 4 characters.',
            })
        if User.objects.filter(username=username).exists():
            return render(request, 'registration/cms_login.html', {
                'register_error': 'This username is already taken.',
            })
        if User.objects.filter(office_id=office_id).exists():
            return render(request, 'registration/cms_login.html', {
                'register_error': 'This Office ID is already registered.',
            })
        if User.objects.filter(email=email).exists():
            return render(request, 'registration/cms_login.html', {
                'register_error': 'This email address is already registered.',
            })

        User.objects.create_user(
            username=username, password=password,
            full_name=full_name, office_id=office_id,
            designation=designation, email=email,
            phone=phone, blood_group=blood_group,
            is_active=False, pending_approval=True,
        )
        return render(request, 'registration/cms_login.html', {
            'registered': True,
        })
    return render(request, 'registration/cms_login.html')


def cms_login(request):
    if request.user.is_authenticated:
        return redirect('cms:cms-dashboard')
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '')
        password = request.POST.get('password', '')
        user = None
        for field in ['username', 'email', 'office_id']:
            try:
                u = User.objects.get(**{field: identifier})
                if u.check_password(password):
                    user = u
                    break
            except User.DoesNotExist:
                continue
        if user and user.is_active:
            auth_login(request, user)
            next_url = request.POST.get('next', '')
            if next_url and next_url.startswith('/') and '//' not in next_url.lstrip('/'):
                return redirect(next_url)
            return redirect('cms:cms-dashboard')
        return render(request, 'registration/cms_login.html', {
            'form': type('obj', (object,), {'errors': True})(),
        })
    return render(request, 'registration/cms_login.html')


def _dashboard_context(period='month'):
    today = timezone.now()
    analytics = get_dashboard_data(period=period)
    entries = ContentEntry.objects.filter(deleted_at__isnull=True)
    today_entries = entries.filter(entry_date=today.date())
    from apps.analytics.services import AnalyticsService
    svc = AnalyticsService()
    kpi = analytics['kpi']
    kpi['active_sessions'] = svc.session_metrics()['active_sessions']

    return {
        'today': _today_str(),
        'analytics': analytics,
        'stats': kpi,
        'platforms': PLATFORMS,
        'recent_entries': entries.select_related('member').order_by('-created_at')[:6],
        'today_entries': today_entries.select_related('member').order_by('-created_at')[:5],
        'notices': Notice.objects.filter(deleted_at__isnull=True).select_related('created_by').order_by('-created_at')[:5],
    }


@login_required
def cms_dashboard(request):
    period = request.GET.get('period', 'month')
    ctx = _dashboard_context(period=period)
    ctx['user'] = request.user
    ctx['title'] = 'Content Dashboard'
    return render(request, 'cms/dashboard.html', ctx)


@login_required
def dashboard_tab(request):
    period = request.GET.get('period', 'month')
    ctx = _dashboard_context(period=period)
    return _tab_response(request, 'cms/dashboard_tab.html', ctx)


@login_required
def new_entry_tab(request):
    sponsors = Sponsor.objects.filter(deleted_at__isnull=True)
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    initial = {
        'date': _today_str(),
        'time': timezone.now().strftime('%H:%M'),
    }
    return _tab_response(request, 'cms/new_entry.html', {
        'platforms': PLATFORMS,
        'sponsors': sponsors,
        'today_assignments': today_assignments,
        'initial': initial,
        'user': request.user,
    })


@login_required
def all_entries_tab(request):
    today = _today_str()
    qs = ContentEntry.objects.filter(deleted_at__isnull=True).select_related('member', 'sponsor')
    sponsors = Sponsor.objects.filter(deleted_at__isnull=True)
    users = User.objects.filter(is_active=True)

    search = request.GET.get('search', '')
    sponsor_id = request.GET.get('sponsor', '')
    member_id = request.GET.get('member', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if not date_from and not date_to:
        qs = qs.filter(entry_date=today)

    if search:
        qs = qs.filter(
            Q(headline__icontains=search) | Q(slug__icontains=search) |
            Q(member__username__icontains=search) | Q(comment__icontains=search)
        )
    if sponsor_id:
        qs = qs.filter(sponsor_id=sponsor_id)
    if member_id:
        qs = qs.filter(member_id=member_id)
    if date_from:
        qs = qs.filter(entry_date__gte=date_from)
    if date_to:
        qs = qs.filter(entry_date__lte=date_to)

    if request.GET.get('export') == 'csv':
        rows = []
        for e in qs.order_by('-entry_date', '-entry_time'):
            links_str = ' | '.join(
                f'{p["label"]}: {e.links.get(p["key"], "")}'
                for p in PLATFORMS if e.links.get(p["key"])
            )
            rows.append([
                e.entry_date.strftime('%Y-%m-%d'),
                e.entry_time.strftime('%H:%M') if e.entry_time else '',
                e.member.username,
                e.headline,
                e.slug,
                e.sponsor.name if e.sponsor else '',
                links_str,
                e.comment or '',
            ])
        return _csv_response(
            'content-entries.csv',
            ['Date', 'Time', 'Member', 'Headline', 'Slug', 'Sponsor', 'Links', 'Comment'],
            rows,
        )

    now = timezone.now()
    stats = {
        'total': qs.count(),
        'this_month': qs.filter(entry_date__year=now.year, entry_date__month=now.month).count(),
        'sponsored': qs.filter(sponsor__isnull=False).count(),
        'sponsor_count': sponsors.count(),
    }

    months_dict = {}
    for e in qs.order_by('-entry_date', '-entry_time'):
        key = e.entry_date.strftime('%Y-%m')
        if key not in months_dict:
            months_dict[key] = []
        months_dict[key].append(e)

    months = []
    for key in sorted(months_dict.keys(), reverse=True):
        year_str, month_str = key.split('-')
        label = _bengali_month(month_str) + ' ' + year_str
        months.append({
            'key': key,
            'label': label,
            'entries': months_dict[key],
            'is_open': key == now.strftime('%Y-%m'),
        })

    return _tab_response(request, 'cms/all_entries.html', {
        'months': months,
        'stats': stats,
        'sponsors': sponsors,
        'users': users,
        'platforms': PLATFORMS,
        'search': search,
        'selected_sponsor': sponsor_id,
        'selected_member': member_id,
        'date_from': date_from,
        'date_to': date_to,
        'user': request.user,
    })


@login_required
def sponsors_tab(request):
    sponsors = Sponsor.objects.filter(deleted_at__isnull=True).order_by('-created_at')
    stats = _sponsor_stats()
    return _tab_response(request, 'cms/sponsors.html', {
        'sponsors': sponsors,
        'stats': stats,
        'user': request.user,
    })


@login_required
def content_list_tab(request):
    today = _today_str()
    qs = ContentListItem.objects.filter(deleted_at__isnull=True, list_date=today).select_related('member', 'assignment')
    now = timezone.now()
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')

    stats = {
        'total': qs.count(),
        'today': qs.filter(list_date=today).count(),
        'this_month': qs.filter(list_date__year=now.year, list_date__month=now.month).count(),
        'district': qs.filter(source='district').count(),
    }

    return _tab_response(request, 'cms/content_list.html', {
        'items': qs.order_by('-list_date', '-created_at'),
        'today_assignments': today_assignments,
        'stats': stats,
        'today': today,
        'user': request.user,
    })


@login_required
def assignments_tab(request):
    today = _today_str()
    qs = Assignment.objects.filter(deleted_at__isnull=True, assign_date=today).select_related('member', 'reporter_user')
    stats_qs = Assignment.objects.filter(deleted_at__isnull=True)
    now = timezone.now()
    active_users = User.objects.filter(is_active=True).order_by('full_name')

    if request.GET.get('export') == 'csv':
        csv_qs = Assignment.objects.filter(deleted_at__isnull=True).select_related('member', 'reporter_user')
        rows = []
        for a in csv_qs.order_by('-assign_date', '-created_at'):
            rows.append([
                a.assign_date.strftime('%Y-%m-%d'),
                a.caption,
                a.district or '',
                a.reporter,
                a.get_status_display(),
                a.source_link or '',
            ])
        return _csv_response(
            'assignments.csv',
            ['তারিখ', 'ক্যাপশন', 'জেলা', 'রিপোর্টার', 'স্ট্যাটাস', 'সোর্স লিংক'],
            rows,
        )

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    page_size = 20
    offset = (page - 1) * page_size
    assignments_list = list(qs.order_by('-assign_date', '-created_at')[offset:offset + page_size + 1])
    has_more = len(assignments_list) > page_size
    if has_more:
        assignments_list = assignments_list[:page_size]

    ctx = {
        'assignments': assignments_list,
        'today': today,
        'user': request.user,
        'active_users': active_users,
        'page': page,
        'has_more': has_more,
        'start_index': offset + 1,
    }

    if page == 1:
        stats = {
            'total': stats_qs.count(),
            'today': stats_qs.filter(assign_date=today).count(),
            'this_month': stats_qs.filter(assign_date__year=now.year, assign_date__month=now.month).count(),
            'done': stats_qs.filter(status='Done').count(),
        }
        ctx['stats'] = stats

    return _tab_response(request, 'cms/assignments.html', ctx)


@login_required
def scripts_tab(request):
    now = timezone.now()
    qs = Script.objects.filter(deleted_at__isnull=True, script_date=now.date()).select_related('writer', 'approved_by', 'assignment')
    my_qs = qs.filter(writer=request.user)
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')

    if request.GET.get('export') == 'csv':
        rows = []
        for sc in qs.order_by('-script_date', '-created_at'):
            rows.append([
                sc.script_date.strftime('%Y-%m-%d'),
                sc.writer.username,
                sc.headline or '',
                sc.get_source_display(),
                sc.district or '',
                sc.get_status_display(),
            ])
        return _csv_response(
            'scripts.csv',
            ['তারিখ', 'লেখক', 'হেডলাইন', 'উৎস', 'জেলা', 'স্ট্যাটাস'],
            rows,
        )

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    page_size = 20
    offset = (page - 1) * page_size
    scripts_list = list(qs.order_by('-script_date', '-created_at')[offset:offset + page_size + 1])
    has_more = len(scripts_list) > page_size
    if has_more:
        scripts_list = scripts_list[:page_size]

    ctx = {
        'scripts': scripts_list,
        'today_assignments': today_assignments,
        'user': request.user,
        'page': page,
        'has_more': has_more,
    }

    if page == 1:
        stats = {
            'total': qs.count(),
            'my_total': my_qs.count(),
            'my_today': my_qs.filter(script_date=now.date()).count(),
            'my_month': my_qs.filter(script_date__year=now.year, script_date__month=now.month).count(),
            'pending': qs.filter(status='pending').count(),
        }
        ctx['stats'] = stats

    return _tab_response(request, 'cms/scripts.html', ctx)


@login_required
def leaderboard_tab(request):
    top_users = User.objects.filter(
        is_active=True,
    ).annotate(
        entry_count=Count('content_entries', filter=Q(content_entries__deleted_at__isnull=True)),
    ).order_by('-entry_count')[:5]

    is_winner = bool(top_users and str(top_users[0].id) == str(request.user.id) and top_users[0].entry_count > 0)

    return _tab_response(request, 'cms/leaderboard.html', {
        'top_users': top_users,
        'user': request.user,
        'is_winner': is_winner,
    })


def _admin_response(request, msg=None, msg_type='success'):
    users = User.objects.filter(is_active=True).order_by('username')
    pending_users = User.objects.filter(is_active=False, pending_approval=True).order_by('date_joined')
    sessions = UserSession.objects.all().order_by('-login_at')[:50]
    return _htmx_response(request, 'cms/admin_panel.html', {
        'users': users,
        'pending_users': pending_users,
        'sessions': sessions,
    }, msg, msg_type)


@login_required
def admin_panel_tab(request):
    if not request.user.is_admin:
        return HttpResponse('Unauthorized', status=403)
    return _admin_response(request)


@login_required
def leaderboard_widget(request):
    top_users = User.objects.filter(
        is_active=True,
    ).annotate(
        entry_count=Count('content_entries', filter=Q(content_entries__deleted_at__isnull=True)),
    ).order_by('-entry_count')[:5]

    is_winner = bool(top_users and str(top_users[0].id) == str(request.user.id) and top_users[0].entry_count > 0)

    return render(request, 'cms/leaderboard_widget.html', {
        'top_users': top_users,
        'is_winner': is_winner,
    })


@login_required
def sponsor_track_widget(request):
    today = timezone.now().date()
    active = Sponsor.objects.filter(
        deleted_at__isnull=True,
        start_date__lte=today,
        end_date__gte=today,
    )
    return render(request, 'cms/sponsor_track_widget.html', {
        'active_sponsors': active,
        'today': today,
    })


@login_required
def contributors_widget(request):
    top = User.objects.filter(is_active=True).annotate(
        entry_count=Count('content_entries', filter=Q(content_entries__deleted_at__isnull=True)),
        assignment_count=Count('assignments', filter=Q(assignments__deleted_at__isnull=True)),
        script_count=Count('scripts', filter=Q(scripts__deleted_at__isnull=True)),
        audio_count=Count('audio_items', filter=Q(audio_items__deleted_at__isnull=True)),
        clist_count=Count('content_list_items', filter=Q(content_list_items__deleted_at__isnull=True)),
        fp_count=Count('final_packages', filter=Q(final_packages__deleted_at__isnull=True)),
    ).order_by('-entry_count')[:15]
    for u in top:
        u.total_count = u.entry_count + u.assignment_count + u.script_count + u.audio_count + u.clist_count + u.fp_count
    top = sorted(top, key=lambda u: u.total_count, reverse=True)[:5]
    return render(request, 'cms/contributors_widget.html', {
        'top': top,
    })


@login_required
def save_entry(request):
    if request.method == 'POST':
        links = {}
        for key in ['fb', 'yt', 'ig', 'threads', 'tt', 'linkedin', 'bsky', 'dm', 'reddit']:
            val = request.POST.get(f'links_{key}', '').strip()
            if val:
                links[key] = val
        if not links:
            return _toast_response('Please provide at least 1 social platform URL.', '', 'error')

        sponsor_id = request.POST.get('sponsor_id', '')
        if sponsor_id and not Sponsor.objects.filter(id=sponsor_id, deleted_at__isnull=True).exists():
            sponsor_id = None

        assignment_id = request.POST.get('assignment_id', '')
        if assignment_id and not Assignment.objects.filter(id=assignment_id, deleted_at__isnull=True).exists():
            assignment_id = None

        entry_id = request.POST.get('entry_id', '')
        data = {
            'entry_date': request.POST.get('entry_date'),
            'entry_time': request.POST.get('entry_time'),
            'slug': request.POST.get('slug', ''),
            'headline': request.POST.get('headline', ''),
            'links': links,
            'assignment_id': assignment_id or None,
            'sponsor_id': sponsor_id or None,
            'comment': request.POST.get('comment', ''),
        }
        if entry_id:
            entry = get_object_or_404(ContentEntry, id=entry_id, deleted_at__isnull=True)
            for k, v in data.items():
                setattr(entry, k, v)
            entry.updated_by = request.user
            entry.save()
            return _toast_response('Entry updated successfully.', '/cms/entries/')
        data['member'] = request.user
        data['created_by'] = request.user
        entry = ContentEntry.objects.create(**data)
        # Close the linked assignment as Done / Published
        if assignment_id:
            assignment = get_object_or_404(Assignment, id=assignment_id)
            assignment.status = 'Done'
            assignment.updated_by = request.user
            assignment.save()
        return _toast_response('Entry saved successfully.', '/cms/entries/')
    return redirect('cms:cms-new-entry')


@login_required
def edit_entry(request, pk):
    entry = get_object_or_404(ContentEntry, id=pk, deleted_at__isnull=True)
    sponsors = Sponsor.objects.filter(deleted_at__isnull=True)
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    links = entry.links or {}
    return render(request, 'cms/new_entry.html', {
        'platforms': PLATFORMS,
        'sponsors': sponsors,
        'today_assignments': today_assignments,
        'entry': entry,
        'links': links,
        'user': request.user,
        'editing': True,
    })


@login_required
def duplicate_entry(request, pk):
    original = get_object_or_404(ContentEntry, id=pk, deleted_at__isnull=True)
    sponsors = Sponsor.objects.filter(deleted_at__isnull=True)
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    initial = {
        'entry_date': timezone.now().strftime('%Y-%m-%d'),
        'entry_time': timezone.now().strftime('%H:%M'),
        'slug': original.slug,
        'headline': original.headline,
        'links': original.links or {},
        'comment': original.comment,
        'sponsor_id': str(original.sponsor_id or ''),
        'assignment_id': str(original.assignment_id or ''),
    }
    return render(request, 'cms/new_entry.html', {
        'platforms': PLATFORMS,
        'sponsors': sponsors,
        'today_assignments': today_assignments,
        'initial': initial,
        'links': original.links or {},
        'user': request.user,
        'duplicating': True,
    })


@login_required
@require_POST
def delete_entry(request, pk):
    entry = get_object_or_404(ContentEntry, id=pk, deleted_at__isnull=True)
    entry.deleted_at = timezone.now()
    entry.updated_by = request.user
    entry.save()
    return _toast_response('Entry deleted successfully.', '/cms/entries/')


@login_required
def save_sponsor(request):
    if request.method == 'POST':
        sponsor_id = request.POST.get('sponsor_id', '')
        data = {
            'name': request.POST.get('name'),
            'daily_quota': request.POST.get('daily_quota'),
            'total_quota': request.POST.get('total_quota'),
            'start_date': request.POST.get('start_date'),
            'end_date': request.POST.get('end_date'),
            'content_type': request.POST.get('content_type', ''),
            'has_doggy': request.POST.get('has_doggy') == 'on',
            'has_popup': request.POST.get('has_popup') == 'on',
            'has_tvc': request.POST.get('has_tvc') == 'on',
            'has_gpi': request.POST.get('has_gpi') == 'on',
        }
        if sponsor_id:
            sponsor = get_object_or_404(Sponsor, id=sponsor_id, deleted_at__isnull=True)
            for k, v in data.items():
                setattr(sponsor, k, v)
            sponsor.updated_by = request.user
            sponsor.save()
            return _toast_response('Sponsor updated successfully.', '/cms/sponsors/')
        data['created_by'] = request.user
        Sponsor.objects.create(**data)
        return _toast_response('Sponsor saved successfully.', '/cms/sponsors/')
    return redirect('cms:cms-sponsors')


@login_required
def edit_sponsor(request, pk):
    sponsor = get_object_or_404(Sponsor, id=pk, deleted_at__isnull=True)
    today = _today_str()
    return render(request, 'cms/sponsors.html', {
        'sponsors': Sponsor.objects.filter(deleted_at__isnull=True).order_by('name'),
        'edit_sponsor': sponsor,
        'today': today,
        'user': request.user,
    })


@login_required
@require_POST
def delete_sponsor(request, pk):
    sponsor = get_object_or_404(Sponsor, id=pk, deleted_at__isnull=True)
    sponsor.deleted_at = timezone.now()
    sponsor.updated_by = request.user
    sponsor.save()
    return _toast_response('Sponsor deleted successfully.', '/cms/sponsors/')


@login_required
def save_content_list(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id', '')
        assignment_id = request.POST.get('assignment_id', '')
        if assignment_id and not Assignment.objects.filter(id=assignment_id, deleted_at__isnull=True).exists():
            assignment_id = None
        data = {
            'list_date': request.POST.get('list_date'),
            'content': request.POST.get('content'),
            'source': request.POST.get('source'),
            'district': request.POST.get('district', ''),
            'footage_source': request.POST.get('footage_source'),
            'assignment_id': assignment_id or None,
            'member': request.user,
        }
        if item_id:
            item = get_object_or_404(ContentListItem, id=item_id, deleted_at__isnull=True)
            for k, v in data.items():
                setattr(item, k, v)
            item.updated_by = request.user
            item.save()
            return _toast_response('Content list item updated.', '/cms/content-lists/')
        data['created_by'] = request.user
        ContentListItem.objects.create(**data)
        return _toast_response('Content list item saved.', '/cms/content-lists/')
    return redirect('cms:cms-content-list')


@login_required
def edit_content_list(request, pk):
    item = get_object_or_404(ContentListItem, id=pk, deleted_at__isnull=True)
    today = _today_str()
    qs = ContentListItem.objects.filter(deleted_at__isnull=True).select_related('member', 'assignment')
    now = timezone.now()
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    stats = {
        'total': qs.count(),
        'today': qs.filter(list_date=today).count(),
        'this_month': qs.filter(list_date__year=now.year, list_date__month=now.month).count(),
        'district': qs.filter(source='district').count(),
    }
    return render(request, 'cms/content_list.html', {
        'items': qs.order_by('-list_date', '-created_at'),
        'today_assignments': today_assignments,
        'edit_item': item,
        'stats': stats,
        'today': today,
        'user': request.user,
    })


@login_required
@require_POST
def delete_content_list(request, pk):
    item = get_object_or_404(ContentListItem, id=pk, deleted_at__isnull=True)
    item.deleted_at = timezone.now()
    item.updated_by = request.user
    item.save()
    return _toast_response('Content list item deleted.', '/cms/content-lists/')


# ─── Audio Tab ────────────────────────────────────────────


@login_required
def audio_tab(request):
    today = _today_str()
    qs = AudioItem.objects.filter(deleted_at__isnull=True, audio_date=today).select_related('member', 'assignment')
    now = timezone.now()
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    stats = {
        'total': qs.count(),
        'today': qs.filter(audio_date=today).count(),
        'this_month': qs.filter(audio_date__year=now.year, audio_date__month=now.month).count(),
    }
    return _tab_response(request, 'cms/audio_list.html', {
        'items': qs.order_by('-audio_date', '-created_at'),
        'today_assignments': today_assignments,
        'stats': stats,
        'today': today,
        'user': request.user,
    })


@login_required
def save_audio(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id', '')
        assignment_id = request.POST.get('assignment_id', '')
        if assignment_id and not Assignment.objects.filter(id=assignment_id, deleted_at__isnull=True).exists():
            assignment_id = None
        data = {
            'audio_date': request.POST.get('audio_date'),
            'title': request.POST.get('title', ''),
            'source': request.POST.get('source', 'social'),
            'district': request.POST.get('district', ''),
            'duration': request.POST.get('duration', ''),
            'file_link': request.POST.get('file_link', ''),
            'voice_over': request.POST.get('voice_over', ''),
            'assignment_id': assignment_id or None,
            'member': request.user,
        }
        if item_id:
            item = get_object_or_404(AudioItem, id=item_id, deleted_at__isnull=True)
            for k, v in data.items():
                setattr(item, k, v)
            item.updated_by = request.user
            item.save()
            return _toast_response('Audio updated.', '/cms/audio/')
        data['created_by'] = request.user
        AudioItem.objects.create(**data)
        return _toast_response('Audio saved.', '/cms/audio/')
    return redirect('cms:cms-audio')


@login_required
def edit_audio(request, pk):
    item = get_object_or_404(AudioItem, id=pk, deleted_at__isnull=True)
    today = _today_str()
    qs = AudioItem.objects.filter(deleted_at__isnull=True).select_related('member', 'assignment')
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    return render(request, 'cms/audio_list.html', {
        'items': qs.order_by('-audio_date', '-created_at'),
        'today_assignments': today_assignments,
        'edit_item': item,
        'today': today,
        'user': request.user,
    })


@login_required
@require_POST
def delete_audio(request, pk):
    item = get_object_or_404(AudioItem, id=pk, deleted_at__isnull=True)
    item.deleted_at = timezone.now()
    item.updated_by = request.user
    item.save()
    return _toast_response('Audio deleted.', '/cms/audio/')


# ─── Final Package Tab ────────────────────────────────────


@login_required
def final_package_tab(request):
    today = _today_str()
    qs = FinalPackage.objects.filter(deleted_at__isnull=True, package_date=today).select_related('member', 'assignment')
    now = timezone.now()
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    stats = {
        'total': qs.count(),
        'today': qs.filter(package_date=today).count(),
        'this_month': qs.filter(package_date__year=now.year, package_date__month=now.month).count(),
        'draft': qs.filter(status='draft').count(),
        'approved': qs.filter(status='approved').count(),
    }
    return _tab_response(request, 'cms/final_package_list.html', {
        'items': qs.order_by('-package_date', '-created_at'),
        'today_assignments': today_assignments,
        'stats': stats,
        'today': today,
        'user': request.user,
    })


@login_required
def save_final_package(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id', '')
        assignment_id = request.POST.get('assignment_id', '')
        if assignment_id and not Assignment.objects.filter(id=assignment_id, deleted_at__isnull=True).exists():
            assignment_id = None
        data = {
            'package_date': request.POST.get('package_date'),
            'title': request.POST.get('title', ''),
            'producer': request.POST.get('producer', ''),
            'editor': request.POST.get('editor', ''),
            'runtime': request.POST.get('runtime', ''),
            'file_link': request.POST.get('file_link', ''),
            'notes': request.POST.get('notes', ''),
            'status': request.POST.get('status', 'draft'),
            'assignment_id': assignment_id or None,
            'member': request.user,
        }
        if item_id:
            item = get_object_or_404(FinalPackage, id=item_id, deleted_at__isnull=True)
            for k, v in data.items():
                setattr(item, k, v)
            item.updated_by = request.user
            item.save()
            return _toast_response('Final package updated.', '/cms/final-packages/')
        data['created_by'] = request.user
        FinalPackage.objects.create(**data)
        return _toast_response('Final package saved.', '/cms/final-packages/')
    return redirect('cms:cms-final-packages')


@login_required
def edit_final_package(request, pk):
    item = get_object_or_404(FinalPackage, id=pk, deleted_at__isnull=True)
    today = _today_str()
    qs = FinalPackage.objects.filter(deleted_at__isnull=True).select_related('member', 'assignment')
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    return render(request, 'cms/final_package_list.html', {
        'items': qs.order_by('-package_date', '-created_at'),
        'today_assignments': today_assignments,
        'edit_item': item,
        'today': today,
        'user': request.user,
    })


@login_required
@require_POST
def delete_final_package(request, pk):
    item = get_object_or_404(FinalPackage, id=pk, deleted_at__isnull=True)
    item.deleted_at = timezone.now()
    item.updated_by = request.user
    item.save()
    return _toast_response('Final package deleted.', '/cms/final-packages/')


def _set_assignment_reporter(assignment, reporter_user_id, reporter_name):
    if reporter_user_id:
        try:
            ru = User.objects.get(id=reporter_user_id, is_active=True)
            assignment.reporter_user = ru
            assignment.reporter = reporter_name or ru.full_name or ru.username
            return
        except User.DoesNotExist:
            pass
    assignment.reporter_user = None
    assignment.reporter = reporter_name or ''


@login_required
def save_assignment(request):
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id', '')
        reporter_user_id = request.POST.get('reporter_user', '')
        reporter_name = request.POST.get('reporter', '').strip()

        assign_date = request.POST.get('assign_date')
        caption = request.POST.get('caption')
        source_link = request.POST.get('source_link', '')
        district = request.POST.get('district', '')

        try:
            parsed_date = datetime.strptime(assign_date, '%Y-%m-%d').date() if assign_date else None
            if parsed_date and parsed_date > timezone.now().date():
                return _toast_response('Assign date cannot be in the future.', '', 'error')
        except (ValueError, TypeError):
            return _toast_response('Invalid date format.', '', 'error')

        if assignment_id:
            assignment = get_object_or_404(Assignment, id=assignment_id, deleted_at__isnull=True)
            if not _is_owner_or_admin(request.user, assignment):
                return _toast_response('You do not have permission to edit this assignment.', '', 'error')
            assignment.assign_date = assign_date
            assignment.caption = caption
            assignment.source_link = source_link
            assignment.district = district
            _set_assignment_reporter(assignment, reporter_user_id, reporter_name)
            assignment.updated_by = request.user
            assignment.save()
            return _toast_response('Assignment updated successfully.', reverse('cms:cms-assignments'))
        data = {
            'assign_date': assign_date,
            'caption': caption,
            'source_link': source_link,
            'district': district,
            'member': request.user,
            'created_by': request.user,
        }
        if reporter_user_id:
            try:
                ru = User.objects.get(id=reporter_user_id, is_active=True)
                data['reporter_user'] = ru
                data['reporter'] = reporter_name or ru.full_name or ru.username
            except User.DoesNotExist:
                data['reporter'] = reporter_name or ''
        else:
            data['reporter'] = reporter_name or ''
        Assignment.objects.create(**data)
        return _toast_response('Assignment saved successfully.', reverse('cms:cms-assignments'))
    return redirect(reverse('cms:cms-assignments'))


@login_required
def edit_assignment(request, pk):
    assignment = get_object_or_404(Assignment, id=pk, deleted_at__isnull=True)
    if not _is_owner_or_admin(request.user, assignment):
        return _toast_response('You do not have permission to edit this assignment.', '', 'error')
    today = _today_str()
    now = timezone.now()
    qs = Assignment.objects.filter(deleted_at__isnull=True, assign_date=today).select_related('member', 'reporter_user')
    active_users = User.objects.filter(is_active=True).order_by('full_name')
    stats_qs = Assignment.objects.filter(deleted_at__isnull=True)
    stats = {
        'total': stats_qs.count(),
        'today': stats_qs.filter(assign_date=today).count(),
        'this_month': stats_qs.filter(assign_date__year=now.year, assign_date__month=now.month).count(),
        'done': stats_qs.filter(status='Done').count(),
    }
    return _tab_response(request, 'cms/assignments.html', {
        'assignments': qs.order_by('-assign_date', '-created_at')[:20],
        'edit_assignment': assignment,
        'stats': stats,
        'today': today,
        'user': request.user,
        'active_users': active_users,
        'page': 1,
        'has_more': False,
        'start_index': 1,
    })


@login_required
@require_POST
def delete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, id=pk, deleted_at__isnull=True)
    if not _is_owner_or_admin(request.user, assignment):
        return _toast_response('You do not have permission to delete this assignment.', '', 'error')
    assignment.soft_delete(user=request.user)
    return _toast_response('Assignment deleted successfully.', reverse('cms:cms-assignments'))


# ─── Phase 1: HTMX replacements for JSON-API endpoints ───────────────

@login_required
def update_assignment_status(request, pk):
    assignment = get_object_or_404(Assignment, id=pk, deleted_at__isnull=True)
    if request.method == 'POST':
        if not (request.user.is_admin or request.user.is_superuser or str(assignment.member_id) == str(request.user.id)):
            return _toast_response('You do not have permission to change this assignment status.', '', 'error')
        new_status = request.POST.get('status', '')
        valid = [s[0] for s in Assignment.STATUS_CHOICES]
        if new_status in valid:
            assignment.status = new_status
            assignment.updated_by = request.user
            assignment.save()
            labels = dict(Assignment.STATUS_CHOICES)
            return _toast_response(
                'Status updated: %s' % labels.get(new_status, new_status),
                reverse('cms:cms-assignments')
            )
        return _toast_response('Invalid status value.', '', 'error')
    return redirect(reverse('cms:cms-assignments'))


@login_required
def view_assignment(request, pk):
    assignment = get_object_or_404(
        Assignment.objects.select_related('member', 'reporter_user'),
        id=pk, deleted_at__isnull=True,
    )
    content_items = assignment.content_list_items.filter(deleted_at__isnull=True).select_related('member')[:20]
    scripts = assignment.scripts.filter(deleted_at__isnull=True).select_related('writer')[:20]
    audio_items = assignment.audio_items.filter(deleted_at__isnull=True).select_related('member')[:20]
    packages = assignment.final_packages.filter(deleted_at__isnull=True).select_related('member')[:20]
    entries = assignment.content_entries.filter(deleted_at__isnull=True).select_related('member')[:20]

    return _tab_response(request, 'cms/assignment_detail.html', {
        'assignment': assignment,
        'content_items': content_items,
        'scripts': scripts,
        'audio_items': audio_items,
        'packages': packages,
        'entries': entries,
        'user': request.user,
    })


@login_required
def view_content_list(request, pk):
    item = get_object_or_404(
        ContentListItem.objects.select_related('member', 'assignment'),
        id=pk, deleted_at__isnull=True,
    )
    return render(request, 'cms/content_list_detail.html', {
        'item': item,
        'user': request.user,
    })


@login_required
def script_detail(request, pk):
    script = get_object_or_404(Script.objects.select_related('writer', 'approved_by', 'assignment'), id=pk, deleted_at__isnull=True)
    edit_history = script.edit_history.select_related('editor').all()[:20]
    return render(request, 'cms/script_detail.html', {
        'script': script,
        'edit_history': edit_history,
        'user': request.user,
    })


@login_required
def cms_leaderboard_detail(request, user_id):
    target_user = get_object_or_404(User, id=user_id, is_active=True)
    entries = ContentEntry.objects.filter(
        member=target_user, deleted_at__isnull=True
    ).select_related('sponsor').order_by('-entry_date')[:50]
    return render(request, 'cms/leaderboard_detail.html', {
        'target_user': target_user,
        'entries': entries,
        'platforms': PLATFORMS,
    })


@login_required
def new_script_tab(request):
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    return _tab_response(request, 'cms/new_script.html', {
        'today': timezone.now().strftime('%Y-%m-%d'),
        'today_assignments': today_assignments,
        'user': request.user,
    })


@login_required
def cms_admin_reset_password(request, user_id):
    if not request.user.is_admin:
        return _toast_response('Unauthorized.', '', 'error')
    if request.method == 'POST':
        new_pw = request.POST.get('password', '')
        if len(new_pw) < 4:
            return _toast_response('Password must be at least 4 characters.', '', 'error')
        target_user = get_object_or_404(User, id=user_id)
        target_user.set_password(new_pw)
        target_user.save()
        return _admin_response(request, 'Password reset for %s.' % target_user.username)
    return _admin_response(request)


@login_required
def cms_admin_logout_session(request, session_id):
    if not request.user.is_admin:
        return _toast_response('Unauthorized.', '', 'error')
    if request.method == 'POST':
        session = get_object_or_404(UserSession, id=session_id, is_active=True)
        session.is_active = False
        session.save()
        return _admin_response(request, 'Session logged out.')
    return _admin_response(request)





@login_required
def save_script(request):
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment_id', '')
        if assignment_id and not Assignment.objects.filter(id=assignment_id, deleted_at__isnull=True).exists():
            assignment_id = None
        script_id = request.POST.get('script_id', '')
        if script_id:
            script = get_object_or_404(Script, id=script_id, deleted_at__isnull=True)
            old_headline = script.headline
            old_body = script.body
            for field in ('script_date', 'headline', 'source', 'district', 'district_reporter', 'body'):
                setattr(script, field, request.POST.get(field, ''))
            script.assignment_id = assignment_id or None
            script.updated_by = request.user
            script.save()
            if old_headline != script.headline or old_body != script.body:
                ScriptEditHistory.objects.create(
                    script=script,
                    headline=old_headline,
                    body=old_body,
                    editor=request.user,
                    change_summary=request.POST.get('change_summary', ''),
                    created_by=request.user,
                )
            return _toast_response('Script updated successfully.', '/cms/scripts/')
        Script.objects.create(
            script_date=request.POST.get('script_date'),
            headline=request.POST.get('headline', ''),
            source=request.POST.get('source', 'social'),
            writer=request.user,
            district=request.POST.get('district', ''),
            district_reporter=request.POST.get('district_reporter', ''),
            body=request.POST.get('body', ''),
            assignment_id=assignment_id or None,
            created_by=request.user,
        )
        return redirect('cms:cms-scripts')
    return redirect('cms:cms-scripts')


@login_required
def edit_script(request, pk):
    script = get_object_or_404(Script, id=pk, deleted_at__isnull=True)
    today_assignments = Assignment.objects.filter(
        assign_date=timezone.now().date(),
        deleted_at__isnull=True,
    ).select_related('reporter_user', 'member').order_by('created_at')
    return render(request, 'cms/edit_script.html', {
        'script': script,
        'today': timezone.now().strftime('%Y-%m-%d'),
        'today_assignments': today_assignments,
        'user': request.user,
    })


@login_required
def submit_script(request, pk):
    script = get_object_or_404(Script, id=pk, deleted_at__isnull=True)
    if request.method == 'POST':
        if script.writer != request.user:
            return _toast_response('You cannot submit this script.', '', 'error')
        if script.status == 'draft':
            script.status = 'pending'
            script.updated_by = request.user
            script.save()
        return _toast_response('Script submitted for approval.', '/cms/scripts/')
    return redirect('cms:cms-scripts')


@login_required
def approve_script(request, pk):
    script = get_object_or_404(Script, id=pk, deleted_at__isnull=True)
    if request.method == 'POST':
        if not request.user.is_admin:
            return _toast_response('Only admins can approve scripts.', '', 'error')
        if script.status == 'pending':
            script.status = 'approved'
            script.approved_by = request.user
            script.approved_at = timezone.now()
            script.updated_by = request.user
            script.save()
        return _toast_response('Script approved successfully.', '/cms/scripts/')
    return redirect('cms:cms-scripts')


# ─── User Management (Admin) ────────────────────────────────

@login_required
def cms_admin_add_user(request):
    if not request.user.is_admin:
        return _toast_response('Unauthorized.', '', 'error')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        full_name = request.POST.get('full_name', '').strip()
        office_id = request.POST.get('office_id', '').strip()
        designation = request.POST.get('designation', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        blood_group = request.POST.get('blood_group', 'A+')
        make_admin = request.POST.get('is_admin') == 'on'

        if User.objects.filter(username=username).exists():
            return _toast_response('This username is already taken.', '', 'error')
        if User.objects.filter(office_id=office_id).exists():
            return _toast_response('This Office ID is already registered.', '', 'error')
        if len(password) < 4:
            return _toast_response('Password must be at least 4 characters.', '', 'error')

        User.objects.create_user(
            username=username, password=password,
            full_name=full_name, office_id=office_id,
            designation=designation, email=email,
            phone=phone, blood_group=blood_group,
            is_admin=make_admin,
        )
        return _admin_response(request, 'User created successfully.')
    return _admin_response(request)


@login_required
def cms_admin_toggle_admin(request, user_id):
    if not request.user.is_admin:
        return _toast_response('Unauthorized.', '', 'error')
    if request.method == 'POST':
        target = get_object_or_404(User, id=user_id, is_active=True)
        if target.is_founder:
            return _toast_response('Cannot remove admin from the founder account.', '', 'error')
        target.is_admin = not target.is_admin
        target.save()
        label = 'granted admin access.' if target.is_admin else 'removed from admin.'
        return _admin_response(request, '%s %s' % (target.username, label))
    return _admin_response(request)


@login_required
def cms_admin_delete_user(request, user_id):
    if not request.user.is_admin:
        return _toast_response('Unauthorized.', '', 'error')
    if request.method == 'POST':
        target = get_object_or_404(User, id=user_id, is_active=True)
        if target.is_founder:
            return _toast_response('Cannot delete the founder account.', '', 'error')
        if target == request.user:
            return _toast_response('You cannot delete your own account.', '', 'error')
        target.is_active = False
        target.save()
        return _admin_response(request, '%s has been deactivated.' % target.username)
    return _admin_response(request)


@login_required
def approve_registration(request, user_id):
    if not request.user.is_admin:
        return _toast_response('Unauthorized.', '', 'error')
    if request.method == 'POST':
        target = get_object_or_404(User, id=user_id, pending_approval=True)
        target.is_active = True
        target.pending_approval = False
        target.save()
        return _admin_response(request, f'{target.full_name} has been approved!')
    return _admin_response(request)


@login_required
def reject_registration(request, user_id):
    if not request.user.is_admin:
        return _toast_response('Unauthorized.', '', 'error')
    if request.method == 'POST':
        target = get_object_or_404(User, id=user_id, pending_approval=True)
        name = target.full_name
        target.delete()
        return _admin_response(request, f'{name}\'s registration has been rejected.')
    return _admin_response(request)


# ─── Password Reset (Self-Service) ─────────────────────────

@login_required
def cms_logout(request):
    if request.method == 'POST':
        from django.contrib.auth import logout as auth_logout
        auth_logout(request)
    return redirect('cms:cms-login')


def cms_password_reset_request(request):
    if request.user.is_authenticated:
        return redirect('cms:cms-dashboard')
    step = request.GET.get('step', 'request')
    if request.method == 'POST' and step == 'request':
        identifier = request.POST.get('identifier', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        user = User.objects.filter(
            username=identifier, email=email, phone=phone
        ).first()
        if not user:
            return render(request, 'registration/password_reset_request.html', {
                'error': 'No match found. Please verify your username, email and phone number.',
                'identifier': identifier,
                'email': email,
                'phone': phone,
            })
        import random
        otp = str(random.randint(100000, 999999))
        request.session['reset_otp'] = otp
        request.session['reset_user_id'] = str(user.id)
        request.session['reset_identifier'] = identifier
        return render(request, 'registration/password_reset_request.html', {
            'step': 'verify',
            'otp_display': otp,
            'identifier': identifier,
            'user_name': user.full_name,
        })
    if request.method == 'POST' and step == 'verify':
        entered_otp = request.POST.get('otp', '')
        stored_otp = request.session.get('reset_otp')
        if stored_otp != entered_otp:
            return render(request, 'registration/password_reset_request.html', {
                'step': 'verify',
                'otp_error': 'Incorrect code. Please try again.',
                'identifier': request.session.get('reset_identifier', ''),
            })
        return render(request, 'registration/password_reset_confirm.html', {
            'valid': True,
        })
    return render(request, 'registration/password_reset_request.html', {
        'step': 'request',
    })


def cms_password_reset_confirm(request):
    if request.user.is_authenticated:
        return redirect('cms:cms-dashboard')
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('cms:cms-password-reset')
    if request.method == 'POST':
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        if len(password) < 4:
            return render(request, 'registration/password_reset_confirm.html', {
                'error': 'Password must be at least 4 characters.',
            })
        if password != password2:
            return render(request, 'registration/password_reset_confirm.html', {
                'error': 'Passwords do not match.',
            })
        user = get_object_or_404(User, id=user_id)
        user.set_password(password)
        user.save()
        request.session.flush()
        return render(request, 'registration/password_reset_confirm.html', {
            'done': True,
        })
    return redirect('cms:cms-password-reset')


def _notice_response(request, msg=None, msg_type='success'):
    notices = Notice.objects.filter(deleted_at__isnull=True).select_related('created_by')
    return _htmx_response(request, 'cms/notices_section.html', {
        'notices': notices,
    }, msg, msg_type)


@login_required
def notices_tab(request):
    return _notice_response(request)


@login_required
def create_notice(request):
    if not request.user.is_admin:
        return _notice_response(request, 'Only admins can create notices.', 'error')
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        if not title or not content:
            return _notice_response(request, 'Title and content are required.', 'error')
        Notice.objects.create(
            title=title,
            content=content,
            created_by=request.user,
        )
        return _notice_response(request, 'Notice posted successfully!')
    return _notice_response(request)


@login_required
def notice_detail(request, pk):
    notice = get_object_or_404(Notice, id=pk, deleted_at__isnull=True)
    return render(request, 'cms/notice_detail_modal.html', {'notice': notice})


@login_required
@require_POST
def delete_notice(request, pk):
    if not request.user.is_admin:
        return _notice_response(request, 'Only admins can delete notices.', 'error')
    notice = get_object_or_404(Notice, id=pk, deleted_at__isnull=True)
    notice.soft_delete()
    return _notice_response(request, 'Notice deleted successfully!')


# ─── ROLE & PERMISSION MANAGEMENT ───

def _get_permission_tree():
    """Return all permissions grouped by app with human-readable names."""
    cts = ContentType.objects.prefetch_related('permission_set').order_by('app_label', 'model')
    tree = {}
    for ct in cts:
        perms = ct.permission_set.all()
        if not perms.exists():
            continue
        mc = ct.model_class()
        app_verbose = str(mc._meta.app_config.verbose_name if mc and hasattr(mc._meta, 'app_config') else ct.app_label)
        model_verbose = str(mc._meta.verbose_name if mc else ct.model)
        app_label = ct.app_label
        if app_label not in tree:
            tree[app_label] = {'verbose_name': app_verbose, 'models': {}}
        tree[app_label]['models'][ct.model] = {
            'verbose_name': model_verbose,
            'perms': list(perms),
        }
    return tree


@login_required
def roles_tab(request):
    if not request.user.is_admin:
        return HttpResponse('Unauthorized', status=403)
    groups = Group.objects.annotate(user_count=Count('user')).order_by('name')
    permission_tree = _get_permission_tree()
    return _tab_response(request, 'cms/roles_list.html', {
        'groups': groups,
        'permission_tree': permission_tree,
    })


@login_required
def save_role(request):
    if not request.user.is_admin:
        return HttpResponse('Unauthorized', status=403)
    if request.method == 'POST':
        role_id = request.POST.get('role_id', '').strip()
        name = request.POST.get('name', '').strip()
        if not name:
            return _toast_response('Role name is required.', '/cms/admin-panel/roles/', 'error')
        group, created = (Group.objects.get_or_create(id=role_id, defaults={'name': name})
                          if role_id else (Group.objects.create(name=name), True))
        if not created and role_id:
            group.name = name
            group.save(update_fields=['name'])
        perm_ids = request.POST.getlist('permissions')
        group.permissions.set(Permission.objects.filter(id__in=perm_ids))
        msg = f'Role "{name}" {"created" if created else "updated"} with {len(perm_ids)} permission(s).'
        return _toast_response(msg, '/cms/admin-panel/roles/')
    return redirect('cms:cms-roles')


@login_required
def edit_role(request, pk):
    if not request.user.is_admin:
        return HttpResponse('Unauthorized', status=403)
    group = get_object_or_404(Group, id=pk)
    permission_tree = _get_permission_tree()
    selected = set(group.permissions.values_list('id', flat=True))
    return render(request, 'cms/role_form.html', {
        'group': group,
        'permission_tree': permission_tree,
        'selected': selected,
    })


@login_required
@require_POST
def delete_role(request, pk):
    if not request.user.is_admin:
        return HttpResponse('Unauthorized', status=403)
    group = get_object_or_404(Group, id=pk)
    name = group.name
    group.delete()
    return _toast_response(f'Role "{name}" deleted.', '/cms/admin-panel/roles/')


# ─── USER DETAIL & EDIT ───

@login_required
def user_detail_tab(request, user_id):
    if not request.user.is_admin:
        return HttpResponse('Unauthorized', status=403)
    target = get_object_or_404(User, id=user_id)
    sessions = UserSession.objects.filter(user=target).order_by('-login_at')[:10]
    return _tab_response(request, 'cms/user_detail.html', {
        'target_user': target,
        'sessions': sessions,
    })


@login_required
def user_edit_tab(request, user_id):
    if not request.user.is_admin:
        return HttpResponse('Unauthorized', status=403)
    target = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        target.full_name = request.POST.get('full_name', target.full_name)
        target.designation = request.POST.get('designation', target.designation)
        target.office_id = request.POST.get('office_id', target.office_id)
        target.email = request.POST.get('email', target.email)
        target.phone = request.POST.get('phone', target.phone)
        target.blood_group = request.POST.get('blood_group', target.blood_group)
        target.is_active = request.POST.get('is_active') == '1'
        target.save(update_fields=[
            'full_name', 'designation', 'office_id', 'email',
            'phone', 'blood_group', 'is_active',
        ])
        group_ids = request.POST.getlist('groups')
        target.groups.set(Group.objects.filter(id__in=group_ids))
        perm_ids = request.POST.getlist('user_permissions')
        target.user_permissions.set(Permission.objects.filter(id__in=perm_ids))
        return redirect('cms:cms-admin')
    groups = Group.objects.all().order_by('name')
    user_group_ids = set(target.groups.values_list('id', flat=True))
    user_perm_ids = set(target.user_permissions.values_list('id', flat=True))
    permission_tree = _get_permission_tree()
    return _tab_response(request, 'cms/user_edit.html', {
        'target_user': target,
        'groups': groups,
        'user_group_ids': user_group_ids,
        'permission_tree': permission_tree,
        'selected': user_perm_ids,
    })


# ─── ARCHIVE SYSTEM ───

MODULE_MAP = [
    ('entries', 'Content Entries', 'bi-file-earmark-text-fill'),
    ('assignments', 'Assignments', 'bi-pin-angle-fill'),
    ('contentlist', 'Content List', 'bi-card-checklist'),
    ('audio', 'Audio', 'bi-music-note-beamed'),
    ('scripts', 'Digital Scripts', 'bi-file-earmark-code-fill'),
    ('finalpackage', 'Final Packages', 'bi-box-seam-fill'),
]

MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']


@login_required
def archive_tab(request):
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))
    module = request.GET.get('module', 'entries')
    search_q = request.GET.get('search', '').strip()

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    items = []
    count = 0

    if module == 'entries':
        qs = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=start_date,
            entry_date__lt=end_date,
        ).select_related('member', 'sponsor').order_by('-entry_date', '-entry_time')
        if search_q:
            qs = qs.filter(Q(headline__icontains=search_q) | Q(slug__icontains=search_q) | Q(member__username__icontains=search_q))
        count = qs.count()
        items = qs[:200]

    elif module == 'assignments':
        qs = Assignment.objects.filter(
            deleted_at__isnull=True,
            assign_date__gte=start_date,
            assign_date__lt=end_date,
        ).select_related('member', 'reporter_user').order_by('-assign_date', '-created_at')
        if search_q:
            qs = qs.filter(Q(caption__icontains=search_q) | Q(reporter__icontains=search_q) | Q(district__icontains=search_q))
        count = qs.count()
        items = qs[:200]

    elif module == 'contentlist':
        qs = ContentListItem.objects.filter(
            deleted_at__isnull=True,
            list_date__gte=start_date,
            list_date__lt=end_date,
        ).select_related('member', 'assignment').order_by('-list_date', '-created_at')
        if search_q:
            qs = qs.filter(Q(content__icontains=search_q) | Q(district__icontains=search_q) | Q(member__username__icontains=search_q))
        count = qs.count()
        items = qs[:200]

    elif module == 'audio':
        qs = AudioItem.objects.filter(
            deleted_at__isnull=True,
            audio_date__gte=start_date,
            audio_date__lt=end_date,
        ).select_related('member', 'assignment').order_by('-audio_date', '-created_at')
        if search_q:
            qs = qs.filter(Q(title__icontains=search_q) | Q(district__icontains=search_q) | Q(member__username__icontains=search_q))
        count = qs.count()
        items = qs[:200]

    elif module == 'scripts':
        qs = Script.objects.filter(
            deleted_at__isnull=True,
            script_date__gte=start_date,
            script_date__lt=end_date,
        ).select_related('writer', 'assignment').order_by('-script_date', '-created_at')
        if search_q:
            qs = qs.filter(Q(headline__icontains=search_q) | Q(district__icontains=search_q) | Q(writer__username__icontains=search_q))
        count = qs.count()
        items = qs[:200]

    elif module == 'finalpackage':
        qs = FinalPackage.objects.filter(
            deleted_at__isnull=True,
            package_date__gte=start_date,
            package_date__lt=end_date,
        ).select_related('member', 'assignment').order_by('-package_date', '-created_at')
        if search_q:
            qs = qs.filter(Q(title__icontains=search_q) | Q(producer__icontains=search_q) | Q(member__username__icontains=search_q))
        count = qs.count()
        items = qs[:200]

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return _tab_response(request, 'cms/archive.html', {
        'module': module,
        'year': year,
        'month': month,
        'month_name': MONTH_NAMES[month],
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'module_map': MODULE_MAP,
        'items': items,
        'count': count,
        'search': search_q,
        'today': now.date(),
        'user': request.user,
    })


# ─── REPORT GENERATOR ───

REPORT_MODULE_CHOICES = ReportConfig.MODULE_CHOICES
REPORT_AGG_CHOICES = ReportConfig.AGGREGATION_CHOICES
REPORT_PERIOD_CHOICES = ReportConfig.PERIOD_CHOICES
REPORT_CHART_CHOICES = ReportConfig.CHART_CHOICES


@login_required
def reports_tab(request):
    configs = ReportConfig.objects.filter(created_by=request.user, is_deleted=False)
    return _tab_response(request, 'reports/reports_list.html', {
        'configs': configs,
    })


@login_required
def report_builder(request, pk=None):
    config = None
    if pk:
        config = get_object_or_404(ReportConfig, pk=pk, created_by=request.user, is_deleted=False)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        module = request.POST.get('module', 'entries')
        aggregation = request.POST.get('aggregation', 'list')
        period = request.POST.get('period', 'this_month')
        date_from = request.POST.get('date_from', '') or None
        date_to = request.POST.get('date_to', '') or None
        show_chart = request.POST.get('show_chart', 'none')
        filters = {}
        for key in request.POST:
            if key.startswith('filter_'):
                val = request.POST.get(key)
                if val:
                    filters[key.replace('filter_', '', 1)] = val
        if name:
            if config:
                config.name = name
                config.description = description
                config.module = module
                config.aggregation = aggregation
                config.period = period
                config.date_from = date_from
                config.date_to = date_to
                config.show_chart = show_chart
                config.filters = filters
                config.save()
            else:
                config = ReportConfig.objects.create(
                    name=name, description=description, module=module,
                    aggregation=aggregation, period=period,
                    date_from=date_from, date_to=date_to,
                    show_chart=show_chart, filters=filters,
                    created_by=request.user,
                )
            return redirect('cms:cms-reports')
    return render(request, 'reports/report_builder.html', {
        'config': config,
        'modules': REPORT_MODULE_CHOICES,
        'aggregations': REPORT_AGG_CHOICES,
        'periods': REPORT_PERIOD_CHOICES,
        'charts': REPORT_CHART_CHOICES,
    })


@login_required
@require_POST
def report_delete(request, pk):
    config = get_object_or_404(ReportConfig, pk=pk, created_by=request.user)
    config.is_deleted = True
    config.save()
    return redirect('cms:cms-reports')


@login_required
def report_run(request, pk):
    config = get_object_or_404(ReportConfig, pk=pk, created_by=request.user, is_deleted=False)
    engine = ReportEngine(config)
    engine.execute()
    return render(request, 'reports/report_output.html', {
        'config': config,
        'engine': engine,
    })


@login_required
def report_export_csv(request, pk):
    config = get_object_or_404(ReportConfig, pk=pk, created_by=request.user, is_deleted=False)
    engine = ReportEngine(config)
    engine.execute()
    csv_data = engine.to_csv()
    response = HttpResponse(csv_data, content_type='text/csv; charset=utf-8-sig')
    safe_name = config.name.replace(' ', '_').replace('/', '_')[:50]
    response['Content-Disposition'] = f'attachment; filename="{safe_name}.csv"'
    return response


@login_required
def report_export_pdf(request, pk):
    config = get_object_or_404(ReportConfig, pk=pk, created_by=request.user, is_deleted=False)
    engine = ReportEngine(config)
    engine.execute()
    from django.template.loader import render_to_string
    html = render_to_string('reports/report_pdf.html', {
        'config': config,
        'engine': engine,
    })
    try:
        from weasyprint import HTML
        pdf_file = io.BytesIO()
        HTML(string=html).write_pdf(pdf_file)
        pdf_file.seek(0)
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        safe_name = config.name.replace(' ', '_').replace('/', '_')[:50]
        response['Content-Disposition'] = f'attachment; filename="{safe_name}.pdf"'
        return response
    except ImportError:
        response = HttpResponse(html, content_type='text/html; charset=utf-8')
        safe_name = config.name.replace(' ', '_').replace('/', '_')[:50]
        response['Content-Disposition'] = f'inline; filename="{safe_name}.html"'
        return response
