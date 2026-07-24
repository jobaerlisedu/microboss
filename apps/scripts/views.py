from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Script
from .serializers import ScriptSerializer
from apps.common.mixins import AuditMixin
from apps.common.permissions import IsOwnerOrAdmin


class ScriptListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset = Script.objects.filter(deleted_at__isnull=True)
    serializer_class = ScriptSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'source', 'script_date', 'writer']
    search_fields = ['headline', 'writer__username', 'district']
    ordering_fields = ['script_date', 'created_at']
    ordering = ['-script_date', '-created_at']

    def get_queryset(self):
        return super().get_queryset().select_related('writer', 'approved_by')


class ScriptDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Script.objects.filter(deleted_at__isnull=True)
    serializer_class = ScriptSerializer
    permission_classes = [IsOwnerOrAdmin]

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)


class ScriptSubmitView(generics.UpdateAPIView):
    queryset = Script.objects.filter(deleted_at__isnull=True)
    serializer_class = ScriptSerializer
    permission_classes = [IsOwnerOrAdmin]

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 'draft':
            return Response(
                {'error': 'Only draft scripts can be submitted'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = 'pending'
        instance.updated_by = request.user
        instance.save()
        return Response(ScriptSerializer(instance).data)


class ScriptApproveView(generics.UpdateAPIView):
    queryset = Script.objects.filter(deleted_at__isnull=True)
    serializer_class = ScriptSerializer
    permission_classes = [IsOwnerOrAdmin]

    def patch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admin can grant approval'},
                status=status.HTTP_403_FORBIDDEN,
            )
        instance = self.get_object()
        if instance.status not in ('pending', 'draft'):
            return Response(
                {'error': 'Only pending or draft scripts can be approved'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = 'approved'
        instance.approved_by = request.user
        instance.approved_at = timezone.now()
        instance.updated_by = request.user
        instance.save()
        return Response(ScriptSerializer(instance).data)


class ScriptStatsView(APIView):
    def get(self, request):
        qs = Script.objects.filter(deleted_at__isnull=True)
        today = timezone.now().date()
        month_start = today.replace(day=1)
        my_scripts = qs.filter(writer=request.user)
        return Response({
            'total': qs.count(),
            'my_total': my_scripts.count(),
            'my_today': my_scripts.filter(script_date=today).count(),
            'my_month': my_scripts.filter(script_date__gte=month_start).count(),
            'pending': qs.filter(status='pending').count(),
            'approved': qs.filter(status='approved').count(),
        })
