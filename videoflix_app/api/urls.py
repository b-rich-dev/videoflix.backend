from django.urls import path
from .views import VideoUploadView, VideoListView, HLSManifestView

urlpatterns = [
    path('upload/', VideoUploadView.as_view(), name='video_upload'),
    path('video/', VideoListView.as_view(), name='video_list'),
    path('video/<int:pk>/', VideoListView.as_view(), name='video_detail'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', HLSManifestView.as_view(), name='hls_manifest'),
]