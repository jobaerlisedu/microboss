from django.utils import timezone
from django.db import IntegrityError, models
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Shift, DutyRoster, LeaveType, LeaveRequest, LeaveBalance
from .serializers import (
    ShiftSerializer, DutyRosterSerializer, DutyRosterBulkSerializer,
    LeaveTypeSerializer, LeaveRequestSerializer, LeaveRequestActionSerializer,
    LeaveBalanceSerializer,
)
from .filters import DutyRosterFilter, LeaveRequestFilter, LeaveBalanceFilter
from apps.common.permissions import IsAdmin


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code']


class DutyRosterViewSet(viewsets.ModelViewSet):
    queryset = DutyRoster.objects.select_related('employee', 'shift', 'assigned_by').all()
    serializer_class = DutyRosterSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DutyRosterFilter

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        serializer = DutyRosterBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        created = []
        errors = []
        for emp_id in data['employee_ids']:
            try:
                obj, _ = DutyRoster.objects.update_or_create(
                    employee_id=emp_id,
                    date=data['date'],
                    defaults={
                        'shift_id': data['shift_id'],
                        'note': data.get('note', ''),
                        'assigned_by': request.user,
                    },
                )
                created.append(str(obj.id))
            except IntegrityError as e:
                errors.append({'employee_id': str(emp_id), 'error': str(e)})
        return Response({'created': created, 'errors': errors}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my(self, request):
        today = timezone.now().date()
        rosters = self.get_queryset().filter(
            employee=request.user,
            date__gte=today - timezone.timedelta(days=7),
            date__lte=today + timezone.timedelta(days=30),
        ).order_by('date')
        page = self.paginate_queryset(rosters)
        serializer = self.get_serializer(page, many=True) if page else self.get_serializer(rosters, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)


class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.filter(is_active=True)
    serializer_class = LeaveTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active', 'carry_forward']


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.select_related(
        'employee', 'leave_type', 'approved_by', 'created_by'
    ).all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LeaveRequestFilter

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        leave = self.get_object()
        if leave.employee != request.user and not request.user.is_admin:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        if leave.status not in (LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED):
            return Response({'detail': 'Cannot cancel in current status.'}, status=status.HTTP_400_BAD_REQUEST)
        leave.status = LeaveRequest.Status.CANCELLED
        leave.save(update_fields=['status'])
        return Response(self.get_serializer(leave).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def review(self, request, pk=None):
        leave = self.get_object()
        serializer = LeaveRequestActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data['action']
        if leave.status != LeaveRequest.Status.PENDING:
            return Response({'detail': 'Only pending requests can be reviewed.'}, status=status.HTTP_400_BAD_REQUEST)
        if action == 'approve':
            leave.status = LeaveRequest.Status.APPROVED
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save(update_fields=['status', 'approved_by', 'approved_at'])
            self._update_balance(leave)
        else:
            leave.status = LeaveRequest.Status.REJECTED
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            leave.save(update_fields=['status', 'approved_by', 'approved_at', 'rejection_reason'])
        return Response(self.get_serializer(leave).data)

    def _update_balance(self, leave):
        balance, _ = LeaveBalance.objects.get_or_create(
            employee=leave.employee,
            leave_type=leave.leave_type,
            year=leave.start_date.year,
            defaults={'total_days': leave.leave_type.days_per_year},
        )
        used = LeaveRequest.objects.filter(
            employee=leave.employee,
            leave_type=leave.leave_type,
            status=LeaveRequest.Status.APPROVED,
            start_date__year=leave.start_date.year,
        ).aggregate(total=models.Sum('total_days'))['total'] or 0
        balance.used_days = used
        balance.save(update_fields=['used_days'])

    @action(detail=False, methods=['get'])
    def my(self, request):
        leaves = self.get_queryset().filter(employee=request.user)
        page = self.paginate_queryset(leaves)
        serializer = self.get_serializer(page, many=True) if page else self.get_serializer(leaves, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def pending(self, request):
        leaves = self.get_queryset().filter(status=LeaveRequest.Status.PENDING)
        page = self.paginate_queryset(leaves)
        serializer = self.get_serializer(page, many=True) if page else self.get_serializer(leaves, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LeaveBalance.objects.select_related('employee', 'leave_type').all()
    serializer_class = LeaveBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LeaveBalanceFilter

    @action(detail=False, methods=['get'])
    def my(self, request):
        balances = self.get_queryset().filter(employee=request.user)
        serializer = self.get_serializer(balances, many=True)
        return Response(serializer.data)
