from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for the Video model."""

    list_display = ('title', 'category', 'created_at')
    search_fields = ('title', 'category')
    exclude = ('thumbnail',)
