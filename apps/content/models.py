from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel


class ContentEntry(BaseModel):
    entry_date = models.DateField(_('তারিখ'), db_index=True)
    entry_time = models.TimeField(_('টাইম'))
    slug = models.CharField(_('কন্টেন্ট স্লাগ নেম'), max_length=255, db_index=True)
    headline = models.TextField(_('হেডলাইন'))
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='content_entries', verbose_name=_('আপলোডকারী'),
        db_index=True,
    )
    links = models.JSONField(_('লিংকসমূহ'), default=dict, blank=True)
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='content_entries',
        verbose_name=_('এসাইনমেন্ট'),
    )
    sponsor = models.ForeignKey(
        'sponsors.Sponsor', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='content_entries',
        verbose_name=_('স্পন্সর'),
    )
    comment = models.TextField(_('মন্তব্য'), blank=True, default='')

    class Meta:
        verbose_name = _('কন্টেন্ট এন্ট্রি')
        verbose_name_plural = _('কন্টেন্ট এন্ট্রিসমূহ')
        constraints = [
            models.UniqueConstraint(fields=['slug', 'entry_date'], name='uq_content_slug_date'),
        ]
        indexes = [
            models.Index(fields=['entry_date']),
            models.Index(fields=['member', 'entry_date']),
            models.Index(fields=['-entry_date', '-entry_time']),
        ]

    def __str__(self):
        return f'{self.entry_date} - {self.headline[:60]}'
