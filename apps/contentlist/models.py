from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class ContentListItem(BaseModel):
    SOURCE_CHOICES = [
        ('District', 'District'),
        ('Reuters', 'Reuters'),
        ('Social', 'Social Media'),
        ('Studio', 'Studio Shooting'),
    ]
    FOOTAGE_CHOICES = [
        ('FTP', 'FTP'), ('WhatsApp', 'WhatsApp'), ('Gmail', 'Gmail'),
        ('Google Drive', 'Google Drive'), ('Ingest', 'Ingest'),
        ('Card', 'Card'), ('Studio shoot', 'Studio shoot'),
    ]

    list_date = models.DateField('The Date', db_index=True)
    content = models.TextField('Content')
    source = models.CharField('Source', max_length=20, choices=SOURCE_CHOICES, db_index=True)
    district = models.CharField('District', max_length=100, blank=True, default='')
    footage_source = models.CharField(
        'Footage', max_length=50, choices=FOOTAGE_CHOICES,
        blank=True, default='',
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='content_list_items', verbose_name='Adder',
        db_index=True,
    )
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='content_list_items',
        verbose_name='Assignment',
    )

    class Meta:
        verbose_name = 'Content Source'
        verbose_name_plural = 'Content Sources'
        indexes = [
            models.Index(fields=['list_date']),
            models.Index(fields=['source']),
            models.Index(fields=['-list_date', '-created_at']),
        ]

    def __str__(self):
        return f'{self.list_date} - {self.content[:60]}'
