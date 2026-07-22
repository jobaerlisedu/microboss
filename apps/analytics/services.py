from datetime import date, timedelta, datetime
from collections import OrderedDict, defaultdict
from django.db.models import Count, Sum, Q, Avg, F, Value, IntegerField, CharField, Case, When
from django.db.models.functions import TruncDate, TruncMonth, ExtractYear, ExtractMonth, ExtractWeekDay, ExtractHour, Coalesce
from django.utils import timezone
from apps.content.models import ContentEntry
from apps.sponsors.models import Sponsor
from apps.contentlist.models import ContentListItem
from apps.assignments.models import Assignment
from apps.scripts.models import Script
from apps.notices.models import Notice
from apps.accounts.models import User, UserSession
from apps.audit.models import AuditLog


ALIGNMENT_DAYS = 7
PLATFORM_KEYS = ['fb', 'yt', 'ig', 'threads', 'tt', 'linkedin', 'bsky', 'dm', 'reddit']
PLATFORM_LABELS = {
    'fb': 'Facebook', 'yt': 'YouTube', 'ig': 'Instagram',
    'threads': 'Threads', 'tt': 'TikTok', 'linkedin': 'LinkedIn',
    'bsky': 'Bluesky', 'dm': 'Dailymotion', 'reddit': 'Reddit',
}
PLATFORM_COLORS = {
    'fb': '#3B82F6', 'yt': '#EF4444', 'ig': '#DD2A7B',
    'threads': '#111827', 'tt': '#000000', 'linkedin': '#0A66C2',
    'bsky': '#1185FE', 'dm': '#00A0DE', 'reddit': '#FF4500',
}


def _start_of_day(days_ago=0):
    return timezone.now().date() - timedelta(days=days_ago)


def _default_range(days=30):
    end = timezone.now().date()
    start = end - timedelta(days=days)
    return start, end


