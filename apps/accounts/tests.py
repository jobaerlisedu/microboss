from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.accounts.models import UserSession

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='test1234',
            full_name='Test User', office_id='TST001',
            designation='Reporter', phone='01711111111',
            blood_group='O+', date_of_birth='1990-01-15',
        )

    def test_create_user(self):
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(str(self.user), 'Test User (testuser)')

    def test_create_admin(self):
        admin = User.objects.create_user(
            username='admin', password='admin123',
            full_name='Admin User', office_id='ADM001',
            designation='Admin', phone='01722222222',
            blood_group='A+', is_admin=True,
        )
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_founder)

    def test_create_founder(self):
        founder = User.objects.create_user(
            username='founder', password='found123',
            full_name='Founder', office_id='FND001',
            designation='Founder', phone='01733333333',
            blood_group='AB+', is_admin=True, is_founder=True,
        )
        self.assertTrue(founder.is_founder)

    def test_user_str(self):
        self.assertIn('Test User', str(self.user))
        self.assertIn('testuser', str(self.user))

    def test_user_verbose_names(self):
        meta = User._meta
        self.assertEqual(meta.verbose_name, 'ব্যবহারকারী')
        self.assertEqual(meta.verbose_name_plural, 'ব্যবহারকারীগণ')


class UserSessionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sessionuser', password='test1234',
            full_name='Session User', office_id='SES001',
            designation='User', phone='01744444444',
            blood_group='B+',
        )

    def test_create_session(self):
        session = UserSession.objects.create(
            user=self.user, ip_address='127.0.0.1',
            device_info='Test Browser', session_key='test-key-123',
        )
        self.assertEqual(UserSession.objects.count(), 1)
        self.assertTrue(session.is_active)
        self.assertIn('sessionuser', str(session))
        self.assertIn('127.0.0.1', str(session))

    def test_session_verbose_names(self):
        meta = UserSession._meta
        self.assertEqual(meta.verbose_name, 'সেশন')
        self.assertEqual(meta.verbose_name_plural, 'সেশনসমূহ')


