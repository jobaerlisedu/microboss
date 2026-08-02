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
        ordering = ['-entry_date', '-entry_time']
        indexes = [
            models.Index(fields=['entry_date']),
            models.Index(fields=['member', 'entry_date']),
            models.Index(fields=['-entry_date', '-entry_time']),
            models.Index(fields=['language']),
        ]

    def save(self, *args, **kwargs):
        if self.links is None:
            self.links = {}
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.entry_date} - {self.headline[:60]}'


class ContentDeletion(models.Model):
    content_entry = models.ForeignKey(
        ContentEntry, on_delete=models.CASCADE,
        related_name='deletion_records', verbose_name='Content Entry',
    )
    platforms = models.CharField('Platform(s)', max_length=255, blank=True, default='')
    deleted_at = models.DateTimeField('Deleted At', db_index=True)
    instructed_by = models.CharField('Instructed By', max_length=255, blank=True, default='')
    reason = models.TextField('Reason', blank=True, default='')
    notes = models.TextField('Notes', blank=True, default='')
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='recorded_deletions',
        verbose_name='Recorded By',
    )
    created_at = models.DateTimeField('Created At', auto_now_add=True)

    class Meta:
        verbose_name = 'Content Deletion'
        verbose_name_plural = 'Content Deletions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.content_entry} - {self.platforms}'
