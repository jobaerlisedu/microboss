from datetime import date
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel


class Sponsor(BaseModel):
    name = models.CharField(_('স্পন্সরের নাম'), max_length=255, unique=True)
    daily_quota = models.IntegerField(_('প্রতিদিন কয়টা'))
    total_quota = models.IntegerField(_('মোট কয়টা'))
    start_date = models.DateField(_('শুরুর তারিখ'), db_index=True)
    end_date = models.DateField(_('শেষ তারিখ'), db_index=True)
    content_type = models.CharField(_('কন্টেন্ট টাইপ'), max_length=255, blank=True, default='')
    has_doggy = models.BooleanField(_('ডগি (FT)'), default=False)
    has_popup = models.BooleanField(_('পপআপ x2'), default=False)
    has_tvc = models.BooleanField(_('টিভিসি x1'), default=False)
    has_gpi = models.BooleanField(_('জিপিআই x1'), default=False)

    class Meta:
        verbose_name = _('স্পন্সর')
        verbose_name_plural = _('স্পন্সরগণ')
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
