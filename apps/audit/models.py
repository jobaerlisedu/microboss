import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    username = models.CharField(max_length=150, blank=True, db_index=True)
    action = models.CharField(max_length=20, db_index=True)
    content_type = models.CharField(max_length=100, db_index=True)
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['action', 'created_at']),
        ]

    def __str__(self):
        return f'[{self.action}] {self.content_type}#{self.object_id} by {self.username}'
