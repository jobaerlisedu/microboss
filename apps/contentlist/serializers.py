from rest_framework import serializers
from .models import ContentListItem


class ContentListItemSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.username', read_only=True)

    class Meta:
        model = ContentListItem
        fields = (
            'id', 'list_date', 'content', 'source', 'district',
            'footage_source', 'member', 'member_name', 'assignment',
            'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at',
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted_at',
        )

    def validate_source(self, value):
        if value.lower() == 'district':
            district = self.initial_data.get('district', '')
            if not district:
                raise serializers.ValidationError('District name is required if district source is selected')
        return value.capitalize()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