class AnalyticsService:
    def __init__(self, start_date=None, end_date=None):
        now = timezone.now().date()
        self.end_date = end_date or now
        self.start_date = start_date or (self.end_date - timedelta(days=30))
        if self.start_date > self.end_date:
            self.start_date, self.end_date = self.end_date, self.start_date
        self._entries = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=self.start_date,
            entry_date__lte=self.end_date,
        )
        period_days = (self.end_date - self.start_date).days or 1
        self._prev_start = self.start_date - timedelta(days=period_days)

    def kpi_summary(self):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        total_entries = ContentEntry.objects.filter(deleted_at__isnull=True).count()
        today_entries = ContentEntry.objects.filter(
            deleted_at__isnull=True, entry_date=today
        ).count()
        month_entries = ContentEntry.objects.filter(
            deleted_at__isnull=True, entry_date__gte=month_start, entry_date__lte=today
        ).count()
        active_sponsors = Sponsor.objects.filter(
            deleted_at__isnull=True,
            start_date__lte=today, end_date__gte=today
        ).count()
        total_sponsors = Sponsor.objects.filter(deleted_at__isnull=True).count()
        total_scripts = Script.objects.filter(deleted_at__isnull=True).count()
        pending_scripts = Script.objects.filter(deleted_at__isnull=True, status='pending').count()
        total_assignments = Assignment.objects.filter(deleted_at__isnull=True).count()
        active_assignments = Assignment.objects.filter(
            deleted_at__isnull=True, status__in=['Assigned', 'Processing']
        ).count()
        completed_assignments = Assignment.objects.filter(
            deleted_at__isnull=True, status='Done'
        ).count()
        total_users = User.objects.filter(is_active=True).count()
        sponsored_count = ContentEntry.objects.filter(
            deleted_at__isnull=True, sponsor__isnull=False
        ).count()
        organic_count = total_entries - sponsored_count
        total_notices = Notice.objects.filter(deleted_at__isnull=True, is_active=True).count()
        approved_scripts = Script.objects.filter(
            deleted_at__isnull=True, status='approved'
        ).count()
        period_entries = self._entries.count()
        prev_period = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=self._prev_start,
            entry_date__lt=self.start_date,
        ).count()
        growth_pct = 0
        if prev_period > 0:
            growth_pct = round((period_entries - prev_period) / prev_period * 100, 1)
        return {
            'total_entries': total_entries,
            'today_entries': today_entries,
            'month_entries': month_entries,
            'active_sponsors': active_sponsors,
            'total_sponsors': total_sponsors,
            'total_scripts': total_scripts,
            'pending_scripts': pending_scripts,
            'total_assignments': total_assignments,
            'active_assignments': active_assignments,
            'completed_assignments': completed_assignments,
            'approved_scripts': approved_scripts,
            'total_users': total_users,
            'total_notices': total_notices,
            'sponsored_entries': sponsored_count,
            'organic_entries': organic_count,
            'period_entries': period_entries,
            'prev_period_entries': prev_period,
            'growth_pct': growth_pct,
        }

    def content_trend(self, interval='day'):
        if interval == 'month':
            qs = self._entries.annotate(
                period=TruncMonth('entry_date')
            ).values('period').annotate(
                total=Count('id')
            ).order_by('period')
        else:
            qs = self._entries.annotate(
                period=TruncDate('entry_date')
            ).values('period').annotate(
                total=Count('id')
            ).order_by('period')
        labels, values = [], []
        data_map = {str(r['period']): r['total'] for r in qs if r['period']}
        current = self.start_date
        if interval == 'month':
            while current <= self.end_date:
                key = current.strftime('%Y-%m-01')
                labels.append(current.strftime('%b %Y'))
                values.append(data_map.get(str(current.replace(day=1)), 0))
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        else:
            while current <= self.end_date:
                labels.append(current.strftime('%d %b'))
                values.append(data_map.get(str(current), 0))
                current += timedelta(days=1)

        moving_avg = self._moving_average(values, window=min(7, len(values)))
        forecast = self._linear_forecast(values, steps=7)
        return {
            'labels': labels,
            'values': values,
            'interval': interval,
            'moving_avg': moving_avg,
            'forecast': forecast,
        }

    def daily_trend(self, days=7):
        today = timezone.now().date()
        start = today - timedelta(days=days - 1)
        qs = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=start,
            entry_date__lte=today,
        ).annotate(
            period=TruncDate('entry_date')
        ).values('period').annotate(
            total=Count('id')
        ).order_by('period')
        data_map = {str(r['period']): r['total'] for r in qs if r['period']}
        labels, values = [], []
        current = start
        while current <= today:
            labels.append(current.strftime('%a'))
            values.append(data_map.get(str(current), 0))
            current += timedelta(days=1)
        avg_val = round(sum(values) / max(len(values), 1), 1)
        peak_val = max(values) if values else 0
        return {
            'labels': labels,
            'values': values,
            'total': sum(values),
            'average': avg_val,
            'peak': peak_val,
        }

    def weekly_trend(self, weeks=8):
        today = timezone.now().date()
        start = today - timedelta(weeks=weeks)
        qs = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=start,
        ).annotate(
            year=ExtractYear('entry_date'),
            week=F('entry_date') - Value(timedelta(days=1)),
        ).extra(
            select={'iso_week': "WEEK(entry_date, 3)"}
        ).values('iso_week', 'year').annotate(
            total=Count('id')
        ).order_by('year', 'iso_week')
        return {
            'labels': [f"W{r['iso_week']}" for r in qs],
            'values': [r['total'] for r in qs],
        }

    def platform_breakdown(self):
        platform_counts = defaultdict(int)
        total_with_links = 0
        for entry_links in self._entries.values_list('links', flat=True).iterator():
            has_link = False
            for key in PLATFORM_KEYS:
                if entry_links and entry_links.get(key):
                    platform_counts[key] += 1
                    has_link = True
            if has_link:
                total_with_links += 1
        total = total_with_links or 1
        breakdown = []
        for key in PLATFORM_KEYS:
            count = platform_counts.get(key, 0)
            if count > 0:
                breakdown.append({
                    'key': key,
                    'label': PLATFORM_LABELS[key],
                    'color': PLATFORM_COLORS[key],
                    'count': count,
                    'pct': round(count / total * 100, 1),
                })
        breakdown.sort(key=lambda x: x['count'], reverse=True)
        other_count = sum(b['count'] for b in breakdown[5:])
        if other_count > 0:
            breakdown = breakdown[:5]
            breakdown.append({
                'key': 'other', 'label': 'Others',
                'color': '#94a3b8', 'count': other_count,
                'pct': round(other_count / total * 100, 1),
            })
        return {'breakdown': breakdown, 'total_links': total}

    def sponsored_vs_organic(self):
        total = self._entries.count() or 1
        sponsored = self._entries.filter(sponsor__isnull=False).count()
        organic = total - sponsored
        return {
            'sponsored': sponsored,
            'organic': organic,
            'sponsored_pct': round(sponsored / total * 100, 1),
            'organic_pct': round(organic / total * 100, 1),
        }

    def member_performance(self, limit=10):
        qs = self._entries.values(
            'member__id', 'member__full_name', 'member__username'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:limit]
        members = []
        rank = 1
        for r in qs:
            members.append({
                'rank': rank,
                'id': r['member__id'],
                'name': r['member__full_name'] or r['member__username'],
                'username': r['member__username'],
                'total': r['total'],
            })
            rank += 1
        return members

    def member_trend(self, limit=5):
        """Publishing trend for top N members over the period."""
        top_ids = self._entries.values('member').annotate(
            total=Count('id')
        ).order_by('-total')[:limit]
        member_ids = [t['member'] for t in top_ids if t['member']]
        if not member_ids:
            return []
        users = {u.id: u for u in User.objects.filter(id__in=member_ids)}
        entries = ContentEntry.objects.filter(
            deleted_at__isnull=True, member_id__in=member_ids,
            entry_date__gte=self.start_date, entry_date__lte=self.end_date,
        ).annotate(
            day=TruncDate('entry_date')
        ).values('member_id', 'day').annotate(total=Count('id')).order_by('member_id', 'day')
        by_member = defaultdict(lambda: defaultdict(int))
        for r in entries:
            if r['day']:
                by_member[r['member_id']][str(r['day'])] = r['total']
        data = []
        for mid in member_ids:
            user = users.get(mid)
            if not user:
                continue
            trend_map = by_member[mid]
            values = []
            current = self.start_date
            while current <= self.end_date:
                values.append(trend_map.get(str(current), 0))
                current += timedelta(days=1)
            data.append({
                'name': user.full_name or user.username,
                'total': sum(values),
                'values': values,
            })
        return data

    def assignment_metrics(self):
        assignments = Assignment.objects.filter(
            deleted_at__isnull=True,
            assign_date__gte=self.start_date,
            assign_date__lte=self.end_date,
        )
        done = assignments.filter(status='Done').count()
        assigned = assignments.filter(status='Assigned').count()
        processing = assignments.filter(status='Processing').count()
        cancelled = assignments.filter(status='Cancel').count()
        total = assignments.count() or 1
        completion_rate = round(done / total * 100, 1) if total else 0
        return {
            'total': total,
            'done': done,
            'assigned': assigned,
            'processing': processing,
            'cancelled': cancelled,
            'done_pct': round(done / total * 100, 1),
            'assigned_pct': round(assigned / total * 100, 1),
            'processing_pct': round(processing / total * 100, 1),
            'cancelled_pct': round(cancelled / total * 100, 1),
            'completion_rate': completion_rate,
        }

    def assignment_trend(self):
        """Daily assignment completion trend."""
        assignments = Assignment.objects.filter(
            deleted_at__isnull=True,
            assign_date__gte=self.start_date,
            assign_date__lte=self.end_date,
        )
        created_trend = assignments.annotate(
            day=TruncDate('assign_date')
        ).values('day').annotate(total=Count('id')).order_by('day')
        created_map = {str(r['day']): r['total'] for r in created_trend if r['day']}
        done_qs = assignments.filter(status='Done').annotate(
            day=TruncDate('assign_date')
        ).values('day').annotate(total=Count('id')).order_by('day')
        done_map = {str(r['day']): r['total'] for r in done_qs if r['day']}
        labels, created_vals, done_vals = [], [], []
        current = self.start_date
        while current <= self.end_date:
            labels.append(current.strftime('%d %b'))
            created_vals.append(created_map.get(str(current), 0))
            done_vals.append(done_map.get(str(current), 0))
            current += timedelta(days=1)
        return {'labels': labels, 'created': created_vals, 'done': done_vals}

    def script_metrics(self):
        scripts = Script.objects.filter(
            deleted_at__isnull=True,
            script_date__gte=self.start_date,
            script_date__lte=self.end_date,
        )
        total = scripts.count() or 1
        draft = scripts.filter(status='draft').count()
        pending = scripts.filter(status='pending').count()
        approved = scripts.filter(status='approved').count()
        approval_rate = round(approved / total * 100, 1) if total else 0
        return {
            'total': total,
            'draft': draft,
            'pending': pending,
            'approved': approved,
            'draft_pct': round(draft / total * 100, 1),
            'pending_pct': round(pending / total * 100, 1),
            'approved_pct': round(approved / total * 100, 1),
            'approval_rate': approval_rate,
        }

    def content_list_sources(self):
        items = ContentListItem.objects.filter(
            list_date__gte=self.start_date,
            list_date__lte=self.end_date,
        )
        sources = items.values('source').annotate(
            total=Count('id')
        ).order_by('-total')
        total = items.count() or 1
        result = []
        for s in sources:
            result.append({
                'source': s['source'],
                'total': s['total'],
                'pct': round(s['total'] / total * 100, 1),
            })
        return {'sources': result, 'total': items.count()}

    def content_list_structure(self):
        """Composition analysis of content list items."""
        items = ContentListItem.objects.filter(
            list_date__gte=self.start_date,
            list_date__lte=self.end_date,
        )
        total = items.count()
        footage = items.values('footage_source').annotate(
            total=Count('id')
        ).filter(footage_source__gt='').order_by('-total')
        return {
            'total': total,
            'footage_breakdown': list(footage),
        }

    def sponsor_performance(self):
        active = Sponsor.objects.filter(
            deleted_at__isnull=True,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date,
        )
        sponsor_ids = [sp.id for sp in active]
        usage_map = defaultdict(int)
        if sponsor_ids:
            usage_qs = ContentEntry.objects.filter(
                deleted_at__isnull=True,
                sponsor_id__in=sponsor_ids,
                entry_date__gte=self.start_date,
                entry_date__lte=self.end_date,
            ).values('sponsor_id').annotate(total=Count('id'))
            for r in usage_qs:
                usage_map[r['sponsor_id']] = r['total']
        result = []
        for sp in active:
            result.append({
                'id': sp.id,
                'name': sp.name,
                'daily_quota': sp.daily_quota,
                'total_quota': sp.total_quota,
                'period_used': usage_map.get(sp.id, 0),
                'is_active': sp.is_active,
                'progress_pct': sp.progress_pct,
                'today_remaining': sp.today_remaining,
                'start_date': sp.start_date.isoformat(),
                'end_date': sp.end_date.isoformat(),
            })
        return result

    def user_activity_timeline(self, days=7, limit=20):
        since = timezone.now() - timedelta(days=days)
        logs = AuditLog.objects.filter(created_at__gte=since).order_by('-created_at')[:limit]
        activity = []
        for log in logs:
            activity.append({
                'username': log.username,
                'action': log.action,
                'content_type': log.content_type,
                'object_repr': log.object_repr,
                'timestamp': log.created_at.isoformat(),
                'ip_address': log.ip_address,
            })
        return activity

    def session_metrics(self):
        total_sessions = UserSession.objects.filter(is_active=True).count()
        recent_logins = UserSession.objects.filter(
            login_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        today = timezone.now().date()
        today_logins = UserSession.objects.filter(
            login_at__date=today
        ).count()
        return {
            'active_sessions': total_sessions,
            'recent_24h_logins': recent_logins,
            'today_logins': today_logins,
        }

    def monthly_comparison(self):
        this_month_start = self.start_date
        this_month_end = self.end_date
        prev_period_days = (this_month_end - this_month_start).days or 1
        prev_month_start = this_month_start - timedelta(days=prev_period_days)
        prev_month_end = this_month_start - timedelta(days=1)
        this_qs = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=this_month_start,
            entry_date__lte=this_month_end,
        )
        prev_qs = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=prev_month_start,
            entry_date__lte=prev_month_end,
        )
        this_count = this_qs.count()
        prev_count = prev_qs.count()
        change = this_count - prev_count
        change_pct = 0
        if prev_count > 0:
            change_pct = round(change / prev_count * 100, 1)
        this_sponsored = this_qs.filter(sponsor__isnull=False).count()
        prev_sponsored = prev_qs.filter(sponsor__isnull=False).count()
        this_organic = this_count - this_sponsored
        prev_organic = prev_count - prev_sponsored
        return {
            'current_period': {
                'start': this_month_start.isoformat(),
                'end': this_month_end.isoformat(),
                'total': this_count,
                'sponsored': this_sponsored,
                'organic': this_organic,
            },
            'previous_period': {
                'start': prev_month_start.isoformat(),
                'end': prev_month_end.isoformat(),
                'total': prev_count,
                'sponsored': prev_sponsored,
                'organic': prev_organic,
            },
            'change': change,
            'change_pct': change_pct,
        }

    def content_list_stats(self):
        items = ContentListItem.objects.filter(
            list_date__gte=self.start_date,
            list_date__lte=self.end_date,
        )
        districts = items.values('district').annotate(
            total=Count('id')
        ).filter(district__gt='').order_by('-total')[:10]
        sources = items.values('source').annotate(
            total=Count('id')
        ).order_by('-total')
        daily = items.annotate(
            period=TruncDate('list_date')
        ).values('period').annotate(
            total=Count('id')
        ).order_by('period')
        return {
            'total': items.count(),
            'top_districts': list(districts),
            'sources': list(sources),
            'daily_trend': [
                {'date': str(r['period']), 'total': r['total']}
                for r in daily if r['period']
            ],
        }

    def day_of_week_analysis(self):
        """Content entry distribution by day of week."""
        entries = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=self.start_date,
            entry_date__lte=self.end_date,
        ).annotate(
            dow=ExtractWeekDay('entry_date')
        ).values('dow').annotate(
            total=Count('id')
        ).order_by('dow')
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        result = {day: 0 for day in day_names}
        for r in entries:
            idx = (r['dow'] - 1) % 7
            result[day_names[idx]] = r['total']
        total = sum(result.values()) or 1
        labels = day_names
        values = [result[d] for d in day_names]
        return {
            'labels': labels,
            'values': values,
            'peak_day': day_names[values.index(max(values))] if values else '',
            'peak_value': max(values) if values else 0,
        }

    def hourly_analysis(self):
        """Extract hourly distribution from entry_time."""
        hourly = [0] * 24
        for entry_time in ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__gte=self.start_date,
            entry_date__lte=self.end_date,
        ).values_list('entry_time', flat=True).iterator():
            if entry_time:
                try:
                    hour = entry_time.hour if hasattr(entry_time, 'hour') else int(str(entry_time).split(':')[0])
                    hourly[hour] += 1
                except (ValueError, IndexError):
                    pass
        labels = [f'{h:02d}:00' for h in range(24)]
        return {
            'labels': labels,
            'values': hourly,
        }

    def export_summary_csv(self):
        import csv
        from io import StringIO
        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(['Metric', 'Value', 'Period'])
        kpi = self.kpi_summary()
        for k, v in kpi.items():
            w.writerow([k.replace('_', ' ').title(), v, f'{self.start_date} to {self.end_date}'])
        w.writerow([])
        w.writerow(['Daily Trend'])
        trend = self.daily_trend(7)
        for label, val in zip(trend['labels'], trend['values']):
            w.writerow([label, val, ''])
        buf.seek(0)
        return buf.getvalue()

    def _moving_average(self, values, window=7):
        if len(values) < window:
            return []
        result = []
        for i in range(len(values)):
            start = max(0, i - window + 1)
            chunk = values[start:i + 1]
            result.append(round(sum(chunk) / len(chunk), 1))
        return result

    def _linear_forecast(self, values, steps=7):
        if len(values) < 3:
            return []
        n = len(values)
        x_avg = (n - 1) / 2
        y_avg = sum(values) / n
        num = sum(i * values[i] for i in range(n)) - n * x_avg * y_avg
        den = sum(i * i for i in range(n)) - n * x_avg * x_avg
        slope = num / den if den else 0
        intercept = y_avg - slope * x_avg
        forecast = []
        for i in range(steps):
            pred = max(0, round(slope * (n + i) + intercept))
            forecast.append(pred)
        return forecast


