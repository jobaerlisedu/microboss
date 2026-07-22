from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from apps.assignments.models import Assignment
from apps.assignments.serializers import AssignmentSerializer

User = get_user_model()


class AssignmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='assuser', password='test1234',
            full_name='Ass User', office_id='ASU001',
            designation='User', phone='01711111111',
            blood_group='A+',
        )

    def test_create_assignment(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(),
            caption='Test Assignment',
            reporter='John Doe',
            district='Dhaka',
            member=self.user,
        )
        self.assertEqual(Assignment.objects.count(), 1)
        self.assertEqual(a.status, 'Assigned')

    def test_status_choices(self):
        statuses = [s[0] for s in Assignment.STATUS_CHOICES]
        self.assertIn('Assigned', statuses)
        self.assertIn('Processing', statuses)
        self.assertIn('Done', statuses)
        self.assertIn('Cancel', statuses)

    def test_verbose_names(self):
        meta = Assignment._meta
        self.assertEqual(meta.verbose_name, 'এসাইনমেন্ট')

    def test_str_method(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(),
            caption='Str Test', reporter='Jane',
            member=self.user,
        )
        self.assertIn('Assigned', str(a))

    def test_future_date_raises_error(self):
        future = timezone.now().date() + timezone.timedelta(days=7)
        a = Assignment(
            assign_date=future, caption='Future', reporter='F',
            member=self.user,
        )
        with self.assertRaises(ValidationError):
            a.full_clean()

    def test_cancel_status_valid(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(), caption='Cancel Test',
            reporter='Cancel', member=self.user,
        )
        a.status = 'Cancel'
        a.save()
        self.assertEqual(a.status, 'Cancel')


class AssignmentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='assapi', password='test1234',
            full_name='Ass API', office_id='ASA001',
            designation='User', phone='01722222222',
            blood_group='B+',
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('assignments:assignment-list')

    def test_create_assignment(self):
        resp = self.client.post(self.url, {
            'assign_date': '2024-03-15',
            'caption': 'API Assignment',
            'reporter': 'API Reporter',
            'member': str(self.user.id),
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_created_by_set_on_create(self):
        resp = self.client.post(self.url, {
            'assign_date': timezone.now().date().isoformat(),
            'caption': 'Creator Test',
            'reporter': 'Creator Reporter',
            'member': str(self.user.id),
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        a = Assignment.objects.get(pk=resp.data['id'])
        self.assertEqual(a.created_by, self.user)
        self.assertEqual(a.updated_by, self.user)

    def test_list_assignments(self):
        Assignment.objects.create(
            assign_date=timezone.now().date(),
            caption='List Test', reporter='List Reporter',
            member=self.user,
        )
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_status(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(),
            caption='Status Test', reporter='Status Reporter',
            member=self.user,
        )
        resp = self.client.patch(
            reverse('assignments:assignment-status', kwargs={'pk': a.id}),
            {'status': 'Processing'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        a.refresh_from_db()
        self.assertEqual(a.status, 'Processing')

    def test_update_status_invalid(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(),
            caption='Invalid Status', reporter='Inv Reporter',
            member=self.user,
        )
        resp = self.client.patch(
            reverse('assignments:assignment-status', kwargs={'pk': a.id}),
            {'status': 'InvalidStatus'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stats_endpoint(self):
        Assignment.objects.create(
            assign_date=timezone.now().date(),
            caption='Stats Test', reporter='Stats Reporter',
            member=self.user,
        )
        resp = self.client.get(reverse('assignments:assignment-stats'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total', resp.data)

    def test_stats_total_includes_all_dates(self):
        today = timezone.now().date()
        Assignment.objects.create(
            assign_date=today, caption='Today',
            reporter='R1', member=self.user,
        )
        Assignment.objects.create(
            assign_date=today - timezone.timedelta(days=5), caption='Old',
            reporter='R2', member=self.user,
        )
        resp = self.client.get(reverse('assignments:assignment-stats'))
        self.assertEqual(resp.data['total'], 2)
        self.assertEqual(resp.data['today'], 1)

    def test_status_workflow_order(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(),
            caption='Workflow', reporter='WF Reporter',
            member=self.user,
        )
        self.client.patch(
            reverse('assignments:assignment-status', kwargs={'pk': a.id}),
            {'status': 'Processing'}, format='json',
        )
        a.refresh_from_db()
        self.assertEqual(a.status, 'Processing')
        self.client.patch(
            reverse('assignments:assignment-status', kwargs={'pk': a.id}),
            {'status': 'Done'}, format='json',
        )
        a.refresh_from_db()
        self.assertEqual(a.status, 'Done')

    def test_soft_delete_sets_updated_by(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(), caption='Del Test',
            reporter='Del Reporter', member=self.user,
            created_by=self.user, updated_by=self.user,
        )
        resp = self.client.delete(
            reverse('assignments:assignment-detail', kwargs={'pk': a.id}),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        a.refresh_from_db()
        self.assertIsNotNone(a.deleted_at)
        self.assertEqual(a.updated_by, self.user)

    def test_non_owner_cannot_update_status(self):
        other = User.objects.create_user(
            username='other', password='test1234',
            full_name='Other User', office_id='OTH001',
            designation='User', phone='01733333333',
            blood_group='O+',
        )
        a = Assignment.objects.create(
            assign_date=timezone.now().date(), caption='Perm Test',
            reporter='Perm Reporter', member=other,
        )
        resp = self.client.patch(
            reverse('assignments:assignment-status', kwargs={'pk': a.id}),
            {'status': 'Processing'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_owner_cannot_delete(self):
        other = User.objects.create_user(
            username='other2', password='test1234',
            full_name='Other User 2', office_id='OTH002',
            designation='User', phone='01744444444',
            blood_group='AB+',
        )
        a = Assignment.objects.create(
            assign_date=timezone.now().date(), caption='Perm Del',
            reporter='Perm Del', member=other,
        )
        resp = self.client.delete(
            reverse('assignments:assignment-detail', kwargs={'pk': a.id}),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_signal_creates_notification(self):
        from apps.notifications.models import Notification
        reporter = User.objects.create_user(
            username='reporter', password='test1234',
            full_name='The Reporter', office_id='REP001',
            designation='Reporter', phone='01766666666',
            blood_group='O+',
        )
        a = Assignment.objects.create(
            assign_date=timezone.now().date(), caption='Signal Test',
            reporter='Signal Reporter', member=self.user,
            reporter_user=reporter, created_by=self.user,
        )
        self.assertTrue(Notification.objects.filter(recipient=reporter).exists())


class AssignmentSerializerNullTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='seruser', password='test1234',
            full_name='Ser User', office_id='SER001',
            designation='User', phone='01755555555',
            blood_group='A+',
        )

    def test_reporter_user_name_returns_empty_string_when_null(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(), caption='Null FK Test',
            reporter='Manual Reporter', member=self.user,
            reporter_user=None,
        )
        s = AssignmentSerializer(a)
        self.assertEqual(s.data['reporter_user_name'], '')

    def test_reporter_user_name_returns_full_name_when_set(self):
        a = Assignment.objects.create(
            assign_date=timezone.now().date(), caption='FK Set Test',
            reporter='FK Reporter', member=self.user,
            reporter_user=self.user,
        )
        s = AssignmentSerializer(a)
        self.assertEqual(s.data['reporter_user_name'], self.user.full_name)
