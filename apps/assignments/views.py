from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count
from .models import Assignment
from .serializers import AssignmentSerializer
from apps.common.mixins import AuditMixin
from apps.common.permissions import IsOwnerOrAdmin


class AssignmentPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class AssignmentListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset = Assignment.objects.filter(deleted_at__isnull=True)
    serializer_class = AssignmentSerializer
    permission_classes = [IsOwnerOrAdmin]
    pagination_class = AssignmentPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'assign_date', 'reporter']
    search_fields = ['caption', 'reporter', 'district', 'member__username']
    ordering_fields = ['assign_date', 'created_at']
    ordering = ['-assign_date', '-created_at']

    def get_queryset(self):
        return super().get_queryset().select_related('member', 'reporter_user')


class AssignmentDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Assignment.objects.filter(deleted_at__isnull=True)
    serializer_class = AssignmentSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return super().get_queryset().select_related('member', 'reporter_user')

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)


class AssignmentUpdateStatusView(AuditMixin, generics.UpdateAPIView):
    queryset = Assignment.objects.filter(deleted_at__isnull=True)
    serializer_class = AssignmentSerializer
    permission_classes = [IsOwnerOrAdmin]
    http_method_names = ['patch', 'options', 'head']

    def get_queryset(self):
        return super().get_queryset().select_related('member', 'reporter_user')

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        valid_statuses = [s[0] for s in Assignment.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.status = new_status
        instance.updated_by = request.user
        from django.core.exceptions import ValidationError
        try:
            instance.full_clean()
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        instance.save()
        return Response(self.get_serializer(instance).data)


class AssignmentStatsView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get(self, request):
        qs = Assignment.objects.filter(deleted_at__isnull=True)
        today = timezone.now().date()
        month_start = today.replace(day=1)
        agg = qs.aggregate(
            total=Count('id'),
            today=Count('id', filter=Q(assign_date=today)),
            this_month=Count('id', filter=Q(assign_date__gte=month_start)),
            completed=Count('id', filter=Q(status='Done')),
            assigned=Count('id', filter=Q(status='Assigned')),
            processing=Count('id', filter=Q(status='Processing')),
        )
        return Response(agg)
