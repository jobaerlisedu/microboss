from rest_framework import serializers
from .models import ContentEntry


class ContentEntrySerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.username', read_only=True)
    sponsor_name = serializers.CharField(
        source='sponsor.name', read_only=True, allow_null=True,
    )

    class Meta:
        model = ContentEntry
        fields = '__all__'
        read_only_fields = (
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted_at',
        )

    def validate_links(self, value):
        if not value or not any(v for v in value.values() if v):
            raise serializers.ValidationError('অন্তত ১টি লিংক আবশ্যক')
        return value

    def validate(self, attrs):
        headline = attrs.get('headline', '').strip()
        instance_id = self.instance.id if self.instance else None

        if headline:
            dup_qs = ContentEntry.objects.filter(
                headline__iexact=headline, deleted_at__isnull=True,
            )
            if instance_id:
                dup_qs = dup_qs.exclude(id=instance_id)
            if dup_qs.exists():
                raise serializers.ValidationError(
                    {'headline': 'এই হেডলাইনটি আগেই তালিকায় আছে'}
                )

        links = attrs.get('links', {})
        for key, url in links.items():
            if not url:
                continue
            dup_qs = ContentEntry.objects.filter(
                **{f'links__{key}': url}, deleted_at__isnull=True,
            )
            if instance_id:
                dup_qs = dup_qs.exclude(id=instance_id)
            if dup_qs.exists():
                raise serializers.ValidationError(
                    {'links': f'এই লিংকটি ({key}) আগেই তালিকায় আছে'}
                )

        return attrs