class RegisterAPITest(APITestCase):
    def setUp(self):
        self.url = '/api/v1/auth/register/'
        self.valid_payload = {
            'username': 'newuser',
            'password': 'pass1234',
            'password2': 'pass1234',
            'full_name': 'New User',
            'office_id': 'NEW001',
            'designation': 'Reporter',
            'email': 'new@example.com',
            'phone': '01755555555',
            'blood_group': 'A+',
        }

    def test_register_success(self):
        resp = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', resp.data)
        self.assertIn('access', resp.data['tokens'])
        self.assertEqual(User.objects.count(), 1)

    def test_register_duplicate_username(self):
        User.objects.create_user(
            username='newuser', password='pass1234',
            full_name='Existing', office_id='EXI001',
            designation='User', phone='01766666666',
            blood_group='O+',
        )
        resp = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        payload = dict(self.valid_payload)
        payload['password2'] = 'different'
        resp = self.client.post(self.url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_first_user_is_admin_and_founder(self):
        resp = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.first()
        self.assertTrue(user.is_admin)
        self.assertTrue(user.is_founder)


class LoginAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser', password='login1234',
            full_name='Login User', office_id='LOG001',
            designation='User', phone='01777777777',
            blood_group='B+', email='loginuser@example.com',
        )
        self.url = '/api/v1/auth/login/'

    def test_login_by_username(self):
        resp = self.client.post(self.url, {
            'identifier': 'loginuser', 'password': 'login1234',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', resp.data)
        self.assertIn('session_id', resp.data)

    def test_login_by_email(self):
        resp = self.client.post(self.url, {
            'identifier': 'loginuser@example.com', 'password': 'login1234',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_by_office_id(self):
        resp = self.client.post(self.url, {
            'identifier': 'LOG001', 'password': 'login1234',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_wrong_password(self):
        resp = self.client.post(self.url, {
            'identifier': 'loginuser', 'password': 'wrongpass',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        resp = self.client.post(self.url, {
            'identifier': 'ghost', 'password': 'pass1234',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='resetuser', password='reset1234',
            full_name='Reset User', office_id='RST001',
            designation='User', phone='01788888888',
            blood_group='A+', email='reset@example.com',
        )
        self.request_url = '/api/v1/auth/password-reset/request/'
        self.verify_url = '/api/v1/auth/password-reset/verify/'
        self.confirm_url = '/api/v1/auth/password-reset/confirm/'

    def test_password_reset_request(self):
        resp = self.client.post(self.request_url, {
            'identifier': 'resetuser',
            'email': 'reset@example.com',
            'phone': '01788888888',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('otp_display', resp.data)

    def test_password_reset_request_wrong_info(self):
        resp = self.client.post(self.request_url, {
            'identifier': 'resetuser',
            'email': 'wrong@example.com',
            'phone': '01788888888',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_verify_otp(self):
        self.client.post(self.request_url, {
            'identifier': 'resetuser',
            'email': 'reset@example.com',
            'phone': '01788888888',
        }, format='json')
        session = self.client.session
        otp = session.get('reset_otp')
        self.assertIsNotNone(otp)
        resp = self.client.post(self.verify_url, {'otp': otp}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)

    def test_password_reset_verify_wrong_otp(self):
        self.client.post(self.request_url, {
            'identifier': 'resetuser',
            'email': 'reset@example.com',
            'phone': '01788888888',
        }, format='json')
        resp = self.client.post(self.verify_url, {'otp': '000000'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_full_flow(self):
        self.client.post(self.request_url, {
            'identifier': 'resetuser',
            'email': 'reset@example.com',
            'phone': '01788888888',
        }, format='json')
        session = self.client.session
        otp = session.get('reset_otp')
        self.client.post(self.verify_url, {'otp': otp}, format='json')
        resp = self.client.post(self.confirm_url, {
            'token': 'verified',
            'password': 'newpass123',
            'password2': 'newpass123',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))


class LogoutAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='logoutuser', password='logout1234',
            full_name='Logout User', office_id='LGT001',
            designation='User', phone='01799999999',
            blood_group='AB+',
        )
        self.client.force_authenticate(user=self.user)

    def test_logout_with_session_id(self):
        session = UserSession.objects.create(
            user=self.user, ip_address='127.0.0.1',
            session_key='logout-test-key',
        )
        resp = self.client.post('/api/v1/auth/logout/', {
            'session_id': str(session.id),
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertFalse(session.is_active)


class UserListAPITest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123',
            full_name='Admin User', office_id='ADM001',
            designation='Admin', phone='01700000000',
            blood_group='A+', is_admin=True, is_staff=True,
        )
        self.user = User.objects.create_user(
            username='regular', password='reg1234',
            full_name='Regular User', office_id='REG001',
            designation='User', phone='01711111111',
            blood_group='B+',
        )

    def test_user_list_admin_only(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v1/auth/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_user_list_denied_for_regular(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/v1/auth/users/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_list_denied_for_anon(self):
        resp = self.client.get('/api/v1/auth/users/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class AdminResetPasswordAPITest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123',
            full_name='Admin', office_id='ADM001',
            designation='Admin', phone='01700000000',
            blood_group='A+', is_admin=True, is_staff=True,
        )
        self.user = User.objects.create_user(
            username='target', password='oldpass123',
            full_name='Target User', office_id='TGT001',
            designation='User', phone='01722222222',
            blood_group='O+',
        )

    def test_admin_reset_password(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            f'/api/v1/auth/users/{self.user.id}/reset-password/',
            {'password': 'newadmin123'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newadmin123'))

    def test_admin_reset_password_too_short(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            f'/api/v1/auth/users/{self.user.id}/reset-password/',
            {'password': 'ab'}, format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ToggleAdminAPITest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin123',
            full_name='Admin', office_id='ADM001',
            designation='Admin', phone='01700000000',
            blood_group='A+', is_admin=True, is_staff=True,
        )
        self.user = User.objects.create_user(
            username='regular', password='reg1234',
            full_name='Regular', office_id='REG001',
            designation='User', phone='01733333333',
            blood_group='B+',
        )

    def test_toggle_admin(self):
        self.client.force_authenticate(user=self.admin)
        self.assertFalse(self.user.is_admin)
        resp = self.client.post(
            f'/api/v1/auth/users/{self.user.id}/toggle-admin/',
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_admin)


class UserSessionsAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sesuser', password='ses1234',
            full_name='Session User', office_id='SES001',
            designation='User', phone='01744444444',
            blood_group='A+',
        )
        self.client.force_authenticate(user=self.user)

    def test_get_own_sessions(self):
        UserSession.objects.create(
            user=self.user, ip_address='10.0.0.1',
            session_key='ses-key-1',
        )
        resp = self.client.get('/api/v1/auth/sessions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.data.get('results', resp.data)
        self.assertEqual(len(results), 1)
