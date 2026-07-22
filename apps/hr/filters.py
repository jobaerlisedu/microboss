import django_filters
from .models import DutyRoster, LeaveRequest, LeaveBalance


class DutyRosterFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    employee = django_filters.UUIDFilter()

    class Meta:
        model = DutyRoster
        fields = ['date', 'shift', 'employee', 'date_from', 'date_to']


class LeaveRequestFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='end_date', lookup_expr='lte')

    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'status', 'date_from', 'date_to']


class LeaveBalanceFilter(django_filters.FilterSet):
    class Meta:
        model = LeaveBalance
        fields = ['employee', 'leave_type', 'year']
