import os
import tempfile

from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework_simplejwt.tokens import RefreshToken

from unittest.mock import patch
from videoflix_app.models import Video

VIDEO_LIST_URL = reverse('video_list')
VIDEO_UPLOAD_URL = reverse('video_upload')


def create_user(email='user@example.com', password='Pass123!', is_staff=False):
    """Creates and returns an active user. Optionally grants staff privileges."""
    
    user = User.objects.create_user(username=email, email=email, password=password, is_staff=is_staff)
    user.is_active = True
    user.save()
    return user


def auth_header(user):
    """Returns a JWT Authorization header dict for the given user."""
    
    token = RefreshToken.for_user(user).access_token
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


def create_video(title='Test Video'):
    """Creates and returns a Video instance with a dummy file upload."""
    
    dummy_file = SimpleUploadedFile('test.mp4', b'videodata', content_type='video/mp4')
    return Video.objects.create(
        title=title,
        description='A test video.',
        category='Action',
        file=dummy_file,
    )


class VideoListTests(TestCase):
    """Tests for the video list endpoint including authentication and response structure."""

    def test_unauthenticated_returns_401(self):
        response = self.client.get(VIDEO_LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        user = create_user()
        response = self.client.get(VIDEO_LIST_URL, **auth_header(user))
        self.assertEqual(response.status_code, 200)

    def test_returns_list_of_videos(self):
        user = create_user()
        create_video('Movie A')
        create_video('Movie B')
        response = self.client.get(VIDEO_LIST_URL, **auth_header(user))
        self.assertEqual(len(response.json()), 2)

    def test_response_contains_expected_fields(self):
        user = create_user()
        create_video()
        response = self.client.get(VIDEO_LIST_URL, **auth_header(user))
        video = response.json()[0]
        for field in ['id', 'title', 'description', 'category', 'created_at', 'thumbnail_url']:
            self.assertIn(field, video)


class VideoUploadTests(TestCase):
    """Tests for the video upload endpoint including permission checks for staff and regular users."""

    @patch('videoflix_app.signals.django_rq.get_queue')
    def test_staff_can_upload_video(self, mock_queue):
        staff = create_user(email='staff@example.com', is_staff=True)
        dummy_file = SimpleUploadedFile('upload.mp4', b'videodata', content_type='video/mp4')
        response = self.client.post(VIDEO_UPLOAD_URL, {
            'title': 'New Video',
            'description': 'Desc',
            'category': 'Drama',
            'file': dummy_file,
        }, **auth_header(staff))
        self.assertEqual(response.status_code, 201)

    @patch('videoflix_app.signals.django_rq.get_queue')
    def test_upload_creates_video_in_db(self, mock_queue):
        staff = create_user(email='staff@example.com', is_staff=True)
        dummy_file = SimpleUploadedFile('upload.mp4', b'videodata', content_type='video/mp4')
        self.client.post(VIDEO_UPLOAD_URL, {
            'title': 'New Video',
            'description': 'Desc',
            'category': 'Drama',
            'file': dummy_file,
        }, **auth_header(staff))
        self.assertTrue(Video.objects.filter(title='New Video').exists())

    def test_regular_user_cannot_upload(self):
        user = create_user()
        dummy_file = SimpleUploadedFile('upload.mp4', b'videodata', content_type='video/mp4')
        response = self.client.post(VIDEO_UPLOAD_URL, {
            'title': 'New Video',
            'description': 'Desc',
            'category': 'Drama',
            'file': dummy_file,
        }, **auth_header(user))
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_cannot_upload(self):
        dummy_file = SimpleUploadedFile('upload.mp4', b'videodata', content_type='video/mp4')
        response = self.client.post(VIDEO_UPLOAD_URL, {
            'title': 'New Video',
            'description': 'Desc',
            'category': 'Drama',
            'file': dummy_file,
        })
        self.assertEqual(response.status_code, 401)


class HLSManifestTests(TestCase):
    """
    Tests for the HLS manifest endpoint.
    Creates a real manifest file on disk in setUp and cleans it up in tearDown.
    """

    def setUp(self):
        self.user = create_user()
        self.video = create_video()
        base, _ = os.path.splitext(self.video.file.path)
        self.manifest_dir = os.path.join(base, '720p')
        os.makedirs(self.manifest_dir, exist_ok=True)
        self.manifest_path = os.path.join(self.manifest_dir, 'index.m3u8')
        with open(self.manifest_path, 'w') as f:
            f.write('#EXTM3U\n#EXT-X-VERSION:3\n')

    def tearDown(self):
        import shutil
        base, _ = os.path.splitext(self.video.file.path)
        if os.path.isdir(base):
            shutil.rmtree(base)
        if self.video.file and os.path.isfile(self.video.file.path):
            os.remove(self.video.file.path)

    def test_valid_manifest_returns_200(self):
        url = reverse('hls_manifest', kwargs={'movie_id': self.video.pk, 'resolution': '720p'})
        response = self.client.get(url, **auth_header(self.user))
        self.assertEqual(response.status_code, 200)

    def test_manifest_content_type(self):
        url = reverse('hls_manifest', kwargs={'movie_id': self.video.pk, 'resolution': '720p'})
        response = self.client.get(url, **auth_header(self.user))
        self.assertIn('mpegurl', response['Content-Type'])

    def test_nonexistent_video_returns_404(self):
        url = reverse('hls_manifest', kwargs={'movie_id': 9999, 'resolution': '720p'})
        response = self.client.get(url, **auth_header(self.user))
        self.assertEqual(response.status_code, 404)

    def test_invalid_resolution_returns_404(self):
        url = reverse('hls_manifest', kwargs={'movie_id': self.video.pk, 'resolution': '360p'})
        response = self.client.get(url, **auth_header(self.user))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        url = reverse('hls_manifest', kwargs={'movie_id': self.video.pk, 'resolution': '720p'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
