import os

from django.http import HttpResponse, Http404

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from videoflix_app.models import Video

from .serializers import VideoUploadSerializer
from .permissions import IsAdminOrStaff


class VideoUploadView(generics.CreateAPIView):
    """
    API view for uploading new videos.
    Requires JWT authentication. Only staff and superusers may upload.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer


class VideoListView(generics.ListAPIView):
    """
    API view for listing all available videos.
    Requires JWT authentication.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer


VALID_RESOLUTIONS = {'480p', '720p', '1080p'}


class HLSManifestView(APIView):
    """
    API view for serving the HLS index playlist for a specific video and resolution.
    Requires JWT authentication.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """
        Returns the index.m3u8 playlist for the given video and resolution.
        Raises 404 if the resolution is invalid, the video does not exist,
        or the manifest file has not been generated yet.
        """
        
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
       
       
class HLSSegmentView(APIView):
    """
    API view for serving individual HLS transport stream segments (.ts files).
    Requires JWT authentication.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """
        Returns the binary content of the requested .ts segment file.
        Raises 404 if the resolution is invalid, the video does not exist,
        or the segment file is not found.
        """
        
        if resolution not in VALID_RESOLUTIONS:
            raise Http404('Invalid resolution.')

        try:
            video = Video.objects.get(pk=movie_id)
        except Video.DoesNotExist:
            raise Http404('Video not found.')

        base, _ = os.path.splitext(video.file.path)
        segment_path = os.path.join(base, resolution, segment)

        if not os.path.isfile(segment_path):
            raise Http404('HLS segment not found.')

        with open(segment_path, 'rb') as f:
            content = f.read()

        return HttpResponse(content, content_type='video/MP2T') 
    