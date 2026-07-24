from rest_framework import serializers
from .models import Script


class ScriptSerializer(serializers.ModelSerializer):
    writer_name = serializers.CharField(source='writer.username', read_only=True)
    approved_by_name = serializers.CharField(
        source='approved_by.username', read_only=True, allow_null=True,
    )
    filename = serializers.CharField(read_only=True)

    class Meta:
        model = Script
        fields = (
            'id', 'script_date', 'headline', 'source', 'writer',
            'writer_name', 'district', 'district_reporter', 'body',
            'assignment', 'status', 'approved_by', 'approved_by_name',
            'approved_at', 'filename', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted_at',
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'deleted_at', 'approved_by', 'approved_at', 'filename',
        )

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
