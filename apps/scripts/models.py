import re
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel


class ScriptEditHistory(BaseModel):
    script = models.ForeignKey(
        'Script', on_delete=models.CASCADE,
        related_name='edit_history', verbose_name=_('স্ক্রিপ্ট'),
    )
    headline = models.CharField(_('সম্ভাব্য হেডলাইন'), max_length=255)
    body = models.TextField(_('স্ক্রিপ্ট'), blank=True, default='')
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='script_edits',
        verbose_name=_('সম্পাদক'),
    )
    change_summary = models.TextField(_('পরিবর্তনের সারাংশ'), blank=True, default='')

    class Meta:
        verbose_name = _('স্ক্রিপ্ট সম্পাদনা ইতিহাস')
        verbose_name_plural = _('স্ক্রিপ্ট সম্পাদনা ইতিহাসসমূহ')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.script.headline} - {self.created_at}'


class Script(BaseModel):
    STATUS_CHOICES = [
        ('draft', _('খসড়া')),
        ('pending', _('অনুমোদনের অপেক্ষায়')),
        ('approved', _('অনুমোদিত')),
    ]
    SOURCE_CHOICES = [
        ('district', _('জেলা')),
        ('reuters', _('রয়টার্স')),
        ('social', _('সোশ্যাল মিডিয়া')),
        ('studio', _('স্টুডিও শুটিং')),
    ]

    script_date = models.DateField(_('তারিখ'), db_index=True)
    headline = models.CharField(_('সম্ভাব্য হেডলাইন'), max_length=255)
    source = models.CharField(_('কন্টেন্ট সোর্স'), max_length=20, choices=SOURCE_CHOICES, db_index=True)
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='scripts', verbose_name=_('স্ক্রিপ্ট রাইটার'),
        db_index=True,
    )
    district = models.CharField(_('জেলার নাম'), max_length=100, blank=True, default='')
    district_reporter = models.CharField(
        _('জেলার রিপোর্টার'), max_length=255, blank=True, default='',
    )
    body = models.TextField(_('স্ক্রিপ্ট'), blank=True, default='')
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='scripts',
        verbose_name=_('এসাইনমেন্ট'),
    )
    status = models.CharField(
        _('স্ট্যাটাস'), max_length=20,
        choices=STATUS_CHOICES, default='draft', db_index=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_scripts',
        verbose_name=_('অনুমোদনকারী'),
    )
    approved_at = models.DateTimeField(
        _('অনুমোদনের সময়'), null=True, blank=True,
    )

    class Meta:
        verbose_name = _('ডিজিটাল স্ক্রিপ্ট')
        verbose_name_plural = _('ডিজিটাল স্ক্রিপ্টসমূহ')
        indexes = [
            models.Index(fields=['script_date']),
            models.Index(fields=['status']),
            models.Index(fields=['writer', 'status']),
            models.Index(fields=['-script_date', '-created_at']),
        ]

    def __str__(self):
        return f'{self.script_date} - {self.headline[:60]}'

    @property
    def filename(self):
        parts = [
            re.sub(r'\s+', '-', self.headline or ''),
            re.sub(r'\s+', '-', self.writer.username if self.writer else ''),
            self.get_source_display() if self.source else '',
            str(self.script_date),
        ]
        return '_'.join(filter(None, parts))
