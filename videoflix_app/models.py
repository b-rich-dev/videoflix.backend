from django.db import models

class Video(models.Model):
    """
    Represents a video entry in the Videoflix platform.
    Stores metadata such as title, description and category, as well as
    the video file and an optional auto-generated thumbnail.
    HLS conversion output is stored alongside the video file on disk.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    category = models.CharField(max_length=100)
    file=models.FileField(upload_to='videos/')

    def __str__(self):
        return self.title
