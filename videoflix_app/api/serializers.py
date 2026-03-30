from rest_framework import serializers
from videoflix_app.models import Video

class VideoUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model.
    Exposes video metadata for list and detail responses.
    The file field is write-only and used only during upload.
    The thumbnail_url field returns an absolute URL to the video thumbnail.
    """

    thumbnail_url = serializers.SerializerMethodField()

    def get_thumbnail_url(self, obj):
        """Returns the absolute URL of the video thumbnail, or None if not available."""
        
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category', 'file']
        read_only_fields = ['id', 'created_at', 'thumbnail_url']
        extra_kwargs = {'file': {'write_only': True}}
        