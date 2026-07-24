from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.common.models import BaseModel


class Assignment(BaseModel):
    STATUS_CHOICES = [
        ('Assigned', 'Assigned'),
        ('Processing', 'Processing'),
        ('Done', 'Done'),
        ('Cancel', 'Cancel'),
    ]

    assign_date = models.DateField('The Date', db_index=True)
    caption = models.TextField('Content Caption')
    source_link = models.URLField('Source Link', max_length=500, blank=True, default='')
    district = models.CharField('District', max_length=100, blank=True, default='')
    reporter = models.CharField('Reporter Name', max_length=255, db_index=True)
    reporter_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_assignments',
        verbose_name='Reporter (User)',
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=STATUS_CHOICES, default='Assigned', db_index=True,
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='assignments', verbose_name='Assignor',
        db_index=True,
    )

    class Meta:
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
        ordering = ['-assign_date', '-created_at']
        indexes = [
            models.Index(fields=['assign_date']),
            models.Index(fields=['status']),
            models.Index(fields=['reporter']),
            models.Index(fields=['-assign_date', '-created_at']),
        ]

    def clean(self):
        if self.assign_date and self.assign_date > timezone.now().date():
            raise ValidationError({'assign_date': 'Assign date cannot be in the future.'})

    def __str__(self):
        return f'{self.assign_date} - {self.reporter} - {self.status}'
