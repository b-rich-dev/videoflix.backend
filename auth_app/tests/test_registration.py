from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch


REGISTER_URL = reverse('register')

VALID_PAYLOAD = {
    'email': 'test@example.com',
    'password': 'StrongPass123!',
    'confirmed_password': 'StrongPass123!',
}


class RegistrationSuccessTests(TestCase):

    @patch('auth_app.api.views.send_mail')
    def test_registration_returns_201(self, mock_mail):
        response = self.client.post(REGISTER_URL, VALID_PAYLOAD, content_type='application/json')
        self.assertEqual(response.status_code, 201)

    @patch('auth_app.api.views.send_mail')
    def test_registration_creates_user(self, mock_mail):
        self.client.post(REGISTER_URL, VALID_PAYLOAD, content_type='application/json')
        self.assertTrue(User.objects.filter(email=VALID_PAYLOAD['email']).exists())

    @patch('auth_app.api.views.send_mail')
    def test_user_is_inactive_after_registration(self, mock_mail):
        self.client.post(REGISTER_URL, VALID_PAYLOAD, content_type='application/json')
        user = User.objects.get(email=VALID_PAYLOAD['email'])
        self.assertFalse(user.is_active)

    @patch('auth_app.api.views.send_mail')
    def test_username_equals_email(self, mock_mail):
        self.client.post(REGISTER_URL, VALID_PAYLOAD, content_type='application/json')
        user = User.objects.get(email=VALID_PAYLOAD['email'])
        self.assertEqual(user.username, VALID_PAYLOAD['email'])

    @patch('auth_app.api.views.send_mail')
    def test_activation_email_is_sent(self, mock_mail):
        self.client.post(REGISTER_URL, VALID_PAYLOAD, content_type='application/json')
        mock_mail.assert_called_once()

    @patch('auth_app.api.views.send_mail')
    def test_response_contains_email_and_token(self, mock_mail):
        response = self.client.post(REGISTER_URL, VALID_PAYLOAD, content_type='application/json')
        data = response.json()
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], VALID_PAYLOAD['email'])
        self.assertIn('token', data)


class RegistrationValidationTests(TestCase):

    def test_missing_email_returns_400(self):
        payload = {'password': 'StrongPass123!', 'confirmed_password': 'StrongPass123!'}
        response = self.client.post(REGISTER_URL, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_password_returns_400(self):
        payload = {'email': 'test@example.com', 'confirmed_password': 'StrongPass123!'}
        response = self.client.post(REGISTER_URL, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_passwords_do_not_match_returns_400(self):
        payload = {
            'email': 'test@example.com',
            'password': 'StrongPass123!',
            'confirmed_password': 'WrongPass!',
        }
        response = self.client.post(REGISTER_URL, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    @patch('auth_app.api.views.send_mail')
    def test_duplicate_email_returns_400(self, mock_mail):
        self.client.post(REGISTER_URL, VALID_PAYLOAD, content_type='application/json')
        response = self.client.post(REGISTER_URL, VALID_PAYLOAD, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_email_format_returns_400(self):
        payload = {**VALID_PAYLOAD, 'email': 'not-an-email'}
        response = self.client.post(REGISTER_URL, payload, content_type='application/json')
        self.assertEqual(response.status_code, 400)
