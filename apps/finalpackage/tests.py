from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from apps.finalpackage.models import FinalPackage
from apps.assignments.models import Assignment

User = get_user_model()


class FinalPackageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='fpuser', password='test1234',
            full_name='FP User', office_id='FPU001',
            designation='User', phone='01711111111',
            blood_group='O+',
        )

    def test_create_package(self):
        pkg = FinalPackage.objects.create(
            package_date=timezone.now().date(),
            title='Test Package',
            producer='Test Producer',
            runtime='5:30',
            status='draft',
            member=self.user,
        )
        self.assertEqual(FinalPackage.objects.count(), 1)
        self.assertEqual(pkg.status, 'draft')
        self.assertIn('Test Package', str(pkg))

    def test_status_choices(self):
        choices = dict(FinalPackage.STATUS_CHOICES)
        self.assertIn('draft', choices)
        self.assertIn('complete', choices)
        self.assertIn('approved', choices)

    def test_verbose_names(self):
        meta = FinalPackage._meta
        self.assertEqual(meta.verbose_name, 'The Final Package')

    def test_str_method(self):
        pkg = FinalPackage.objects.create(
            package_date=timezone.now().date(),
            title='My Package',
            member=self.user,
        )
        self.assertIn('My Package', str(pkg))


class FinalPackageAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='fpapi', password='test1234',
            full_name='FP API', office_id='FPA001',
            designation='User', phone='01722222222',
            blood_group='B+',
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/final-packages/'

    def test_create_package(self):
        resp = self.client.post(self.url, {
            'package_date': timezone.now().date().isoformat(),
            'title': 'API Test Package',
            'producer': 'API Producer',
            'status': 'draft',
            'member': str(self.user.id),
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['title'], 'API Test Package')

    def test_list_packages(self):
        FinalPackage.objects.create(
            package_date=timezone.now().date(),
            title='List Test',
            member=self.user,
        )
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

    def test_stats_endpoint(self):
        FinalPackage.objects.create(
            package_date=timezone.now().date(),
            title='Stats Test',
            status='approved',
            member=self.user,
        )
        resp = self.client.get(f'{self.url}stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total', resp.data)
        self.assertIn('approved', resp.data)

    def test_non_owner_cannot_delete(self):
        other = User.objects.create_user(
            username='other', password='test1234',
            full_name='Other', office_id='OTH001',
            designation='User', phone='01733333333',
            blood_group='A+',
        )
        pkg = FinalPackage.objects.create(
            package_date=timezone.now().date(),
            title='Delete Test',
            member=other,
        )
        resp = self.client.delete(f'{self.url}{pkg.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class FinalPackageSignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='fpsig', password='test1234',
            full_name='FP Signal', office_id='FPS001',
            designation='User', phone='01744444444',
            blood_group='AB+',
        )

    def test_signal_creates_notification_on_create(self):
        from apps.notifications.models import Notification
        pkg = FinalPackage.objects.create(
            package_date=timezone.now().date(),
            title='Signal Test Package',
            member=self.user,
            created_by=self.user,
        )
        notifs = Notification.objects.filter(recipient=self.user)
        self.assertGreaterEqual(notifs.count(), 1)
        self.assertIn('Final Package Created', notifs.first().title)


class FinalPackageCMSTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='fpcms', password='test1234',
            full_name='FP CMS', office_id='FPC001',
            designation='User', phone='01755555555',
            blood_group='O+',
        )
        self.client.login(username='fpcms', password='test1234')

    def test_save_package_via_cms(self):
        resp = self.client.post('/cms/final-packages/save/', {
            'package_date': timezone.now().date().isoformat(),
            'title': 'CMS Test Package',
            'status': 'draft',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(FinalPackage.objects.count(), 1)

    def test_save_package_missing_title_fails(self):
        resp = self.client.post('/cms/final-packages/save/', {
            'package_date': timezone.now().date().isoformat(),
            'title': '',
            'status': 'draft',
        })
        self.assertEqual(FinalPackage.objects.count(), 0)
