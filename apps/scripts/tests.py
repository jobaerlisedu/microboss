from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.scripts.models import Script
from django.utils import timezone

User = get_user_model()


class ScriptModelTest(TestCase):
    def setUp(self):
        self.writer = User.objects.create_user(
            username='writer', password='test1234',
            full_name='Script Writer', office_id='WRI001',
            designation='Writer', phone='01711111111',
            blood_group='A+',
        )

    def test_create_script(self):
        s = Script.objects.create(
            script_date=timezone.now().date(),
            headline='Test Script',
            source='social',
            writer=self.writer,
            body='Script body content',
        )
        self.assertEqual(Script.objects.count(), 1)
        self.assertEqual(s.status, 'draft')

    def test_status_choices(self):
        statuses = [s[0] for s in Script.STATUS_CHOICES]
        self.assertIn('draft', statuses)
        self.assertIn('pending', statuses)
        self.assertIn('approved', statuses)

    def test_source_choices(self):
        sources = [s[0] for s in Script.SOURCE_CHOICES]
        self.assertIn('district', sources)
        self.assertIn('reuters', sources)
        self.assertIn('social', sources)
        self.assertIn('studio', sources)

    def test_filename_property(self):
        s = Script.objects.create(
            script_date='2024-03-15',
            headline='Breaking News',
            source='social',
            writer=self.writer,
        )
        fn = s.filename
        self.assertIn('Breaking', fn)
        self.assertIn('writer', fn.lower())

    def test_verbose_names(self):
        meta = Script._meta
        self.assertEqual(meta.verbose_name, 'Digital Script')


class ScriptAPITest(APITestCase):
    def setUp(self):
        self.writer = User.objects.create_user(
            username='scrapi', password='test1234',
            full_name='Script API', office_id='SCA001',
            designation='Writer', phone='01722222222',
            blood_group='B+',
        )
        self.admin = User.objects.create_user(
            username='scradmin', password='test1234',
            full_name='Script Admin', office_id='SCA002',
            designation='Admin', phone='01733333333',
            blood_group='O+', is_admin=True,
        )
        self.client.force_authenticate(user=self.writer)
        self.url = '/api/v1/scripts/'

    def test_create_script(self):
        resp = self.client.post(self.url, {
            'script_date': '2024-03-15',
            'headline': 'API Script',
            'source': 'studio',
            'writer': str(self.writer.id),
            'body': 'API script body',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_list_scripts(self):
        Script.objects.create(
            script_date=timezone.now().date(),
            headline='List Script', source='social',
            writer=self.writer,
        )
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_submit_script(self):
        s = Script.objects.create(
            script_date=timezone.now().date(),
            headline='Submit Script', source='social',
            writer=self.writer,
        )
        self.assertEqual(s.status, 'draft')
        resp = self.client.patch(f'{self.url}{s.id}/submit/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        s.refresh_from_db()
        self.assertEqual(s.status, 'pending')

    def test_submit_non_draft_fails(self):
        s = Script.objects.create(
            script_date=timezone.now().date(),
            headline='Already Submitted', source='social',
            writer=self.writer, status='pending',
        )
        resp = self.client.patch(f'{self.url}{s.id}/submit/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ScriptApprovalTest(APITestCase):
    def setUp(self):
        self.writer = User.objects.create_user(
            username='appwr', password='test1234',
            full_name='Approval Writer', office_id='APW001',
            designation='Writer', phone='01744444444',
            blood_group='A+',
        )
        self.admin = User.objects.create_user(
            username='appadm', password='test1234',
            full_name='Approval Admin', office_id='APA001',
            designation='Admin', phone='01755555555',
            blood_group='B+', is_admin=True,
        )
        self.url = '/api/v1/scripts/'

    def test_admin_can_approve(self):
        s = Script.objects.create(
            script_date=timezone.now().date(),
            headline='Approve Me', source='district',
            writer=self.writer, status='pending',
        )
        self.client.force_authenticate(user=self.admin)
        resp = self.client.patch(f'{self.url}{s.id}/approve/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        s.refresh_from_db()
        self.assertEqual(s.status, 'approved')
        self.assertEqual(s.approved_by.id, self.admin.id)
        self.assertIsNotNone(s.approved_at)

    def test_non_admin_cannot_approve(self):
        s = Script.objects.create(
            script_date=timezone.now().date(),
            headline='No Approve', source='social',
            writer=self.writer, status='pending',
        )
        self.client.force_authenticate(user=self.writer)
        resp = self.client.patch(f'{self.url}{s.id}/approve/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_non_pending_fails(self):
        s = Script.objects.create(
            script_date=timezone.now().date(),
            headline='Already Done', source='social',
            writer=self.writer, status='approved',
        )
        self.client.force_authenticate(user=self.admin)
        resp = self.client.patch(f'{self.url}{s.id}/approve/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
