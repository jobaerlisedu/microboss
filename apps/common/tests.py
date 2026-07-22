from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from apps.common.permissions import IsAdmin, IsOwnerOrAdmin
from apps.common.pagination import StandardPagination
from apps.common.models import BaseModel

User = get_user_model()


class TestPermissions(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123',
            full_name='Admin', office_id='ADM001',
            designation='Admin', phone='01700000000',
            blood_group='A+', is_admin=True,
        )
        self.user = User.objects.create_user(
            username='user1', password='pass1234',
            full_name='User One', office_id='USR001',
            designation='User', phone='01700000001',
            blood_group='B+',
        )

    def test_is_admin_has_permission_admin(self):
        perm = IsAdmin()
        request = type('obj', (object,), {'user': self.admin})()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_admin_has_permission_regular(self):
        perm = IsAdmin()
        request = type('obj', (object,), {'user': self.user})()
        self.assertFalse(perm.has_permission(request, None))

    def test_is_admin_has_permission_anon(self):
        perm = IsAdmin()
        request = type('obj', (object,), {'user': type('anon', (object,), {'is_authenticated': False})()})
        self.assertFalse(perm.has_permission(request, None))

    def test_is_owner_or_admin_has_permission(self):
        perm = IsOwnerOrAdmin()
        request = type('obj', (object,), {'user': self.user})()
        self.assertTrue(perm.has_permission(request, None))

    def test_is_owner_or_admin_admin_can_access_any(self):
        perm = IsOwnerOrAdmin()
        request = type('obj', (object,), {'user': self.admin})()
        obj = type('obj', (object,), {'member_id': 'some-other-id'})()
        self.assertTrue(perm.has_object_permission(request, None, obj))

    def test_is_owner_or_admin_owner_can_access(self):
        perm = IsOwnerOrAdmin()
        request = type('obj', (object,), {'user': self.user})()
        obj = type('obj', (object,), {'member_id': str(self.user.id)})()
        self.assertTrue(perm.has_object_permission(request, None, obj))

    def test_is_owner_or_admin_stranger_cannot_access(self):
        perm = IsOwnerOrAdmin()
        request = type('obj', (object,), {'user': self.user})()
        obj = type('obj', (object,), {'member_id': 'some-other-id'})()
        self.assertFalse(perm.has_object_permission(request, None, obj))

    def test_is_owner_or_admin_writer_can_access(self):
        perm = IsOwnerOrAdmin()
        request = type('obj', (object,), {'user': self.user})()
        obj = type('obj', (object,), {'writer_id': str(self.user.id)})()
        self.assertTrue(perm.has_object_permission(request, None, obj))


class TestPagination(TestCase):
    def test_default_page_size(self):
        p = StandardPagination()
        self.assertEqual(p.page_size, 50)
        self.assertEqual(p.page_size_query_param, 'page_size')
        self.assertEqual(p.max_page_size, 500)


class TestBengaliFilters(TestCase):
    def test_bn_date_filter(self):
        from django.template import Template, Context
        import datetime
        t = Template('{% load bengali_filters %}{{ dt|bn_date }}')
        rendered = t.render(Context({'dt': datetime.date(2024, 3, 15)}))
        self.assertIn('মার্চ', rendered)
        self.assertIn('15', rendered)

    def test_bn_number_filter(self):
        from django.template import Template, Context
        t = Template('{% load bengali_filters %}{{ 1234|bn_number }}')
        rendered = t.render(Context({}))
        self.assertIn('১২৩৪', rendered)

    def test_get_item_filter(self):
        from django.template import Template, Context
        t = Template('{% load bengali_filters %}{{ d|get_item:"key1" }}')
        rendered = t.render(Context({'d': {'key1': 'val1'}}))
        self.assertEqual('val1', rendered.strip())
