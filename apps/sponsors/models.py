from datetime import date
from django.db import models
from django.utils.functional import cached_property
from apps.common.models import BaseModel


class Sponsor(BaseModel):
    name = models.CharField("Sponsor's Name", max_length=255, unique=True)
    daily_quota = models.IntegerField('how many per day')
    total_quota = models.IntegerField('how many in total')
    start_date = models.DateField('Start Date', db_index=True)
    end_date = models.DateField('Last Date', db_index=True)
    content_type = models.CharField('Content Type', max_length=255, blank=True, default='')
    has_doggy = models.BooleanField('Dougie (Ft)', default=False, db_index=True)
    has_popup = models.BooleanField('Popup X2', default=False, db_index=True)
    has_tvc = models.BooleanField('Tvc X1', default=False, db_index=True)
    has_gpi = models.BooleanField('Gpi X1', default=False, db_index=True)

    class Meta:
        verbose_name = 'Sponsor'
        verbose_name_plural = 'Sponsors'
        ordering = ['name']
        indexes = [
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        today = date.today()
        return self.start_date <= today <= self.end_date

    @cached_property
    def _cached_counts(self):
        today = date.today()
        total = self.content_entries.filter(deleted_at__isnull=True).count()
        today_c = self.content_entries.filter(deleted_at__isnull=True, entry_date=today).count()
        return {'given_count': total, 'today_given': today_c}

    @cached_property
    def given_count(self):
        return self._cached_counts['given_count']

    @cached_property
    def today_given(self):
        return self._cached_counts['today_given']

    @cached_property
    def remaining_count(self):
        return max(0, self.total_quota - self.given_count)

    @cached_property
    def today_remaining(self):
        return max(0, self.daily_quota - self.today_given)

    @cached_property
    def progress_pct(self):
        if self.total_quota == 0:
            return 100
        return min(100, round(self.given_count / self.total_quota * 100))
