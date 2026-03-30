from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Video
import os
import shutil
import django_rq
from .tasks import convert_to_hls, create_video_thumbnail


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    print('Video wurde gespeichert:', instance.title)
    if created:
        queue = django_rq.get_queue('default')
        queue.enqueue(create_video_thumbnail, instance.file.path, instance.thumbnail, second=1)
        queue.enqueue(convert_to_hls, instance.file.path)

        print(f"Video '{instance.title}' wurde zur HLS-Konvertierung in die Queue eingereiht.")


@receiver(post_delete, sender=Video)
def auto_delete_video_on_delete(sender, instance, **kwargs):
    print('Video wurde gelöscht:', instance.title)

    if instance.file:
        original = instance.file.path
        base, _ = os.path.splitext(original)
        if os.path.isfile(original):
            os.remove(original)
        if os.path.isdir(base):
            shutil.rmtree(base)
            