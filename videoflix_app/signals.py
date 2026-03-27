from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Video
import os
import django_rq
from .tasks import convert_480p, convert_720p, convert_1080p, create_video_thumbnail


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    print('Video wurde gespeichert:', instance.title)
    if created:
        queue = django_rq.get_queue('default')
        queue.enqueue(create_video_thumbnail, instance.file.path, instance.thumbnail, second=1)
        queue.enqueue(convert_480p, instance.file.path)
        queue.enqueue(convert_720p, instance.file.path)
        queue.enqueue(convert_1080p, instance.file.path)
        
        print(f"Video '{instance.title}' wurde zur Konvertierung in die Queue eingereiht.")
        

@receiver(post_delete, sender=Video)
def auto_delete_video_on_delete(sender, instance, **kwargs):
    print('Video wurde gelöscht:', instance.title)

    if instance.file:
        original = instance.file.path
        base, ext = os.path.splitext(original)
        files_to_delete = [
            original,
            f"{base}_480p{ext}",
            f"{base}_720p{ext}",
            f"{base}_1080p{ext}",
        ]
        for path in files_to_delete:
            if os.path.isfile(path):
                os.remove(path)
            