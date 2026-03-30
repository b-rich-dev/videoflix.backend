from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from auth_app.api.tokens import generate_token


def create_inactive_user(email='activate@example.com', password='StrongPass123!'):
    user = User.objects.create_user(username=email, email=email, password=password)
    user.is_active = False
    user.save()
    return user


def activation_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = generate_token.make_token(user)
    return reverse('activate', kwargs={'uidb64': uid, 'token': token})


class ActivationSuccessTests(TestCase):

    def test_valid_link_returns_200(self):
        user = create_inactive_user()
        response = self.client.get(activation_url(user))
        self.assertEqual(response.status_code, 200)

    def test_valid_link_activates_user(self):
        user = create_inactive_user()
        self.client.get(activation_url(user))
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_valid_link_response_contains_message(self):
        user = create_inactive_user()
        response = self.client.get(activation_url(user))
        self.assertIn('message', response.json())


class ActivationFailureTests(TestCase):

    def test_invalid_token_returns_400(self):
        user = create_inactive_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = reverse('activate', kwargs={'uidb64': uid, 'token': 'invalid-token'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_invalid_uid_returns_400(self):
        url = reverse('activate', kwargs={'uidb64': 'invaliduid', 'token': 'sometoken'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_already_activated_user_returns_400(self):
        user = create_inactive_user()
        url = activation_url(user)
        self.client.get(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_invalid_token_does_not_activate_user(self):
        user = create_inactive_user()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        url = reverse('activate', kwargs={'uidb64': uid, 'token': 'invalid-token'})
        self.client.get(url)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
