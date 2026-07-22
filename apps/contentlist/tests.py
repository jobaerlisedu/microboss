from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.contentlist.models import ContentListItem
from django.utils import timezone

User = get_user_model()


class ContentListItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cluser', password='test1234',
            full_name='CL User', office_id='CLU001',
            designation='User', phone='01711111111',
            blood_group='A+',
        )

    def test_create_item(self):
        item = ContentListItem.objects.create(
            list_date=timezone.now().date(),
            content='Test Content',
            source='district',
            district='Dhaka',
            footage_source='FTP',
            member=self.user,
        )
        self.assertEqual(ContentListItem.objects.count(), 1)
        self.assertIn('Test Content', str(item))

    def test_source_choices(self):
        self.assertEqual(len(ContentListItem.SOURCE_CHOICES), 4)

    def test_footage_choices(self):
        self.assertEqual(len(ContentListItem.FOOTAGE_CHOICES), 7)

    def test_verbose_names(self):
        meta = ContentListItem._meta
        self.assertEqual(meta.verbose_name, 'Table Of Contents')


class ContentListAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='clapi', password='test1234',
            full_name='CL API', office_id='CLA001',
            designation='User', phone='01722222222',
            blood_group='B+',
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/v1/content-lists/'

    def test_create_item(self):
        resp = self.client.post(self.url, {
            'list_date': '2024-03-15',
            'content': 'API Test Content',
            'source': 'social',
            'footage_source': 'WhatsApp',
            'member': str(self.user.id),
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_list_items(self):
        ContentListItem.objects.create(
            list_date=timezone.now().date(),
            content='List Test',
            source='district', district='Khulna',
            footage_source='Google Drive',
            member=self.user,
        )
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_stats_endpoint(self):
        ContentListItem.objects.create(
            list_date=timezone.now().date(),
            content='Stats Test',
            source='studio',
            footage_source='Studio shoot',
            member=self.user,
        )
        resp = self.client.get(f'{self.url}stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total', resp.data)
