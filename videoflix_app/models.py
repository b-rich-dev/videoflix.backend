from django.db import models

class Video(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    category = models.CharField(max_length=100)
    file=models.FileField(upload_to='videos/')

    def __str__(self):
        return self.title
