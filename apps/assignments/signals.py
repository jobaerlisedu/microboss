from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import Assignment
from apps.notifications.models import Notification


@receiver(post_save, sender=Assignment)
def notify_assignment_reporter(sender, instance, created, **kwargs):
    if created and instance.reporter_user and instance.reporter_user != instance.member:
        Notification.objects.create(
            recipient=instance.reporter_user,
            notification_type='assignment',
            title='নতুন এসাইনমেন্ট',
            message=instance.caption[:200],
            link=reverse('cms:cms-assignments'),
            created_by=instance.created_by,
            updated_by=instance.created_by,
        )
