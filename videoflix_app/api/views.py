from rest_framework import generics
from videoflix_app.models import Video
from .serializers import VideoUploadSerializer


class VideoUploadView(generics.ListCreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer


class VideoListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer
        