from django.contrib import admin
from .models import Shift, DutyRoster, LeaveType, LeaveRequest, LeaveBalance


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'start_time', 'end_time', 'is_active']
    list_filter = ['is_active']


@admin.register(DutyRoster)
class DutyRosterAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'shift', 'note']
    list_filter = ['date', 'shift']
    search_fields = ['employee__full_name', 'employee__username']


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'days_per_year', 'carry_forward', 'requires_approval', 'is_active']
    list_filter = ['is_active', 'carry_forward']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'total_days', 'status']
    list_filter = ['status', 'leave_type']
    search_fields = ['employee__full_name', 'employee__username']
    date_hierarchy = 'start_date'


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'year', 'total_days', 'used_days', 'remaining_days']
    list_filter = ['year', 'leave_type']
    search_fields = ['employee__full_name', 'employee__username']
