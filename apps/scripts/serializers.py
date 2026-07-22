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
        fields = '__all__'
        read_only_fields = (
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'deleted_at', 'approved_by', 'approved_at', 'filename',
        )
