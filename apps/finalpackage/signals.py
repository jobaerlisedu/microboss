from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import FinalPackage
from apps.notifications.models import Notification


@receiver(post_save, sender=FinalPackage, dispatch_uid='notify_final_package_status')
def notify_final_package_status(sender, instance, created, **kwargs):
    if created and instance.member:
        Notification.objects.create(
            recipient=instance.member,
            notification_type='Assignment',
            title='Final Package Created',
            message=f'Package "{instance.title[:100]}" has been created.',
            link=reverse('cms:cms-final-packages'),
            created_by=instance.created_by,
        )
    elif instance.status == 'approved' and instance.assignment and instance.assignment.reporter_user:
        Notification.objects.create(
            recipient=instance.assignment.reporter_user,
            notification_type='Assignment',
            title='Final Package Approved',
            message=f'Package "{instance.title[:100]}" for your assignment has been approved.',
            link=reverse('cms:cms-final-packages'),
            created_by=instance.updated_by or instance.created_by,
        )
