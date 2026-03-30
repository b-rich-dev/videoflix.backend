import os
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.http import HttpResponse, Http404
from videoflix_app.models import Video
from .serializers import VideoUploadSerializer
from .permissions import IsAdminOrStaff


class VideoUploadView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer


class VideoListView(generics.ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer


VALID_RESOLUTIONS = {'480p', '720p', '1080p'}


class HLSManifestView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        if resolution not in VALID_RESOLUTIONS:
            raise Http404('Invalid resolution.')

        try:
            video = Video.objects.get(pk=movie_id)
        except Video.DoesNotExist:
            raise Http404('Video not found.')

        base, _ = os.path.splitext(video.file.path)
        manifest_path = os.path.join(base, resolution, 'index.m3u8')

        if not os.path.isfile(manifest_path):
            raise Http404('HLS manifest not found.')

        with open(manifest_path, 'r') as f:
            content = f.read()

        return HttpResponse(content, content_type='application/vnd.apple.mpegurl')
        