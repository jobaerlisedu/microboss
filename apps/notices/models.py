from django.db import models
from apps.common.models import BaseModel


class Notice(BaseModel):
    title = models.CharField('Title', max_length=255, db_index=True)
    content = models.TextField('Details')
    is_active = models.BooleanField('Active', default=True, db_index=True)

    class Meta:
        verbose_name = 'Notice'
        verbose_name_plural = 'Notices'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return self.title
