from django.utils import timezone
from django.db import IntegrityError, models
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Shift, DutyRoster, Attendance, LeaveType, LeaveRequest, LeaveBalance
from .serializers import (
    ShiftSerializer, DutyRosterSerializer, DutyRosterBulkSerializer,
    AttendanceSerializer, AttendanceCheckSerializer,
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


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.select_related('employee', 'shift').all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'status', 'employee']

    @action(detail=False, methods=['post'])
    def check_in(self, request):
        today = timezone.now().date()
        now = timezone.now()
        existing = Attendance.objects.filter(employee=request.user, date=today).first()
        if existing:
            if existing.check_in:
                return Response({'detail': 'Already checked in today.'}, status=status.HTTP_400_BAD_REQUEST)
            existing.check_in = now
            existing.save(update_fields=['check_in'])
            serializer = self.get_serializer(existing)
            return Response(serializer.data)
        # Determine shift from roster
        from .models import DutyRoster
        roster = DutyRoster.objects.filter(employee=request.user, date=today).first()
        att = Attendance.objects.create(
            employee=request.user, date=today,
            check_in=now, shift=roster.shift if roster else None,
        )
        serializer = self.get_serializer(att)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def check_out(self, request):
        today = timezone.now().date()
        now = timezone.now()
        att = Attendance.objects.filter(employee=request.user, date=today).first()
        if not att:
            return Response({'detail': 'No check-in found for today.'}, status=status.HTTP_400_BAD_REQUEST)
        if att.check_out:
            return Response({'detail': 'Already checked out today.'}, status=status.HTTP_400_BAD_REQUEST)
        att.check_out = now
        # Auto-mark status
        if att.shift:
            late_threshold = (timezone.timedelta(hours=0, minutes=15))
            scheduled_start = timezone.datetime.combine(today, att.shift.start_time)
            scheduled_start = timezone.make_aware(scheduled_start)
            if att.check_in and att.check_in > scheduled_start + late_threshold:
                att.status = Attendance.Status.LATE
        att.save(update_fields=['check_out', 'status'])
        serializer = self.get_serializer(att)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        records = self.get_queryset().filter(date=today).order_by('employee__full_name')
        page = self.paginate_queryset(records)
        serializer = self.get_serializer(page, many=True) if page else self.get_serializer(records, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my(self, request):
        records = self.get_queryset().filter(employee=request.user).order_by('-date')
        page = self.paginate_queryset(records)
        serializer = self.get_serializer(page, many=True) if page else self.get_serializer(records, many=True)
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
