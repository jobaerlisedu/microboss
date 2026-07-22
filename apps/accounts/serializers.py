from rest_framework import serializers
from .models import User, UserSession


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            'username', 'full_name', 'office_id', 'designation',
            'email', 'phone', 'blood_group', 'date_of_birth',
            'facebook_id', 'password', 'password2',
        )

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': 'The two passwords do not match'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        from django.db import transaction
        with transaction.atomic():
            is_first = User.objects.select_for_update().filter(is_founder=True).count() == 0
            user = User.objects.create_user(
                **validated_data,
                password=password,
                is_admin=is_first,
                is_founder=is_first,
            )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'office_id', 'designation',
            'email', 'phone', 'blood_group', 'date_of_birth',
            'facebook_id', 'is_admin', 'is_founder', 'is_active',
        )
        read_only_fields = ('id', 'is_admin', 'is_founder', 'is_active')


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ('id', 'user', 'ip_address', 'device_info', 'login_at', 'is_active')
        read_only_fields = ('id', 'login_at')


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()


class PasswordResetVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8)
    password2 = serializers.CharField(min_length=8)

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password2': 'The two passwords do not match'})
        return attrs
