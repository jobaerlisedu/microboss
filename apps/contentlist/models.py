from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel


class ContentListItem(BaseModel):
    SOURCE_CHOICES = [
        ('district', _('জেলা')),
        ('reuters', _('রয়টার্স')),
        ('social', _('সোশ্যাল মিডিয়া')),
        ('studio', _('স্টুডিও শুটিং')),
    ]
    FOOTAGE_CHOICES = [
        ('FTP', 'FTP'), ('WhatsApp', 'WhatsApp'), ('Gmail', 'Gmail'),
        ('Google Drive', 'Google Drive'), ('Ingest', 'Ingest'),
        ('Card', 'Card'), ('Studio shoot', 'Studio shoot'),
    ]

    list_date = models.DateField(_('তারিখ'), db_index=True)
    content = models.TextField(_('কন্টেন্ট'))
    source = models.CharField(_('সোর্স'), max_length=20, choices=SOURCE_CHOICES, db_index=True)
    district = models.CharField(_('জেলা'), max_length=100, blank=True, default='')
    footage_source = models.CharField(
        _('ফুটেজ'), max_length=50, choices=FOOTAGE_CHOICES,
        blank=True, default='',
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='content_list_items', verbose_name=_('যোগকারী'),
        db_index=True,
    )
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='content_list_items',
        verbose_name=_('এসাইনমেন্ট'),
    )

    class Meta:
        verbose_name = _('কন্টেন্ট তালিকা')
        verbose_name_plural = _('কন্টেন্ট তালিকাসমূহ')
        indexes = [
            models.Index(fields=['list_date']),
            models.Index(fields=['source']),
            models.Index(fields=['-list_date', '-created_at']),
        ]

    def __str__(self):
        return f'{self.list_date} - {self.content[:60]}'
