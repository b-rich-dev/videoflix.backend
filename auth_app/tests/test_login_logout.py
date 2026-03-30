from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User


LOGIN_URL = reverse('login')
LOGOUT_URL = reverse('logout')


def create_active_user(email='user@example.com', password='StrongPass123!'):
    """Creates and returns an active user with the given email and password."""
    
    user = User.objects.create_user(username=email, email=email, password=password)
    user.is_active = True
    user.save()
    return user


class LoginSuccessTests(TestCase):
    """Tests for successful login with valid credentials."""

    def setUp(self):
        self.user = create_active_user()

    def test_login_returns_200(self):
        response = self.client.post(LOGIN_URL, {
            'email': 'user@example.com',
            'password': 'StrongPass123!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_login_sets_access_cookie(self):
        self.client.post(LOGIN_URL, {
            'email': 'user@example.com',
            'password': 'StrongPass123!',
        }, content_type='application/json')
        self.assertIn('access', self.client.cookies)

    def test_login_sets_refresh_cookie(self):
        self.client.post(LOGIN_URL, {
            'email': 'user@example.com',
            'password': 'StrongPass123!',
        }, content_type='application/json')
        self.assertIn('refresh', self.client.cookies)

    def test_login_response_contains_detail_and_user(self):
        response = self.client.post(LOGIN_URL, {
            'email': 'user@example.com',
            'password': 'StrongPass123!',
        }, content_type='application/json')
        data = response.json()
        self.assertIn('detail', data)
        self.assertIn('user', data)


class LoginFailureTests(TestCase):
    """Tests for login failure cases such as wrong credentials, unknown email, or inactive accounts."""

    def setUp(self):
        self.user = create_active_user()

    def test_wrong_password_returns_401(self):
        response = self.client.post(LOGIN_URL, {
            'email': 'user@example.com',
            'password': 'WrongPass!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_unknown_email_returns_401(self):
        response = self.client.post(LOGIN_URL, {
            'email': 'nobody@example.com',
            'password': 'StrongPass123!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_inactive_user_cannot_login(self):
        inactive = User.objects.create_user(
            username='inactive@example.com',
            email='inactive@example.com',
            password='StrongPass123!',
        )
        inactive.is_active = False
        inactive.save()
        response = self.client.post(LOGIN_URL, {
            'email': 'inactive@example.com',
            'password': 'StrongPass123!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_missing_credentials_returns_400(self):
        response = self.client.post(LOGIN_URL, {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class LogoutTests(TestCase):
    """Tests for logout behaviour including cookie deletion and unauthenticated access."""

    def setUp(self):
        self.user = create_active_user()
        self.client.post(LOGIN_URL, {
            'email': 'user@example.com',
            'password': 'StrongPass123!',
        }, content_type='application/json', secure=True)

    def test_logout_returns_200(self):
        response = self.client.post(LOGOUT_URL, secure=True)
        self.assertEqual(response.status_code, 200)

    def test_logout_deletes_access_cookie(self):
        self.client.post(LOGOUT_URL, secure=True)
        self.assertEqual(self.client.cookies.get('access').value, '')

    def test_logout_deletes_refresh_cookie(self):
        self.client.post(LOGOUT_URL, secure=True)
        self.assertEqual(self.client.cookies.get('refresh').value, '')

    def test_logout_without_auth_returns_401(self):
        fresh_client = self.client_class()
        response = fresh_client.post(LOGOUT_URL, secure=True)
        self.assertEqual(response.status_code, 401)
