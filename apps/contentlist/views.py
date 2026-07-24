from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import ContentListItem
from .serializers import ContentListItemSerializer
from apps.common.mixins import AuditMixin
from apps.common.permissions import IsOwnerOrAdmin


class ContentListListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset = ContentListItem.objects.filter(deleted_at__isnull=True)
    serializer_class = ContentListItemSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source', 'footage_source', 'list_date']
    search_fields = ['content', 'district', 'member__username']
    ordering_fields = ['list_date', 'created_at']
    ordering = ['-list_date', '-created_at']

    def get_queryset(self):
        return super().get_queryset().select_related('member')


class ContentListDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = ContentListItem.objects.filter(deleted_at__isnull=True)
    serializer_class = ContentListItemSerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_destroy(self, instance):
        instance.soft_delete()


class ContentListStatsView(APIView):
    def get(self, request):
        qs = ContentListItem.objects.filter(deleted_at__isnull=True)
        today = timezone.now().date()
        month_start = today.replace(day=1)
        return Response({
            'total': qs.count(),
            'today': qs.filter(list_date=today).count(),
            'this_month': qs.filter(list_date__gte=month_start).count(),
            'district_count': qs.filter(source__iexact='District').count(),
        })
