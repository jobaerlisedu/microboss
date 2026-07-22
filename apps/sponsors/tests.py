import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.sponsors.models import Sponsor
from apps.content.models import ContentEntry
from django.utils import timezone

User = get_user_model()


class SponsorModelTest(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.sponsor = Sponsor.objects.create(
            name='Test Sponsor', daily_quota=5, total_quota=100,
            start_date=today - datetime.timedelta(days=30),
            end_date=today + datetime.timedelta(days=30),
            has_doggy=True, has_popup=False, has_tvc=True, has_gpi=False,
        )

    def test_create_sponsor(self):
        self.assertEqual(str(self.sponsor), 'Test Sponsor')

    def test_is_active_within_dates(self):
        self.assertTrue(self.sponsor.is_active)

    def test_is_active_before_start(self):
        s = Sponsor.objects.create(
            name='Future Sponsor', daily_quota=5, total_quota=50,
            start_date=datetime.date(2099, 1, 1),
            end_date=datetime.date(2099, 12, 31),
        )
        self.assertFalse(s.is_active)

    def test_given_count(self):
        user = User.objects.create_user(
            username='sponuser', password='test1234',
            full_name='Spon User', office_id='SPN001',
            designation='User', phone='01711111111',
            blood_group='A+',
        )
        ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='spon-entry', headline='Spon Entry',
            member=user, links={'fb': 'https://fb.com/spon'},
            sponsor=self.sponsor,
        )
        self.assertEqual(self.sponsor.given_count, 1)

    def test_remaining_count(self):
        self.assertEqual(self.sponsor.remaining_count, 100)

    def test_progress_pct(self):
        self.assertEqual(self.sponsor.progress_pct, 0)

    def test_verbose_names(self):
        meta = Sponsor._meta
        self.assertEqual(meta.verbose_name, 'স্পন্সর')

    def test_today_given(self):
        self.assertEqual(self.sponsor.today_given, 0)


class SponsorAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sponapi', password='test1234',
            full_name='Spon API', office_id='SPA001',
            designation='User', phone='01722222222',
            blood_group='B+',
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/sponsors/'

    def test_create_sponsor(self):
        resp = self.client.post(self.url, {
            'name': 'API Sponsor',
            'daily_quota': 3,
            'total_quota': 30,
            'start_date': '2024-06-01',
            'end_date': '2024-08-31',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sponsor.objects.count(), 1)

    def test_list_sponsors(self):
        Sponsor.objects.create(
            name='List Sponsor', daily_quota=5, total_quota=50,
            start_date='2024-01-01', end_date='2024-12-31',
        )
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_sponsor_soft(self):
        sponsor = Sponsor.objects.create(
            name='Del Sponsor', daily_quota=5, total_quota=50,
            start_date='2024-01-01', end_date='2024-12-31',
        )
        resp = self.client.delete(f'{self.url}{sponsor.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Sponsor.objects.filter(deleted_at__isnull=True).count(), 0)
