from rest_framework import serializers
from .models import Notification, DeviceToken


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'link', 'is_read', 'created_at', 'read_at']


class DeviceTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    platform = serializers.ChoiceField(choices=['android', 'ios', 'web'])

    def validate_token(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError('Invalid device token')
        return value
