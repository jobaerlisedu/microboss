from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class AudioItem(BaseModel):
    SOURCE_CHOICES = [
        ('District', 'District'),
        ('Reuters', 'Reuters'),
        ('Social', 'Social Media'),
        ('Studio', 'Studio Shooting'),
    ]

    audio_date = models.DateField('The Date', db_index=True)
    title = models.CharField('Title', max_length=255)
    source = models.CharField('Source', max_length=20, choices=SOURCE_CHOICES, db_index=True)
    district = models.CharField('District', max_length=100, blank=True, default='')
    duration = models.CharField('Duration', max_length=20, blank=True, default='')
    file_link = models.URLField('File Link', max_length=500, blank=True, default='')
    voice_over = models.CharField('Voice Over', max_length=255, blank=True, default='')
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='audio_items', verbose_name='Adder',
        db_index=True,
    )
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='audio_items',
        verbose_name='Assignment',
    )

    class Meta:
        verbose_name = 'Audio'
        verbose_name_plural = 'Audios'
        indexes = [
            models.Index(fields=['audio_date']),
            models.Index(fields=['source']),
            models.Index(fields=['-audio_date', '-created_at']),
        ]

    def __str__(self):
        return f'{self.audio_date} - {self.title[:60]}'
