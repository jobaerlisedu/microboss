from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class AudioItem(BaseModel):
    MEDIA_TYPE_CHOICES = [
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('graphic', 'Graphic'),
        ('document', 'Document'),
    ]

    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='audio_items',
        verbose_name='Assignment',
    )
    media_entries = models.JSONField('Media Entries', default=list, blank=True)
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='audio_items', verbose_name='Adder',
        db_index=True,
    )

    class Meta:
        verbose_name = 'Media Pool'
        verbose_name_plural = 'Media Pools'
        ordering = ['-created_at']

    def __str__(self):
        count = len(self.media_entries) if self.media_entries else 0
        assign = self.assignment.caption[:40] if self.assignment else 'No Assignment'
        return f'{assign} ({count} media)'
