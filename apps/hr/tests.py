import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.hr.models import Shift, DutyRoster, LeaveType, LeaveRequest, LeaveBalance

User = get_user_model()


class HRModelsTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='hr_admin',
            full_name='HR Admin',
            office_id='HR001',
            phone='01711111111',
            is_admin=True,
        )
        self.employee = User.objects.create_user(
            username='emp1',
            full_name='John Doe',
            office_id='EMP001',
            phone='01722222222',
        )
        self.shift = Shift.objects.create(
            name='Morning Shift',
            code='MOR',
            start_time=datetime.time(8, 0),
            end_time=datetime.time(16, 0),
        )
        self.leave_type = LeaveType.objects.create(
            name='Casual Leave',
            code='CL',
            days_per_year=14,
        )

    def test_shift_str(self):
        self.assertIn('Morning Shift', str(self.shift))

    def test_duty_roster_creation(self):
        roster = DutyRoster.objects.create(
            employee=self.employee,
            date=datetime.date(2026, 8, 1),
            shift=self.shift,
            assigned_by=self.admin,
        )
        self.assertEqual(roster.employee, self.employee)
        self.assertEqual(str(roster), f'John Doe – 2026-08-01 ({self.shift.name})')

    def test_leave_request_days_calculation(self):
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=datetime.date(2026, 8, 10),
            end_date=datetime.date(2026, 8, 12),
            reason='Personal work',
        )
        self.assertEqual(leave.total_days, 3)
        self.assertEqual(leave.status, LeaveRequest.Status.PENDING)

    def test_leave_balance_remaining_days(self):
        balance = LeaveBalance.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            year=2026,
            total_days=14,
            used_days=3,
        )
        self.assertEqual(balance.remaining_days, 11)


class HRAPITestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_api',
            full_name='Admin API',
            office_id='HR999',
            phone='01799999999',
            is_admin=True,
        )
        self.employee = User.objects.create_user(
            username='emp_api',
            full_name='Employee API',
            office_id='EMP999',
            phone='01788888888',
        )
        self.shift = Shift.objects.create(
            name='Night Shift',
            code='NIG',
            start_time=datetime.time(20, 0),
            end_time=datetime.time(4, 0),
        )
        self.leave_type = LeaveType.objects.create(
            name='Medical Leave',
            code='ML',
            days_per_year=10,
        )
        self.client = APIClient()

    def test_shift_list_permissions(self):
        self.client.force_authenticate(user=self.employee)
        res = self.client.get('/api/v1/hr/shifts/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/v1/hr/shifts/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_duty_roster_bulk_create(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            'employee_ids': [str(self.employee.id)],
            'date': '2026-08-15',
            'shift_id': str(self.shift.id),
            'note': 'Weekend duty',
        }
        res = self.client.post('/api/v1/hr/rosters/bulk/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DutyRoster.objects.filter(employee=self.employee, date='2026-08-15').exists())

    def test_leave_request_create_and_review(self):
        self.client.force_authenticate(user=self.employee)
        payload = {
            'leave_type': str(self.leave_type.id),
            'start_date': '2026-08-20',
            'end_date': '2026-08-22',
            'reason': 'Health checkup',
        }
        res = self.client.post('/api/v1/hr/leave-requests/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        leave_id = res.data['id']

        # Admin approves leave
        self.client.force_authenticate(user=self.admin)
        review_url = f'/api/v1/hr/leave-requests/{leave_id}/review/'
        res_approve = self.client.post(review_url, {'action': 'approve'}, format='json')
        self.assertEqual(res_approve.status_code, status.HTTP_200_OK)

        leave = LeaveRequest.objects.get(id=leave_id)
        self.assertEqual(leave.status, LeaveRequest.Status.APPROVED)

        balance = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type, year=2026)
        self.assertEqual(balance.used_days, 3)
