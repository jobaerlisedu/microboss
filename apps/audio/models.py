from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel


class AudioItem(BaseModel):
    SOURCE_CHOICES = [
        ('district', _('জেলা')),
        ('reuters', _('রয়টার্স')),
        ('social', _('সোশ্যাল মিডিয়া')),
        ('studio', _('স্টুডিও শুটিং')),
    ]

    audio_date = models.DateField(_('তারিখ'), db_index=True)
    title = models.CharField(_('শিরোনাম'), max_length=255)
    source = models.CharField(_('সোর্স'), max_length=20, choices=SOURCE_CHOICES, db_index=True)
    district = models.CharField(_('জেলা'), max_length=100, blank=True, default='')
    duration = models.CharField(_('সময়কাল'), max_length=20, blank=True, default='')
    file_link = models.URLField(_('ফাইল লিংক'), max_length=500, blank=True, default='')
    voice_over = models.CharField(_('ভয়েস ওভার'), max_length=255, blank=True, default='')
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='audio_items', verbose_name=_('যোগকারী'),
        db_index=True,
    )
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='audio_items',
        verbose_name=_('এসাইনমেন্ট'),
    )

    class Meta:
        verbose_name = _('অডিও')
        verbose_name_plural = _('অডিওসমূহ')
        indexes = [
            models.Index(fields=['audio_date']),
            models.Index(fields=['source']),
            models.Index(fields=['-audio_date', '-created_at']),
        ]

    def __str__(self):
        return f'{self.audio_date} - {self.title[:60]}'
