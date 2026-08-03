import csv
import io
from collections import OrderedDict
from datetime import date, timedelta
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
from apps.content.models import ContentEntry
from apps.sponsors.models import Sponsor
from apps.accounts.models import User


def _resolve_period(period, date_from=None, date_to=None):
    today = timezone.now().date()
    if period == 'custom' and date_from and date_to:
        return date_from, date_to
    periods = {
        'today': (today, today),
        'yesterday': (today - timedelta(1), today - timedelta(1)),
        'this_week': (today - timedelta(days=today.weekday()), today),
        'last_week': (today - timedelta(days=today.weekday() + 7), today - timedelta(days=today.weekday() + 1)),
        'this_month': (today.replace(day=1), today),
        'last_month': ((today.replace(day=1) - timedelta(1)).replace(day=1), today.replace(day=1) - timedelta(1)),
        'this_quarter': (date(today.year, ((today.month - 1) // 3) * 3 + 1, 1), today),
        'this_year': (date(today.year, 1, 1), today),
    }
    return periods.get(period, (today.replace(day=1), today))


MODEL_MAP = {
    'entries': ContentEntry,
    'sponsors': Sponsor,
    'users': User,
}

DATE_FIELD_MAP = {
    'entries': 'entry_date',
    'sponsors': 'start_date',
    'users': 'date_joined',
}

STATUS_FIELD_MAP = {}

SOURCE_FIELD_MAP = {}

LABEL_MAP = {
    'entries': ('Entry Date', 'Headline', 'Member', 'Sponsor', 'Platform'),
    'sponsors': ('Start Date', 'Name', 'Daily Quota', 'Total Quota', 'Status'),
    'users': ('Joined', 'Username', 'Full Name', 'Designation', 'Role'),
}

MEMBER_FIELD_MAP = {
    'entries': 'member',
}

DISTRICT_FIELD_MAP = {}


class ReportEngine:
    def __init__(self, config):
        self.config = config
        self.module = config.module if config.module in MODEL_MAP else 'entries'
        self.aggregation = config.aggregation
        self.period = config.period
        self.date_from, self.date_to = _resolve_period(config.period, config.date_from, config.date_to)
        self.filters = config.filters or {}
        self.model = MODEL_MAP.get(self.module, ContentEntry)
        self.date_field = DATE_FIELD_MAP.get(self.module, 'entry_date')
        self.headers = []
        self.rows = []
        self.summary = {}
        self.chart_data = {}
        self.title = config.name
        self.description = config.description

    def _base_qs(self):
        qs = self.model.objects.all()
        if hasattr(self.model, 'deleted_at'):
            qs = qs.filter(deleted_at__isnull=True)
        if self.date_from and self.date_to:
            kwargs = {f'{self.date_field}__gte': self.date_from, f'{self.date_field}__lte': self.date_to}
            qs = qs.filter(**kwargs)
        for key, val in self.filters.items():
            if val:
                qs = qs.filter(**{key: val})
        return qs

    def _fmt(self, obj, field):
        val = getattr(obj, field, '')
        if val is None:
            return '—'
        if isinstance(val, date):
            return val.isoformat()
        if hasattr(val, 'username'):
            return val.username
        if hasattr(val, 'name'):
            return val.name
        return str(val)

    def _label(self, idx, fallback=''):
        labels = LABEL_MAP.get(self.module, ())
        return labels[idx] if idx < len(labels) else fallback

    def _member_field(self):
        return MEMBER_FIELD_MAP.get(self.module)

    def _status_field(self):
        return STATUS_FIELD_MAP.get(self.module)

    def _source_field(self):
        return SOURCE_FIELD_MAP.get(self.module)

    def _district_field(self):
        return DISTRICT_FIELD_MAP.get(self.module)

    def execute(self):
        method = getattr(self, f'_agg_{self.aggregation}', self._agg_list)
        result = method()
        if self.config.show_chart != 'none' and self.chart_data:
            rendered = self._render_chart()
            if rendered:
                self.chart_data = rendered
        return result

    def _agg_list(self):
        qs = self._base_qs().order_by(f'-{self.date_field}')
        select_fields = {
            'entries': ('member', 'sponsor'),
        }
        s_fields = select_fields.get(self.module, ())
        if s_fields:
            qs = qs.select_related(*s_fields)
        self.rows = []
        for obj in qs[:500]:
            row = {}
            if self.module == 'entries':
                row = {'date': self._fmt(obj, 'entry_date'), 'headline': self._fmt(obj, 'headline'),
                       'member': self._fmt(obj, 'member'), 'sponsor': self._fmt(obj, 'sponsor'),
                       'slug': self._fmt(obj, 'slug')}
            elif self.module == 'sponsors':
                row = {'date': self._fmt(obj, 'start_date'), 'name': self._fmt(obj, 'name'),
                       'daily_quota': obj.daily_quota, 'total_quota': obj.total_quota,
                       'active': 'Active' if obj.is_active else 'Expired'}
            elif self.module == 'users':
                row = {'date': self._fmt(obj, 'date_joined'), 'username': obj.username,
                       'full_name': self._fmt(obj, 'full_name'), 'designation': self._fmt(obj, 'designation'),
                       'role': 'Admin' if obj.is_admin else 'User'}
            self.rows.append(row)
        self.summary = {'total': len(self.rows)}
        return self

    def _agg_count(self):
        total = self._base_qs().count()
        self.rows = [{'metric': 'Total', 'count': total}]
        self.summary = {'total': total}
        return self

    def _agg_status_breakdown(self):
        field = self._status_field()
        if not field:
            return self._agg_list()
        qs = self._base_qs().values(field).annotate(count=Count('id')).order_by('-count')
        self.rows = [{'status': item[field], 'count': item['count']} for item in qs]
        self.summary = {'total': sum(r['count'] for r in self.rows)}
        if self.config.show_chart != 'none':
            self.chart_data = {'labels': [r['status'] for r in self.rows],
                               'values': [r['count'] for r in self.rows]}
        return self

    def _agg_member_breakdown(self):
        field = self._member_field()
        if not field:
            return self._agg_list()
        qs = self._base_qs().values(field).annotate(count=Count('id')).order_by('-count')[:20]
        uids = [item[field] for item in qs if item[field]]
        name_map = {}
        if uids:
            for u in User.objects.filter(id__in=uids).only('id', 'username'):
                name_map[u.id] = u.username
        self.rows = []
        for item in qs:
            uid = item[field]
            uname = name_map.get(uid, 'Deleted') if uid else 'Unknown'
            self.rows.append({'member': uname, 'count': item['count']})
        self.summary = {'total': sum(r['count'] for r in self.rows)}
        if self.config.show_chart != 'none':
            self.chart_data = {'labels': [r['member'] for r in self.rows],
                               'values': [r['count'] for r in self.rows]}
        return self

    def _agg_source_breakdown(self):
        field = self._source_field()
        if not field:
            return self._agg_list()
        qs = self._base_qs().values(field).annotate(count=Count('id')).order_by('-count')
        self.rows = [{'source': item[field], 'count': item['count']} for item in qs]
        self.summary = {'total': sum(r['count'] for r in self.rows)}
        if self.config.show_chart != 'none':
            self.chart_data = {'labels': [r['source'] for r in self.rows],
                               'values': [r['count'] for r in self.rows]}
        return self

    def _agg_sponsor_breakdown(self):
        if self.module != 'entries':
            return self._agg_list()
        qs = self._base_qs().values('sponsor').annotate(count=Count('id')).order_by('-count')[:20]
        sids = [item['sponsor'] for item in qs if item['sponsor']]
        name_map = {}
        if sids:
            for s in Sponsor.objects.filter(id__in=sids).only('id', 'name'):
                name_map[s.id] = s.name
        self.rows = []
        for item in qs:
            sid = item['sponsor']
            sname = name_map.get(sid, 'Organic (No Sponsor)') if sid else 'Organic (No Sponsor)'
            self.rows.append({'sponsor': sname, 'count': item['count']})
        self.summary = {'total': sum(r['count'] for r in self.rows)}
        if self.config.show_chart != 'none':
            self.chart_data = {'labels': [r['sponsor'] for r in self.rows],
                               'values': [r['count'] for r in self.rows]}
        return self

    def _agg_daily_trend(self):
        qs = self._base_qs().annotate(
            day=TruncDay(self.date_field)
        ).values('day').annotate(count=Count('id')).order_by('day')
        self.rows = [{'date': item['day'].isoformat() if item['day'] else '', 'count': item['count']} for item in qs]
        self.summary = {'total': sum(r['count'] for r in self.rows), 'days': len(self.rows)}
        if self.config.show_chart != 'none':
            self.chart_data = {'labels': [r['date'] for r in self.rows],
                               'values': [r['count'] for r in self.rows]}
        return self

    def _agg_monthly_trend(self):
        qs = self._base_qs().annotate(
            month=TruncMonth(self.date_field)
        ).values('month').annotate(count=Count('id')).order_by('month')
        self.rows = [{'month': item['month'].strftime('%Y-%m') if item['month'] else '', 'count': item['count']} for item in qs]
        self.summary = {'total': sum(r['count'] for r in self.rows), 'months': len(self.rows)}
        if self.config.show_chart != 'none':
            self.chart_data = {'labels': [r['month'] for r in self.rows],
                               'values': [r['count'] for r in self.rows]}
        return self

    def _agg_district_breakdown(self):
        field = self._district_field()
        if not field:
            return self._agg_list()
        qs = self._base_qs().values(field).annotate(count=Count('id')).order_by('-count')[:30]
        self.rows = [{'district': item[field] or 'Unknown', 'count': item['count']} for item in qs]
        self.summary = {'total': sum(r['count'] for r in self.rows)}
        if self.config.show_chart != 'none':
            self.chart_data = {'labels': [r['district'] for r in self.rows],
                               'values': [r['count'] for r in self.rows]}
        return self

    CHART_COLORS = ['#8b5cf6', '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16']

    def _render_chart(self):
        labels = self.chart_data.get('labels', [])
        values = self.chart_data.get('values', [])
        if not labels or not values:
            return {}
        total = max(sum(values), 1)
        max_val = max(values)
        segments = []
        for i, (lbl, val) in enumerate(zip(labels, values)):
            pct = round(val / total * 100, 1) if total else 0
            segments.append({
                'label': lbl,
                'value': val,
                'pct': pct,
                'color': self.CHART_COLORS[i % len(self.CHART_COLORS)],
                'bar_height': round(val / max_val * 160, 1) if max_val else 0,
            })
        # Pre-computed bar chart polyline points for line chart
        line_points = []
        for i, seg in enumerate(segments):
            x = i * 100 + 50
            y = 160 - (seg['value'] / max_val * 140 if max_val else 0)
            line_points.append(f"{x},{y}")
        return {
            'segments': segments,
            'total': total,
            'max_val': max_val,
            'line_points': ' '.join(line_points),
        }

    def to_csv(self):
        output = io.StringIO()
        writer = csv.writer(output)
        if self.rows:
            writer.writerow(self.rows[0].keys())
            for row in self.rows:
                writer.writerow(row.values())
        return output.getvalue()
