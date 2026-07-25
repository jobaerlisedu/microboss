from rest_framework import serializers
from .models import Shift, DutyRoster, Attendance, LeaveType, LeaveRequest, LeaveBalance


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['id', 'name', 'code', 'start_time', 'end_time', 'is_active']


class DutyRosterSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    shift_name = serializers.SerializerMethodField()

    class Meta:
        model = DutyRoster
        fields = ['id', 'employee', 'employee_name', 'date', 'shift', 'shift_name', 'note', 'assigned_by', 'created_at']

    def get_employee_name(self, obj):
        return obj.employee.full_name

    def get_shift_name(self, obj):
        return obj.shift.name


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    shift_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'date',
            'check_in', 'check_out', 'status', 'shift', 'shift_name', 'note',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['employee', 'check_in', 'check_out', 'status']

    def get_employee_name(self, obj):
        return obj.employee.full_name

    def get_shift_name(self, obj):
        return obj.shift.name if obj.shift else None


class AttendanceCheckSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, default='')
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)


class DutyRosterBulkSerializer(serializers.Serializer):
    employee_ids = serializers.ListField(child=serializers.UUIDField())
    date = serializers.DateField()
    shift_id = serializers.UUIDField()
    note = serializers.CharField(required=False, default='')


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'name', 'code', 'days_per_year', 'carry_forward', 'requires_approval', 'is_active']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_type_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
            'start_date', 'end_date', 'total_days', 'reason', 'status',
            'approved_by', 'approved_by_name', 'approved_at', 'rejection_reason',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['employee', 'status', 'approved_by', 'approved_at', 'total_days']


    def get_employee_name(self, obj):
        return obj.employee.full_name

    def get_leave_type_name(self, obj):
        return obj.leave_type.name

    def get_approved_by_name(self, obj):
        return obj.approved_by.full_name if obj.approved_by else None


class LeaveRequestActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class LeaveBalanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    leave_type_name = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()

    class Meta:
        model = LeaveBalance
        fields = ['id', 'employee', 'employee_name', 'leave_type', 'leave_type_name',
                  'year', 'total_days', 'used_days', 'remaining_days']

    def get_employee_name(self, obj):
        return obj.employee.full_name

    def get_leave_type_name(self, obj):
        return obj.leave_type.name

    def get_remaining_days(self, obj):
        return obj.remaining_days
