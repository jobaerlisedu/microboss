from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import ContentEntry
from .serializers import ContentEntrySerializer
from apps.common.mixins import AuditMixin
from apps.common.permissions import IsOwnerOrAdmin


class ContentEntryListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset = ContentEntry.objects.filter(deleted_at__isnull=True)
    serializer_class = ContentEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['member', 'sponsor', 'entry_date']
    search_fields = ['headline', 'slug', 'member__username', 'comment']
    ordering_fields = ['entry_date', 'entry_time', 'created_at']
    ordering = ['-entry_date', '-entry_time']

    def get_queryset(self):
        return super().get_queryset().select_related('member', 'sponsor')


class ContentEntryDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = ContentEntry.objects.filter(deleted_at__isnull=True)
    serializer_class = ContentEntrySerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_destroy(self, instance):
        instance.soft_delete()


class ContentEntryStatsView(APIView):
    def get(self, request):
        qs = ContentEntry.objects.filter(deleted_at__isnull=True)
        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Response({
            'total': qs.count(),
            'this_month': qs.filter(entry_date__gte=this_month_start).count(),
            'sponsored': qs.filter(sponsor__isnull=False).count(),
            'today': qs.filter(entry_date=now.date()).count(),
        })


class ContentEntryByMonthView(APIView):
    def get(self, request, year, month):
        entries = ContentEntry.objects.filter(
            deleted_at__isnull=True,
            entry_date__year=year,
            entry_date__month=month,
        ).select_related('member', 'sponsor').order_by('-entry_date', '-entry_time')
        return Response(ContentEntrySerializer(entries, many=True).data)
