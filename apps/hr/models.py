import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Shift(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Shift Name', max_length=100)
    code = models.CharField('Code', max_length=10, unique=True)
    start_time = models.TimeField('Start Time')
    end_time = models.TimeField('End Time')
    is_active = models.BooleanField('Active', default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Shift'
        verbose_name_plural = 'Shifts'
        ordering = ['start_time']

    def __str__(self):
        return f'{self.name} ({self.start_time:%H:%M}–{self.end_time:%H:%M})'


class DutyRoster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='duty_rosters', verbose_name='Employee',
    )
    date = models.DateField('Date', db_index=True)
    shift = models.ForeignKey(
        Shift, on_delete=models.PROTECT,
        related_name='rosters', verbose_name='Shift',
    )
    note = models.CharField('Note', max_length=500, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_rosters',
        verbose_name='Assigned By',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Duty Roster'
        verbose_name_plural = 'Duty Rosters'
        unique_together = ['employee', 'date']
        indexes = [
            models.Index(fields=['date', 'shift']),
        ]
        ordering = ['-date', 'employee']

    def __str__(self):
        return f'{self.employee.full_name} – {self.date} ({self.shift.name})'


class LeaveType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Leave Type', max_length=100)
    code = models.CharField('Code', max_length=20, unique=True)
    days_per_year = models.PositiveSmallIntegerField('Days Per Year', default=0)
    carry_forward = models.BooleanField('Carry Forward', default=False)
    requires_approval = models.BooleanField('Requires Approval', default=True)
    is_active = models.BooleanField('Active', default=True, db_index=True)
    sort_order = models.PositiveSmallIntegerField('Sort Order', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leave Type'
        verbose_name_plural = 'Leave Types'
        ordering = ['sort_order']

    def __str__(self):
        return f'{self.name} ({self.days_per_year} days)'


class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='leave_requests', verbose_name='Employee',
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT,
        related_name='leave_requests', verbose_name='Leave Type',
    )
    start_date = models.DateField('Start Date', db_index=True)
    end_date = models.DateField('End Date')
    total_days = models.PositiveSmallIntegerField('Total Days', editable=False)
    reason = models.TextField('Reason')
    status = models.CharField(
        'Status', max_length=20,
        choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='approved_leave_requests',
        verbose_name='Approved By',
    )
    approved_at = models.DateTimeField('Approved At', null=True, blank=True)
    rejection_reason = models.TextField('Rejection Reason', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='hr_leaverequest_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='hr_leaverequest_updated',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        self.total_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.employee.full_name} – {self.leave_type.name} ({self.start_date}–{self.end_date})'


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'present', 'Present'
        LATE = 'late', 'Late'
        HALF_DAY = 'half_day', 'Half Day'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='attendances', verbose_name='Employee',
    )
    date = models.DateField('Date', db_index=True)
    check_in = models.DateTimeField('Check In', null=True, blank=True)
    check_out = models.DateTimeField('Check Out', null=True, blank=True)
    status = models.CharField(
        'Status', max_length=20,
        choices=Status.choices, default=Status.PRESENT,
    )
    shift = models.ForeignKey(
        Shift, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendances', verbose_name='Shift',
    )
    note = models.CharField('Note', max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        unique_together = ['employee', 'date']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['employee', 'date']),
        ]
        ordering = ['-date', 'employee']

    def __str__(self):
        ci = self.check_in.strftime('%H:%M') if self.check_in else '--'
        co = self.check_out.strftime('%H:%M') if self.check_out else '--'
        return f'{self.employee.full_name} — {self.date} ({ci}–{co})'


class LeaveBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='leave_balances', verbose_name='Employee',
    )
    leave_type = models.ForeignKey(
        LeaveType, on_delete=models.PROTECT,
        related_name='balances', verbose_name='Leave Type',
    )
    year = models.PositiveSmallIntegerField(
        'Year', db_index=True,
        validators=[MinValueValidator(2020), MaxValueValidator(2099)],
    )
    total_days = models.DecimalField('Total Days', max_digits=5, decimal_places=1)
    used_days = models.DecimalField('Used Days', max_digits=5, decimal_places=1, default=0)

    class Meta:
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['employee', 'leave_type']

    @property
    def remaining_days(self):
        return self.total_days - self.used_days

    def __str__(self):
        return f'{self.employee.full_name} – {self.leave_type.name} {self.year}: {self.remaining_days}/{self.total_days}'
