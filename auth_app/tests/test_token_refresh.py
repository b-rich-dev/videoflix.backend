from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User

LOGIN_URL = reverse('login')
REFRESH_URL = reverse('token_refresh')


def create_active_user(email='refresh@example.com', password='StrongPass123!'):
    """Creates and returns an active user with the given email and password."""
    
    user = User.objects.create_user(username=email, email=email, password=password)
    user.is_active = True
    user.save()
    return user


class TokenRefreshSuccessTests(TestCase):
    """Tests for successful token refresh using a valid refresh cookie."""

    def setUp(self):
        create_active_user()
        self.client.post(LOGIN_URL, {
            'email': 'refresh@example.com',
            'password': 'StrongPass123!',
        }, content_type='application/json', secure=True)

    def test_refresh_returns_200(self):
        response = self.client.post(REFRESH_URL, secure=True)
        self.assertEqual(response.status_code, 200)

    def test_refresh_sets_new_access_cookie(self):
        old_access = self.client.cookies.get('access').value
        self.client.post(REFRESH_URL, secure=True)
        new_access = self.client.cookies.get('access').value
        self.assertNotEqual(old_access, new_access)

    def test_refresh_response_contains_detail_and_access(self):
        response = self.client.post(REFRESH_URL, secure=True)
        data = response.json()
        self.assertIn('detail', data)
        self.assertIn('access', data)


class TokenRefreshFailureTests(TestCase):
    """Tests for token refresh failure cases such as missing or invalid refresh cookies."""

    def test_refresh_without_cookie_returns_400(self):
        response = self.client.post(REFRESH_URL, secure=True)
        self.assertEqual(response.status_code, 400)

    def test_refresh_with_invalid_cookie_returns_401(self):
        self.client.cookies['refresh'] = 'invalid.token.value'
        response = self.client.post(REFRESH_URL, secure=True)
        self.assertEqual(response.status_code, 401)
