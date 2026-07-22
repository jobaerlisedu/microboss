import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        _('ডাকনাম'), max_length=150, unique=True,
        help_text=_('লগইনের জন্য ব্যবহার করা হবে'),
    )
    full_name = models.CharField(_('পূর্ণ নাম'), max_length=255)
    office_id = models.CharField(_('অফিস আইডি'), max_length=100, unique=True)
    designation = models.CharField(_('ডেজিগনেশন'), max_length=255)
    phone = models.CharField(_('ফোন'), max_length=20, db_index=True)
    blood_group = models.CharField(
        _('ব্লাড গ্রুপ'), max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
        ],
    )
    date_of_birth = models.DateField(_('জন্ম তারিখ'), null=True, blank=True)
    facebook_id = models.CharField(_('ফেসবুক আইডি'), max_length=500, blank=True, default='')
    is_admin = models.BooleanField(_('অ্যাডমিন'), default=False, db_index=True)
    is_founder = models.BooleanField(_('প্রতিষ্ঠাতা'), default=False)
    pending_approval = models.BooleanField(_('অনুমোদন বিহীন'), default=False, db_index=True)

    class Meta:
        verbose_name = _('ব্যবহারকারী')
        verbose_name_plural = _('ব্যবহারকারীগণ')
        indexes = [
            models.Index(fields=['office_id']),
            models.Index(fields=['phone']),
            models.Index(fields=['is_active', 'is_admin']),
        ]

    def __str__(self):
        return f'{self.full_name} ({self.username})'


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions', db_index=True)
    ip_address = models.CharField(max_length=45, db_index=True)
    device_info = models.CharField(max_length=255, blank=True, default='')
    login_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, db_index=True)
    session_key = models.CharField(max_length=40, unique=True)

    class Meta:
        verbose_name = _('সেশন')
        verbose_name_plural = _('সেশনসমূহ')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['-login_at']),
        ]

    def __str__(self):
        return f'{self.user.username} @ {self.ip_address}'


class SiteConfig(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, default='')
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'সাইট কনফিগারেশন'
        verbose_name_plural = 'সাইট কনফিগারেশন'

    def __str__(self):
        return f'{self.key} = {self.value}'
