from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.content.models import ContentEntry
from apps.sponsors.models import Sponsor
from django.utils import timezone

User = get_user_model()


class ContentEntryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='contentuser', password='test1234',
            full_name='Content User', office_id='CNT001',
            designation='User', phone='01711111111',
            blood_group='A+',
        )

    def test_create_entry(self):
        entry = ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='test-slug',
            headline='Test Headline',
            member=self.user,
            links={'fb': 'https://facebook.com/test'},
        )
        self.assertEqual(ContentEntry.objects.count(), 1)
        self.assertIn('Test Headline', str(entry))

    def test_entry_verbose_names(self):
        meta = ContentEntry._meta
        self.assertEqual(meta.verbose_name, 'Content Entry')

    def test_soft_delete(self):
        entry = ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='del-slug', headline='To Delete',
            member=self.user, links={'fb': 'https://fb.com/del'},
        )
        entry.deleted_at = timezone.now()
        entry.save()
        self.assertEqual(ContentEntry.objects.filter(deleted_at__isnull=True).count(), 0)


class ContentEntryAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='apiuser', password='test1234',
            full_name='API User', office_id='API001',
            designation='User', phone='01722222222',
            blood_group='B+',
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = '/api/v1/entries/'

    def test_create_entry(self):
        resp = self.client.post(self.list_url, {
            'entry_date': '2024-03-15',
            'entry_time': '14:30:00',
            'slug': 'api-test',
            'headline': 'API Test Entry',
            'member': str(self.user.id),
            'links': {'fb': 'https://fb.com/api-test'},
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ContentEntry.objects.count(), 1)

    def test_create_entry_no_links_fails(self):
        resp = self.client.post(self.list_url, {
            'entry_date': '2024-03-15',
            'entry_time': '14:30:00',
            'slug': 'no-link',
            'headline': 'No Links',
            'member': str(self.user.id),
            'links': {},
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_entries(self):
        ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='list-test', headline='List Test',
            member=self.user, links={'yt': 'https://yt.com/test'},
        )
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

    def test_duplicate_headline_fails(self):
        ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='first', headline='Duplicate Headline',
            member=self.user, links={'fb': 'https://fb.com/first'},
        )
        resp = self.client.post(self.list_url, {
            'entry_date': '2024-03-15',
            'entry_time': '14:30:00',
            'slug': 'second',
            'headline': 'Duplicate Headline',
            'member': str(self.user.id),
            'links': {'fb': 'https://fb.com/second'},
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_delete(self):
        entry = ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='del-me', headline='Delete Me',
            member=self.user, links={'fb': 'https://fb.com/del-me'},
        )
        resp = self.client.delete(f'{self.list_url}{entry.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_stats_endpoint(self):
        ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='stats-test', headline='Stats Test',
            member=self.user, links={'fb': 'https://fb.com/stats'},
        )
        resp = self.client.get(f'{self.list_url}stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total', resp.data)


class ContentEntrySponsorTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sponsoruser', password='test1234',
            full_name='Sponsor User', office_id='SPU001',
            designation='User', phone='01733333333',
            blood_group='O+',
        )
        self.client.force_authenticate(user=self.user)
        self.sponsor = Sponsor.objects.create(
            name='Test Sponsor', daily_quota=5, total_quota=50,
            start_date='2024-01-01', end_date='2024-12-31',
        )

    def test_create_entry_with_sponsor(self):
        resp = self.client.post('/api/v1/entries/', {
            'entry_date': '2024-03-15',
            'entry_time': '14:30:00',
            'slug': 'sponsored-entry',
            'headline': 'Sponsored Entry',
            'member': str(self.user.id),
            'links': {'fb': 'https://fb.com/sponsored'},
            'sponsor': str(self.sponsor.id),
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        entry = ContentEntry.objects.first()
        self.assertEqual(entry.sponsor.id, self.sponsor.id)
