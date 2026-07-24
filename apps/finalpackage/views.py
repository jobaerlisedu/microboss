from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import FinalPackage
from .serializers import FinalPackageSerializer
from apps.common.mixins import AuditMixin
from apps.common.permissions import IsOwnerOrAdmin


class FinalPackageListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset = FinalPackage.objects.filter(deleted_at__isnull=True)
    serializer_class = FinalPackageSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'package_date']
    search_fields = ['title', 'producer', 'member__username']
    ordering_fields = ['package_date', 'created_at']
    ordering = ['-package_date', '-created_at']

    def get_queryset(self):
        return super().get_queryset().select_related('member', 'editor_user', 'assignment')


class FinalPackageDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = FinalPackage.objects.filter(deleted_at__isnull=True)
    serializer_class = FinalPackageSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return super().get_queryset().select_related('member', 'editor_user', 'assignment')

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)


class FinalPackageStatsView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request):
        qs = FinalPackage.objects.filter(deleted_at__isnull=True)
        now = timezone.now()
        today = now.date()
        month_start = today.replace(day=1)
        return Response({
            'total': qs.count(),
            'today': qs.filter(package_date=today).count(),
            'this_month': qs.filter(package_date__gte=month_start).count(),
            'draft': qs.filter(status='draft').count(),
            'complete': qs.filter(status='complete').count(),
            'approved': qs.filter(status='approved').count(),
        })