def get_dashboard_data(period='month', days=30):
    today = timezone.now().date()
    if period == 'week':
        start = today - timedelta(days=7)
    elif period == 'quarter':
        start = today - timedelta(days=90)
    elif period == 'year':
        start = today.replace(month=1, day=1)
    else:
        start = today - timedelta(days=days)
    svc = AnalyticsService(start_date=start, end_date=today)
    return {
        'kpi': svc.kpi_summary(),
        'daily_trend': svc.daily_trend(7),
        'content_trend': svc.content_trend('day'),
        'platform_breakdown': svc.platform_breakdown(),
        'sponsored_vs_organic': svc.sponsored_vs_organic(),
        'member_performance': svc.member_performance(limit=10),
        'member_trend': svc.member_trend(limit=5),
        'assignment_metrics': svc.assignment_metrics(),
        'assignment_trend': svc.assignment_trend(),
        'script_metrics': svc.script_metrics(),
        'content_list_sources': svc.content_list_sources(),
        'content_list_structure': svc.content_list_structure(),
        'sponsor_performance': svc.sponsor_performance(),
        'monthly_comparison': svc.monthly_comparison(),
        'session_metrics': svc.session_metrics(),
        'content_list_stats': svc.content_list_stats(),
        'day_of_week': svc.day_of_week_analysis(),
        'hourly': svc.hourly_analysis(),
        'period': {
            'start': start.isoformat(),
            'end': today.isoformat(),
            'label': period,
        },
    }
