from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from .models import Notification
import json


def _notification_response(request, template, ctx=None):
    ctx = ctx or {}
    ctx['user'] = request.user
    resp = render(request, template, ctx)
    return resp


@login_required
def notification_bell(request):
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    recent = Notification.objects.filter(recipient=request.user)[:10]
    return _notification_response(request, 'cms/notifications_dropdown.html', {
        'notifications': recent,
        'unread_count': unread_count,
    })


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(Notification, id=pk, recipient=request.user)
    notification.mark_read()
    resp = HttpResponse()
    resp['HX-Trigger'] = json.dumps({'notification-update': {}})
    if notification.link:
        resp['HX-Redirect'] = notification.link
    return resp


@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    unread_count = 0
    recent = Notification.objects.filter(recipient=request.user)[:10]
    resp = render(request, 'cms/notifications_dropdown.html', {
        'notifications': recent,
        'unread_count': unread_count,
        'user': request.user,
    })
    resp['HX-Trigger'] = json.dumps({'notification-update': {}})
    return resp


@login_required
def unread_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    html = str(count) if count > 0 else ''
    return render(request, 'cms/notification_badge.html', {'count': count, 'user': request.user})


@login_required
def unread_notice_count(request):
    count = Notification.objects.filter(recipient=request.user, notification_type='notice', is_read=False).count()
    return render(request, 'cms/notice_badge.html', {'count': count, 'user': request.user})


def create_notification(recipient, notification_type, title, message='', link='', created_by=None):
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link,
        created_by=created_by,
    )


def notify_admins(notification_type, title, message='', link='', exclude_user=None):
    from apps.accounts.models import User
    admins = User.objects.filter(is_admin=True, is_active=True)
    for admin in admins:
        if exclude_user and admin == exclude_user:
            continue
        create_notification(admin, notification_type, title, message, link)


def notify_all_users(notification_type, title, message='', link='', exclude_user=None):
    from apps.accounts.models import User
    users = User.objects.filter(is_active=True)
    for user in users:
        if exclude_user and user == exclude_user:
            continue
        create_notification(user, notification_type, title, message, link)


# ─── DRF Mobile API Views ───────────────────────────────────

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import NotificationSerializer, DeviceTokenSerializer
from .models import DeviceToken


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)[:50]


class NotificationMarkReadAPIView(generics.UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def perform_update(self, serializer):
        from django.utils import timezone
        serializer.save(is_read=True, read_at=timezone.now())


class NotificationMarkAllReadAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({'detail': 'সব নোটিফিকেশন পড়া হয়েছে'})


class DeviceTokenRegisterAPIView(generics.GenericAPIView):
    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        platform = serializer.validated_data['platform']
        DeviceToken.objects.update_or_create(
            token=token,
            defaults={'user': request.user, 'platform': platform, 'is_active': True},
        )
        return Response({'detail': 'টোকেন নিবন্ধিত হয়েছে'}, status=status.HTTP_201_CREATED)


class DeviceTokenUnregisterAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('token', '')
        if token:
            DeviceToken.objects.filter(user=request.user, token=token).update(is_active=False)
        return Response({'detail': 'টোকেন নিষ্ক্রিয় করা হয়েছে'})
