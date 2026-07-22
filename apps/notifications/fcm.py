import logging
from django.conf import settings
from .models import DeviceToken

logger = logging.getLogger(__name__)

try:
    from firebase_admin import initialize_app, credentials, messaging
    _initialized = False

    def _get_app():
        global _initialized
        if not _initialized:
            cred = None
            firebase_creds = getattr(settings, 'FIREBASE_CREDENTIALS', None)
            if firebase_creds:
                cred = credentials.Certificate(firebase_creds)
            initialize_app(cred)
            _initialized = True

    def send_push(user, title, body, data=None, badge=None):
        tokens = DeviceToken.objects.filter(user=user, is_active=True).values_list('token', flat=True)
        if not tokens:
            logger.info(f'No device tokens for user {user.username}')
            return 0
        _get_app()
        message = messaging.MulticastMessage(
            tokens=list(tokens),
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='content_tracker',
                    default_sound=True,
                    priority='high',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(title=title, body=body),
                        badge=badge,
                        sound='default',
                    ),
                ),
            ),
        )
        try:
            response = messaging.send_each_for_multicast(message)
            sent = response.success_count
            if response.failure_count > 0:
                _cleanup_invalid_tokens(user, response.responses, tokens)
            logger.info(f'Push sent: {sent}/{len(tokens)} to {user.username}')
            return sent
        except Exception as e:
            logger.error(f'Push failed for {user.username}: {e}')
            return 0

    def send_push_all(title, body, data=None, exclude_user=None):
        from apps.accounts.models import User
        qs = User.objects.filter(is_active=True)
        if exclude_user:
            qs = qs.exclude(id=exclude_user.id)
        total = 0
        for user in qs:
            total += send_push(user, title, body, data)
        return total

    def _cleanup_invalid_tokens(user, responses, tokens):
        inactive = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception) or (hasattr(resp, 'exception') and resp.exception):
                inactive.append(tokens[i])
        if inactive:
            DeviceToken.objects.filter(user=user, token__in=inactive).update(is_active=False)

except ImportError:
    logger.warning('firebase-admin not installed. Push notifications disabled.')

    def send_push(user, title, body, data=None, badge=None):
        logger.info(f'[mock] push to {user.username}: {title}')
        return 0

    def send_push_all(title, body, data=None, exclude_user=None):
        logger.info(f'[mock] push to all: {title}')
        return 0
