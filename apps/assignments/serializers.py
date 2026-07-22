from django.utils import timezone
from rest_framework import serializers
from .models import Assignment


class AssignmentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.username', read_only=True)
    reporter_user_name = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            'id', 'assign_date', 'caption', 'source_link', 'district',
            'reporter', 'reporter_user', 'status', 'member',
            'member_name', 'reporter_user_name',
            'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at',
        ]
        read_only_fields = (
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted_at',
        )

    def get_reporter_user_name(self, obj):
        return obj.reporter_user.full_name if obj.reporter_user else ''

    def validate_assign_date(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError('Assign date cannot be in the future.')
        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
