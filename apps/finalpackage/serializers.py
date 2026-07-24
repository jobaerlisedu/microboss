from rest_framework import serializers
from .models import FinalPackage


class FinalPackageSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.username', read_only=True)
    editor_name = serializers.SerializerMethodField()

    class Meta:
        model = FinalPackage
        fields = (
            'id', 'package_date', 'title', 'producer', 'editor', 'editor_user',
            'editor_name', 'runtime', 'file_link', 'video_link', 'voice_link',
            'notes', 'status', 'member', 'member_name', 'assignment',
            'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at',
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted_at',
        )

    def get_editor_name(self, obj):
        if obj.editor_user:
            return obj.editor_user.full_name or obj.editor_user.username
        return obj.editor or ''

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
