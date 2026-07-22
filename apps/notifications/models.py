import uuid
from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class DeviceToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='device_tokens', db_index=True)
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')], default='android')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Device Token'
        verbose_name_plural = 'Device Token'
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user.username} ({self.platform})'


NOTIFICATION_TYPES = [
    ('Assignment', 'Assignment'),
    ('Script_Submit', 'Script Submit'),
    ('Script_Approve', 'Script Approval'),
    ('Script_Reject', 'Script Rejected'),
    ('Notice', 'Notice'),
    ('Registration', 'Registration'),
    ('Welcome', 'Swagtam'),
]


class Notification(BaseModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    notification_type = models.CharField('Type', max_length=30, choices=NOTIFICATION_TYPES, db_index=True)
    title = models.CharField('Title', max_length=255)
    message = models.TextField('The Message', blank=True)
    link = models.CharField('Link', max_length=500, blank=True)
    is_read = models.BooleanField('Has Been Read', default=False, db_index=True)
    read_at = models.DateTimeField('Reading Time', null=True, blank=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', '-created_at']),
        ]

    def __str__(self):
        return f'[{self.notification_type}] {self.title} → {self.recipient}'

    def mark_read(self):
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
