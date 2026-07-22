from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from apps.content.models import ContentEntry
from django.utils import timezone

User = get_user_model()


class LeaderboardAPITest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='topuser', password='test1234',
            full_name='Top User', office_id='TOP001',
            designation='User', phone='01711111111',
            blood_group='A+',
        )
        self.user2 = User.objects.create_user(
            username='second', password='test1234',
            full_name='Second User', office_id='SEC001',
            designation='User', phone='01722222222',
            blood_group='B+',
        )
        self.client.force_authenticate(user=self.user1)
        ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='entry-1', headline='Entry 1',
            member=self.user1, links={'fb': 'https://fb.com/1'},
        )
        ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='entry-2', headline='Entry 2',
            member=self.user1, links={'fb': 'https://fb.com/2'},
        )
        ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='entry-3', headline='Entry 3',
            member=self.user2, links={'fb': 'https://fb.com/3'},
        )

    def test_leaderboard_returns_top_users(self):
        resp = self.client.get('/api/v1/leaders/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 2)
        self.assertEqual(resp.data[0]['entry_count'], 2)
        self.assertEqual(resp.data[1]['entry_count'], 1)

    def test_leaderboard_rank_order(self):
        resp = self.client.get('/api/v1/leaders/')
        self.assertEqual(resp.data[0]['rank'], 1)
        self.assertEqual(resp.data[1]['rank'], 2)

    def test_user_entries_detail(self):
        resp = self.client.get(f'/api/v1/leaders/{self.user1.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_entries'], 2)
        self.assertEqual(resp.data['user']['username'], 'topuser')
