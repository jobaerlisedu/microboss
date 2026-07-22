from rest_framework import generics, filters, views
from rest_framework.response import Response
from django.utils import timezone
from .models import Sponsor
from .serializers import SponsorSerializer
from apps.common.mixins import AuditMixin


class SponsorListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset = Sponsor.objects.filter(deleted_at__isnull=True)
    serializer_class = SponsorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'content_type']
    ordering_fields = ['name', 'start_date', 'end_date']
    ordering = ['name']


class SponsorDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Sponsor.objects.filter(deleted_at__isnull=True)
    serializer_class = SponsorSerializer

    def perform_destroy(self, instance):
        instance.soft_delete()


class SponsorTrackView(views.APIView):
    def get(self, request):
        today = timezone.now().date()
        active = Sponsor.objects.filter(
            deleted_at__isnull=True,
            start_date__lte=today,
            end_date__gte=today,
        )
        data = []
        for s in active:
            data.append({
                'id': str(s.id),
                'name': s.name,
                'daily_quota': s.daily_quota,
                'total_quota': s.total_quota,
                'given_count': s.given_count,
                'remaining_count': s.remaining_count,
                'today_given': s.today_given,
                'today_remaining': s.today_remaining,
                'progress_pct': s.progress_pct,
                'is_active': True,
            })
        return Response(data)
