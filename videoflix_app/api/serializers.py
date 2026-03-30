from rest_framework import serializers
from videoflix_app.models import Video
import os

class VideoUploadSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']
        read_only_fields = ['id', 'created_at', 'thumbnail_url']
        
        
class VideoHLSSerializer(serializers.ModelSerializer):
    hls_url = serializers.SerializerMethodField()

    def get_hls_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            base_url, _ = os.path.splitext(obj.file.url)
            return request.build_absolute_uri(f"{base_url}/master.m3u8")
        return None

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'hls_url']
        read_only_fields = ['id', 'created_at', 'hls_url']
        