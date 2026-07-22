from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class ContentEntry(BaseModel):
    entry_date = models.DateField('The Date', db_index=True)
    entry_time = models.TimeField('Time')
    slug = models.CharField('Content Slug Name', max_length=255, db_index=True)
    headline = models.TextField('The Headline')
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='content_entries', verbose_name='Uploader',
        db_index=True,
    )
    links = models.JSONField('Links', default=dict, blank=True)
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='content_entries',
        verbose_name='Assignment',
    )
    sponsor = models.ForeignKey(
        'sponsors.Sponsor', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='content_entries',
        verbose_name='Sponsor',
    )
    comment = models.TextField('Comment', blank=True, default='')
    language = models.CharField(
        'The Language', max_length=5, choices=[('Bn', 'Bangla'), ('en', 'English')],
        default='bn', db_index=True,
    )

    class Meta:
        verbose_name = 'Content Entry'
        verbose_name_plural = 'Content Entries'
        constraints = [
            models.UniqueConstraint(fields=['slug', 'entry_date'], name='uq_content_slug_date'),
        ]
        indexes = [
            models.Index(fields=['entry_date']),
            models.Index(fields=['member', 'entry_date']),
            models.Index(fields=['-entry_date', '-entry_time']),
            models.Index(fields=['language']),
        ]

    def __str__(self):
        return f'{self.entry_date} - {self.headline[:60]}'
