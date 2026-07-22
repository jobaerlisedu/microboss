from rest_framework import serializers
from .models import ContentListItem


class ContentListItemSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.username', read_only=True)

    class Meta:
        model = ContentListItem
        fields = '__all__'
        read_only_fields = (
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted_at',
        )

    def validate_source(self, value):
        if value == 'district':
            district = self.initial_data.get('district', '')
            if not district:
                raise serializers.ValidationError('জেলা উৎস নির্বাচন করলে জেলার নাম আবশ্যক')
        return value
