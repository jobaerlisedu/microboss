from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Script
from apps.notifications.models import Notification
from apps.accounts.models import User


@receiver(post_save, sender=Script)
def notify_script_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Script.objects.get(pk=instance.pk)
        if old.status == instance.status:
            return
    except Script.DoesNotExist:
        return

    if instance.status == 'pending':
        admins = User.objects.filter(is_admin=True, is_active=True)
        for admin in admins:
            if admin == instance.writer:
                continue
            Notification.objects.create(
                recipient=admin,
                notification_type='script_submit',
                title='নতুন স্ক্রিপ্ট জমা দেওয়া হয়েছে',
                message=f'{instance.writer.full_name or instance.writer.username} একটি স্ক্রিপ্ট জমা দিয়েছেন: {instance.headline[:100]}',
                link=f'/cms/scripts/{instance.id}/',
                created_by=instance.updated_by or instance.created_by,
            )

    elif instance.status == 'approved' and instance.writer:
        if instance.approved_by and instance.writer != instance.approved_by:
            Notification.objects.create(
                recipient=instance.writer,
                notification_type='script_approve',
                title='স্ক্রিপ্ট অনুমোদিত হয়েছে',
                message=f'আপনার স্ক্রিপ্ট "{instance.headline[:100]}" অনুমোদিত হয়েছে।',
                link=f'/cms/scripts/{instance.id}/',
                created_by=instance.approved_by,
            )
