from django.db import models
from apps.common.models import BaseModel


class Notice(BaseModel):
    title = models.CharField('শিরোনাম', max_length=255, db_index=True)
    content = models.TextField('বিবরণ')
    is_active = models.BooleanField('সক্রিয়', default=True, db_index=True)

    class Meta:
        verbose_name = 'নোটিশ'
        verbose_name_plural = 'নোটিশ'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return self.title
