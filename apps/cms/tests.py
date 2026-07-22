import json
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.content.models import ContentEntry
from apps.sponsors.models import Sponsor
from apps.assignments.models import Assignment

User = get_user_model()


class CMSSaveEntryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='entrytest', password='test1234',
            full_name='Entry Tester', office_id='ENT001',
            designation='Reporter', phone='01711111111',
            blood_group='O+',
        )
        self.client.login(username='entrytest', password='test1234')
        self.url = '/cms/entries/save/'
        self.today = date.today().isoformat()

    def test_save_entry_success(self):
        resp = self.client.post(self.url, {
            'entry_date': self.today,
            'entry_time': '10:30',
            'slug': 'test-entry-1',
            'headline': 'Test Headline',
            'links_fb': 'https://facebook.com/test',
            'comment': 'Test comment',
            'language': 'bn',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('HX-Trigger', resp)
        trigger = json.loads(resp['HX-Trigger'])
        self.assertEqual(trigger['cms-toast']['type'], 'success')
        self.assertEqual(ContentEntry.objects.count(), 1)
        entry = ContentEntry.objects.first()
        self.assertEqual(entry.slug, 'test-entry-1')
        self.assertEqual(entry.headline, 'Test Headline')
        self.assertEqual(entry.language, 'bn')
        self.assertEqual(entry.member, self.user)

    def test_save_entry_empty_links_fails(self):
        resp = self.client.post(self.url, {
            'entry_date': self.today,
            'entry_time': '10:30',
            'slug': 'test-entry-2',
            'headline': 'No Links',
        })
        self.assertEqual(resp.status_code, 200)
        trigger = json.loads(resp['HX-Trigger'])
        self.assertEqual(trigger['cms-toast']['type'], 'error')
        self.assertEqual(ContentEntry.objects.count(), 0)

    def test_save_entry_duplicate_slug_date_fails(self):
        ContentEntry.objects.create(
            entry_date=self.today, entry_time='10:00',
            slug='dup-slug', headline='First',
            member=self.user, links={'fb': 'https://fb.com/1'},
            created_by=self.user,
        )
        resp = self.client.post(self.url, {
            'entry_date': self.today,
            'entry_time': '11:00',
            'slug': 'dup-slug',
            'headline': 'Duplicate',
            'links_fb': 'https://facebook.com/dup',
        })
        self.assertEqual(resp.status_code, 200)
        trigger = json.loads(resp['HX-Trigger'])
        self.assertEqual(trigger['cms-toast']['type'], 'error')
        self.assertIn('duplicate', trigger['cms-toast']['message'].lower())

    def test_save_entry_updates_assignment_status(self):
        assignment = Assignment.objects.create(
            assign_date=self.today, caption='Test',
            status='Pending', member=self.user,
            created_by=self.user, reporter='Reporter',
        )
        resp = self.client.post(self.url, {
            'entry_date': self.today,
            'entry_time': '12:00',
            'slug': 'assigned-entry',
            'headline': 'Assigned',
            'links_fb': 'https://facebook.com/assign',
            'assignment_id': str(assignment.id),
        })
        self.assertEqual(resp.status_code, 200)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, 'Done')

    def test_save_entry_english_language(self):
        resp = self.client.post(self.url, {
            'entry_date': self.today,
            'entry_time': '14:00',
            'slug': 'english-entry',
            'headline': 'English Headline',
            'links_yt': 'https://youtube.com/watch?v=test',
            'language': 'en',
        })
        self.assertEqual(resp.status_code, 200)
        entry = ContentEntry.objects.get(slug='english-entry')
        self.assertEqual(entry.language, 'en')


class CMSSaveSponsorTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='sponsoradmin', password='test1234',
            full_name='Sponsor Admin', office_id='SPO001',
            designation='Admin', phone='01722222222',
            blood_group='A+', is_admin=True,
        )
        self.client.login(username='sponsoradmin', password='test1234')
        self.url = '/cms/sponsors/save/'

    def test_save_sponsor_success(self):
        resp = self.client.post(self.url, {
            'name': 'Test Sponsor',
            'daily_quota': '5',
            'total_quota': '100',
            'start_date': date.today().isoformat(),
            'end_date': date.today().isoformat(),
            'content_type': 'video',
            'has_doggy': 'on',
        })
        self.assertEqual(resp.status_code, 200)
        trigger = json.loads(resp['HX-Trigger'])
        self.assertEqual(trigger['cms-toast']['type'], 'success')
        self.assertEqual(Sponsor.objects.count(), 1)
        sponsor = Sponsor.objects.first()
        self.assertEqual(sponsor.name, 'Test Sponsor')
        self.assertTrue(sponsor.has_doggy)
        self.assertFalse(sponsor.has_popup)

    def test_save_sponsor_missing_name_fails(self):
        resp = self.client.post(self.url, {
            'daily_quota': '5',
            'total_quota': '100',
        })
        self.assertEqual(resp.status_code, 200)
        trigger = json.loads(resp['HX-Trigger'])
        self.assertEqual(trigger['cms-toast']['type'], 'error')
        self.assertEqual(Sponsor.objects.count(), 0)


class CMSSaveAssignmentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='assigntest', password='test1234',
            full_name='Assign Tester', office_id='ASG001',
            designation='Reporter', phone='01733333333',
            blood_group='B+',
        )
        self.client.login(username='assigntest', password='test1234')
        self.url = '/cms/assignments/save/'
        self.today = date.today().isoformat()

    def test_save_assignment_success(self):
        resp = self.client.post(self.url, {
            'assign_date': self.today,
            'caption': 'Test assignment',
            'source_link': 'https://source.example.com',
            'district': 'Dhaka',
        })
        self.assertEqual(resp.status_code, 200)
        trigger = json.loads(resp['HX-Trigger'])
        self.assertEqual(trigger['cms-toast']['type'], 'success')
        self.assertEqual(Assignment.objects.count(), 1)
        assignment = Assignment.objects.first()
        self.assertEqual(assignment.caption, 'Test assignment')
        self.assertEqual(assignment.district, 'Dhaka')
        self.assertEqual(assignment.member, self.user)

    def test_save_assignment_future_date_fails(self):
        future = date(2099, 12, 31).isoformat()
        resp = self.client.post(self.url, {
            'assign_date': future,
            'caption': 'Future assignment',
        })
        self.assertEqual(resp.status_code, 200)
        trigger = json.loads(resp['HX-Trigger'])
        self.assertEqual(trigger['cms-toast']['type'], 'error')
        self.assertIn('future', trigger['cms-toast']['message'].lower())
        self.assertEqual(Assignment.objects.count(), 0)

    def test_save_assignment_with_reporter_user(self):
        reporter = User.objects.create_user(
            username='reporter1', password='test1234',
            full_name='Reporter One', office_id='REP001',
            designation='Reporter', phone='01744444444',
            blood_group='AB+',
        )
        resp = self.client.post(self.url, {
            'assign_date': self.today,
            'caption': 'With reporter',
            'reporter_user': str(reporter.id),
            'reporter': 'Custom Name',
        })
        self.assertEqual(resp.status_code, 200)
        assignment = Assignment.objects.first()
        self.assertEqual(assignment.reporter_user, reporter)
        self.assertEqual(assignment.reporter, 'Custom Name')
