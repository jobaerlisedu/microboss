import uuid
from django.db import models
from django.conf import settings


class ReportConfig(models.Model):
    MODULE_CHOICES = [
        ('entries', 'Content Entries'),
        ('sponsors', 'Sponsors'),
        ('users', 'Users'),
    ]
    AGGREGATION_CHOICES = [
        ('list', 'Detailed List'),
        ('count', 'Total Count'),
        ('status_breakdown', 'Status Breakdown'),
        ('member_breakdown', 'By Member'),
        ('source_breakdown', 'By Source'),
        ('sponsor_breakdown', 'By Sponsor'),
        ('daily_trend', 'Daily Trend'),
        ('monthly_trend', 'Monthly Trend'),
        ('district_breakdown', 'By District'),
    ]
    PERIOD_CHOICES = [
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('this_year', 'This Year'),
        ('custom', 'Custom Range'),
    ]
    CHART_CHOICES = [
        ('none', 'No Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('line', 'Line Chart'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    module = models.CharField(max_length=30, choices=MODULE_CHOICES)
    aggregation = models.CharField(max_length=30, choices=AGGREGATION_CHOICES, default='list')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='this_month')
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True, help_text='Extra filters as JSON')
    show_chart = models.CharField(max_length=10, choices=CHART_CHOICES, default='none')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='report_configs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'report_config'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name
