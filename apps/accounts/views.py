import random
import uuid
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserSession
from .serializers import (
    RegisterSerializer, UserSerializer, UserSessionSerializer,
    LoginSerializer, PasswordResetRequestSerializer,
    PasswordResetVerifySerializer, PasswordResetConfirmSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = self._get_tokens(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)

    def _get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier']
        password = serializer.validated_data['password']

        user = None
        for field in ['username', 'email', 'office_id']:
            try:
                u = User.objects.get(**{field: identifier})
                if u.check_password(password):
                    user = u
                    break
            except User.DoesNotExist:
                continue

        if not user or not user.is_active:
            return Response(
                {'error': 'Incorrect information provided'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ip = self._get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')[:120]
        session_key = str(uuid.uuid4())
        refresh = RefreshToken.for_user(user)

        session = UserSession.objects.create(
            user=user,
            ip_address=ip,
            device_info=ua,
            session_key=session_key,
        )

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'session_id': str(session.id),
        })

    def _get_client_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')


class LogoutView(APIView):
    def post(self, request):
        session_id = request.data.get('session_id')
        if session_id:
            UserSession.objects.filter(
                id=session_id, user=request.user
            ).update(is_active=False)
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
                token = JWTRefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({'message': 'Logged out successfully'})


class UserListView(generics.ListAPIView):
    queryset = User.objects.filter(is_active=True).order_by('username')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class CurrentUserView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserSessionsView(generics.ListAPIView):
    serializer_class = UserSessionSerializer

    def get_queryset(self):
        return UserSession.objects.filter(
            user=self.request.user
        ).order_by('-login_at')


class AllSessionsView(generics.ListAPIView):
    queryset = UserSession.objects.all().order_by('-login_at')[:50]
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAdminUser]


class AdminResetPasswordView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        password = request.data.get('password', '')
        if len(password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(password)
        user.save()
        UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
        return Response({'message': f"Password reset for {user.username}"})


class ToggleAdminView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        if user.is_founder and str(user.id) != str(request.user.id):
            return Response(
                {'error': 'No one else can remove founder from admin'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.db import transaction
        with transaction.atomic():
            admins = User.objects.select_for_update().filter(is_admin=True)
            admin_count = admins.count()
            if not user.is_admin and admin_count >= 3:
                return Response(
                    {'error': 'Maximum 3 admins can be allowed'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.is_admin = not user.is_admin
            user.save(update_fields=['is_admin'])
        return Response({
            'is_admin': user.is_admin,
            'full_name': user.full_name,
        })


class RemoteLogoutView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, session_id):
        try:
            session = UserSession.objects.get(id=session_id)
            session.is_active = False
            session.save()
            return Response({'message': 'Session has been logged out'})
        except UserSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'password_reset'

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        user = User.objects.filter(
            username=d['identifier'],
            email=d['email'],
            phone=d['phone'],
        ).first()

        otp = str(random.randint(100000, 999999))
        otp_hash = make_password(otp)
        request.session['reset_otp_hash'] = otp_hash
        request.session['reset_user_id'] = str(user.id) if user else ''
        request.session['reset_created_at'] = timezone.now().timestamp()
        request.session['reset_attempts'] = 0

        if not user:
            return Response({'message': 'Verification code sent (if information is correct)'})

        return Response({
            'message': 'Verification code sent',
            'user': user.full_name,
        })

    def throttled(self, request, wait):
        return Response(
            {'error': 'Too many attempts. Try again in {:.0f} seconds.'.format(wait)},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class PasswordResetVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stored_hash = request.session.get('reset_otp_hash')
        created_at = request.session.get('reset_created_at', 0)
        attempts = request.session.get('reset_attempts', 0)
        now = timezone.now().timestamp()

        if not stored_hash or (now - created_at) > 600:
            request.session.flush()
            return Response(
                {'error': 'Code has expired. Try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if attempts >= 5:
            request.session.flush()
            return Response(
                {'error': 'Too many wrong attempts. Start the reset again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.session['reset_attempts'] = attempts + 1

        entered_otp = serializer.validated_data['otp']

        if not stored_hash.startswith('pbkdf2_') or not check_password(entered_otp, stored_hash):
            return Response(
                {'error': 'Code does not match'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.session['reset_verified'] = True
        return Response({'token': 'verified'})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.session.get('reset_user_id')
        created_at = request.session.get('reset_created_at', 0)
        verified = request.session.get('reset_verified', False)
        now = timezone.now().timestamp()

        if not user_id or not verified or (now - created_at) > 600:
            request.session.flush()
            return Response(
                {'error': 'Session has expired. Start the reset again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            request.session.flush()
            return Response({'error': 'User not found'}, status=404)

        user.set_password(serializer.validated_data['password'])
        user.save(update_fields=['password'])
        UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
        request.session.flush()
        return Response({'message': 'Password Reset'})
