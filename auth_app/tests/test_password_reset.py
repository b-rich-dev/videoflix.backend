from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from unittest.mock import patch
from auth_app.api.tokens import password_reset_token

PASSWORD_RESET_URL = reverse('password_reset')
LOGIN_URL = reverse('login')


def create_active_user(email='reset@example.com', password='OldPass123!'):
    user = User.objects.create_user(username=email, email=email, password=password)
    user.is_active = True
    user.save()
    return user


def confirm_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = password_reset_token.make_token(user)
    return reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})


class PasswordResetRequestTests(TestCase):

    @patch('auth_app.api.views.send_mail')
    def test_known_email_returns_200(self, mock_mail):
        create_active_user()
        response = self.client.post(PASSWORD_RESET_URL, {'email': 'reset@example.com'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    @patch('auth_app.api.views.send_mail')
    def test_known_email_sends_mail(self, mock_mail):
        create_active_user()
        self.client.post(PASSWORD_RESET_URL, {'email': 'reset@example.com'}, content_type='application/json')
        mock_mail.assert_called_once()

    def test_unknown_email_returns_200(self):
        response = self.client.post(PASSWORD_RESET_URL, {'email': 'nobody@example.com'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_missing_email_returns_400(self):
        response = self.client.post(PASSWORD_RESET_URL, {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)


class PasswordResetConfirmTests(TestCase):

    def test_valid_token_returns_200(self):
        user = create_active_user()
        response = self.client.post(confirm_url(user), {
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_valid_token_changes_password(self):
        user = create_active_user()
        self.client.post(confirm_url(user), {
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, content_type='application/json')
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPass123!'))

    def test_old_password_no_longer_works_after_reset(self):
        user = create_active_user()
        self.client.post(confirm_url(user), {
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, content_type='application/json')
        response = self.client.post(LOGIN_URL, {
            'email': 'reset@example.com',
            'password': 'OldPass123!',
        }, content_type='application/json', secure=True)
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_returns_400(self):
        user = create_active_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': 'invalid-token'})
        response = self.client.post(url, {
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_invalid_uid_returns_400(self):
        url = reverse('password_reset_confirm', kwargs={'uidb64': 'invaliduid', 'token': 'sometoken'})
        response = self.client.post(url, {
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_passwords_do_not_match_returns_400(self):
        user = create_active_user()
        response = self.client.post(confirm_url(user), {
            'new_password': 'NewPass123!',
            'confirm_password': 'Different123!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_passwords_returns_400(self):
        user = create_active_user()
        response = self.client.post(confirm_url(user), {}, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_inactive_user_cannot_reset_password(self):
        user = User.objects.create_user(username='inactive@example.com', email='inactive@example.com', password='OldPass123!')
        user.is_active = False
        user.save()
        response = self.client.post(confirm_url(user), {
            'new_password': 'NewPass123!',
            'confirm_password': 'NewPass123!',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 400)
