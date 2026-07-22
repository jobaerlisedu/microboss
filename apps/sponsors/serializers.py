from rest_framework import serializers
from .models import Sponsor


class SponsorSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    given_count = serializers.IntegerField(read_only=True)
    remaining_count = serializers.IntegerField(read_only=True)
    today_given = serializers.IntegerField(read_only=True)
    today_remaining = serializers.IntegerField(read_only=True)
    progress_pct = serializers.IntegerField(read_only=True)

    class Meta:
        model = Sponsor
        fields = (
            'id', 'name', 'daily_quota', 'total_quota',
            'start_date', 'end_date', 'content_type',
            'has_doggy', 'has_popup', 'has_tvc', 'has_gpi',
            'is_active', 'given_count', 'remaining_count',
            'today_given', 'today_remaining', 'progress_pct',
            'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at',
        )
        read_only_fields = (
            'id', 'created_at', 'updated_at',
            'created_by', 'updated_by', 'deleted_at',
            'is_active', 'given_count', 'remaining_count',
            'today_given', 'today_remaining', 'progress_pct',
        )
