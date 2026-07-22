from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_bell, name='notification-bell'),
    path('count/', views.unread_count, name='notification-count'),
    path('notice-count/', views.unread_notice_count, name='notification-notice-count'),
    path('<hexuuid:pk>/read/', views.mark_read, name='notification-mark-read'),
    path('read-all/', views.mark_all_read, name='notification-mark-all-read'),
    # DRF API
    path('api/', views.NotificationListAPIView.as_view(), name='api-notification-list'),
    path('api/read-all/', views.NotificationMarkAllReadAPIView.as_view(), name='api-notification-read-all'),
    path('api/<hexuuid:pk>/read/', views.NotificationMarkReadAPIView.as_view(), name='api-notification-mark-read'),
    path('api/devices/register/', views.DeviceTokenRegisterAPIView.as_view(), name='api-device-register'),
    path('api/devices/unregister/', views.DeviceTokenUnregisterAPIView.as_view(), name='api-device-unregister'),
]
