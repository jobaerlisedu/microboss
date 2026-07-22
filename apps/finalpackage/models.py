from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel


class FinalPackage(BaseModel):
    STATUS_CHOICES = [
        ('draft', _('খসড়া')),
        ('complete', _('সম্পূর্ণ')),
        ('approved', _('অনুমোদিত')),
    ]

    package_date = models.DateField(_('তারিখ'), db_index=True)
    title = models.CharField(_('শিরোনাম'), max_length=255)
    producer = models.CharField(_('প্রযোজক'), max_length=255, blank=True, default='')
    editor = models.CharField(_('সম্পাদক'), max_length=255, blank=True, default='')
    runtime = models.CharField(_('দৈর্ঘ্য'), max_length=20, blank=True, default='')
    file_link = models.URLField(_('ফাইল লিংক'), max_length=500, blank=True, default='')
    notes = models.TextField(_('নোট'), blank=True, default='')
    status = models.CharField(
        _('স্ট্যাটাস'), max_length=20,
        choices=STATUS_CHOICES, default='draft', db_index=True,
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='final_packages', verbose_name=_('যোগকারী'),
        db_index=True,
    )
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='final_packages',
        verbose_name=_('এসাইনমেন্ট'),
    )

    class Meta:
        verbose_name = _('ফাইনাল প্যাকেজ')
        verbose_name_plural = _('ফাইনাল প্যাকেজসমূহ')
        indexes = [
            models.Index(fields=['package_date']),
            models.Index(fields=['status']),
            models.Index(fields=['-package_date', '-created_at']),
        ]

    def __str__(self):
        return f'{self.package_date} - {self.title[:60]}'
