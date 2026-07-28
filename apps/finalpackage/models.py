from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class FinalPackage(BaseModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('complete', 'Complete'),
        ('approved', 'Approved'),
    ]

    package_date = models.DateField('The Date', db_index=True)
    title = models.CharField('Title', max_length=255)
    producer = models.CharField('The Producer', max_length=255, blank=True, default='')
    editor = models.CharField('Editor', max_length=255, blank=True, default='')
    editor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='edited_packages',
        verbose_name='Editor (User)',
        db_index=True,
    )
    runtime = models.CharField('Length', max_length=20, blank=True, default='')
    file_link = models.URLField('File Link', max_length=500, blank=True, default='')
    video_link = models.URLField('Video Content Link', max_length=500, blank=True, default='')
    voice_link = models.URLField('Voice Recording Link', max_length=500, blank=True, default='')
    notes = models.TextField('Note', blank=True, default='')
    status = models.CharField(
        'Status', max_length=20,
        choices=STATUS_CHOICES, default='draft', db_index=True,
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='final_packages', verbose_name='Adder',
        db_index=True,
    )
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='final_packages',
        verbose_name='Assignment',
    )

    class Meta:
        verbose_name = 'The Final Package'
        verbose_name_plural = 'Final Packages'
        ordering = ['-package_date', '-created_at']
        indexes = [
            models.Index(fields=['package_date']),
            models.Index(fields=['status']),
            models.Index(fields=['-package_date', '-created_at']),
        ]

    def __str__(self):
        return f'{self.package_date} - {self.title[:60]}'
