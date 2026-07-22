import re
from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class ScriptEditHistory(BaseModel):
    script = models.ForeignKey(
        'Script', on_delete=models.CASCADE,
        related_name='edit_history', verbose_name='Script',
    )
    headline = models.CharField('Possible Headlines', max_length=255)
    body = models.TextField('Script', blank=True, default='')
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='script_edits',
        verbose_name='Editor',
    )
    change_summary = models.TextField('Summary Of Changes', blank=True, default='')

    class Meta:
        verbose_name = 'Script Edit History'
        verbose_name_plural = 'Script Edit Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.script.headline} - {self.created_at}'


class Script(BaseModel):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Awaiting Approval'),
        ('Approved', 'Approved'),
    ]
    SOURCE_CHOICES = [
        ('District', 'District'),
        ('Reuters', 'Reuters'),
        ('Social', 'Social Media'),
        ('Studio', 'Studio Shooting'),
    ]

    script_date = models.DateField('The Date', db_index=True)
    headline = models.CharField('Possible Headlines', max_length=255)
    source = models.CharField('Content Source', max_length=20, choices=SOURCE_CHOICES, db_index=True)
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='scripts', verbose_name='Script Writer',
        db_index=True,
    )
    district = models.CharField('District Name', max_length=100, blank=True, default='', db_index=True)
    district_reporter = models.CharField(
        'District Reporter', max_length=255, blank=True, default='',
    )
    body = models.TextField('Script', blank=True, default='')
    assignment = models.ForeignKey(
        'assignments.Assignment', on_delete=models.SET_NULL,
        null=True, blank=True, db_index=True, related_name='scripts',
        verbose_name='Assignment',
    )
    status = models.CharField(
        'Status', max_length=20,
        choices=STATUS_CHOICES, default='draft', db_index=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_scripts',
        verbose_name='Approver',
    )
    approved_at = models.DateTimeField(
        'Approval Time', null=True, blank=True,
    )

    class Meta:
        verbose_name = 'Digital Script'
        verbose_name_plural = 'Digital Scripts'
        indexes = [
            models.Index(fields=['script_date']),
            models.Index(fields=['status']),
            models.Index(fields=['writer', 'status']),
            models.Index(fields=['-script_date', '-created_at']),
        ]

    def __str__(self):
        return f'{self.script_date} - {self.headline[:60]}'

    @property
    def filename(self):
        parts = [
            re.sub(r'\s+', '-', self.headline or ''),
            re.sub(r'\s+', '-', self.writer.username if self.writer else ''),
            self.get_source_display() if self.source else '',
            str(self.script_date),
        ]
        return '_'.join(filter(None, parts))
