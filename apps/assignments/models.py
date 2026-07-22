from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.common.models import BaseModel


class Assignment(BaseModel):
    STATUS_CHOICES = [
        ('Assigned', _('Assigned')),
        ('Processing', _('Processing')),
        ('Done', _('Done')),
        ('Cancel', _('Cancel')),
    ]

    assign_date = models.DateField(_('তারিখ'), db_index=True)
    caption = models.TextField(_('কন্টেন্ট ক্যাপশন'))
    source_link = models.URLField(_('সোর্স লিংক'), max_length=500, blank=True, default='')
    district = models.CharField(_('জেলা'), max_length=100, blank=True, default='')
    reporter = models.CharField(_('রিপোর্টারের নাম'), max_length=255, db_index=True)
    reporter_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_assignments',
        verbose_name=_('রিপোর্টার (ব্যবহারকারী)'),
    )
    status = models.CharField(
        _('স্ট্যাটাস'), max_length=20,
        choices=STATUS_CHOICES, default='Assigned', db_index=True,
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='assignments', verbose_name=_('এসাইনকারী'),
        db_index=True,
    )

    class Meta:
        verbose_name = _('এসাইনমেন্ট')
        verbose_name_plural = _('এসাইনমেন্টসমূহ')
        ordering = ['-assign_date', '-created_at']
        indexes = [
            models.Index(fields=['assign_date']),
            models.Index(fields=['status']),
            models.Index(fields=['reporter']),
            models.Index(fields=['-assign_date', '-created_at']),
        ]

    def clean(self):
        if self.assign_date and self.assign_date > timezone.now().date():
            raise ValidationError({'assign_date': _('Assign date cannot be in the future.')})

    def __str__(self):
        return f'{self.assign_date} - {self.reporter} - {self.status}'
