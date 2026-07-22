from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from apps.content.models import ContentEntry
from apps.scripts.models import Script
from django.utils import timezone

User = get_user_model()


class ReportAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reportuser', password='test1234',
            full_name='Report User', office_id='REP001',
            designation='User', phone='01711111111',
            blood_group='A+',
        )
        self.client.force_authenticate(user=self.user)

    def test_content_report_endpoint(self):
        ContentEntry.objects.create(
            entry_date=timezone.now().date(),
            entry_time=timezone.now().time(),
            slug='report-entry', headline='Report Entry',
            member=self.user, links={'fb': 'https://fb.com/report'},
        )
        resp = self.client.get('/api/v1/reports/content-report/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(resp['Content-Type'], ['application/pdf', 'text/html; charset=utf-8'])

    def test_script_pdf_endpoint(self):
        script = Script.objects.create(
            script_date=timezone.now().date(),
            headline='PDF Script',
            source='social',
            writer=self.user,
            body='PDF body content',
        )
        resp = self.client.get(f'/api/v1/reports/script-pdf/{script.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(resp['Content-Type'], ['application/pdf', 'text/html; charset=utf-8'])
