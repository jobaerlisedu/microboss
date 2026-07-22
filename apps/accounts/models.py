import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        'Nickname', max_length=150, unique=True,
        help_text='will be used for login',
    )
    full_name = models.CharField('Full Name', max_length=255)
    office_id = models.CharField('Office Id', max_length=100, unique=True)
    designation = models.CharField('Designation', max_length=255)
    phone = models.CharField('The Phone', max_length=20, db_index=True)
    blood_group = models.CharField(
        'Blood Group', max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
        ],
    )
    date_of_birth = models.DateField('Date Of Birth', null=True, blank=True)
    facebook_id = models.CharField('Facebook Id', max_length=500, blank=True, default='')
    is_admin = models.BooleanField('Admin', default=False, db_index=True)
    is_founder = models.BooleanField('The Founder', default=False)
    pending_approval = models.BooleanField('Unauthorized', default=False, db_index=True)

    class Meta:
        verbose_name = 'The User'
        verbose_name_plural = 'Users'
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
        verbose_name = 'Session'
        verbose_name_plural = 'Sessions'
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
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configuration'

    def __str__(self):
        return f'{self.key} = {self.value}'
