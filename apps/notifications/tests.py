from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from django.db.models.signals import post_save
from apps.notifications.models import Notification
from apps.notifications.signals import push_on_notification

User = get_user_model()


class PushNotificationSignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notifuser', password='test1234',
            full_name='Notif User', office_id='NTF001',
            designation='User', phone='01711111111',
            blood_group='O+',
        )

    def test_signal_connected(self):
        live, dead = post_save._live_receivers(Notification)
        self.assertEqual(len(live), 1)
        self.assertEqual(len(dead), 0)

    @patch('apps.notifications.signals.send_push')
    def test_signal_not_called_when_fcm_disabled(self, mock_send):
        with self.settings(FCM_DISABLED=True):
            Notification.objects.create(
                recipient=self.user,
                notification_type='notice',
                title='Test',
                message='Hello',
            )
        mock_send.assert_not_called()

    @patch('apps.notifications.signals.send_push')
    def test_signal_called_on_create(self, mock_send):
        with self.settings(FCM_DISABLED=False):
            notif = Notification.objects.create(
                recipient=self.user,
                notification_type='welcome',
                title='Welcome!',
                message='You are registered.',
                created_by=self.user,
            )
        mock_send.assert_called_once()
        args, kwargs = mock_send.call_args
        self.assertEqual(kwargs['user'], self.user)
        self.assertEqual(kwargs['title'], 'Welcome!')
        self.assertEqual(kwargs['data']['id'], str(notif.id))

    @patch('apps.notifications.signals.send_push')
    def test_signal_not_called_on_update(self, mock_send):
        with self.settings(FCM_DISABLED=False):
            notif = Notification.objects.create(
                recipient=self.user,
                notification_type='notice',
                title='Test',
                message='Hello',
            )
            mock_send.assert_called_once()
            mock_send.reset_mock()
            notif.message = 'Updated'
            notif.save()
        mock_send.assert_not_called()
