import os
import shutil
import django_rq

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from .models import Video
from .tasks import convert_to_hls, create_video_thumbnail


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    Signal handler triggered after a Video instance is saved.
    On creation, enqueues thumbnail generation and HLS conversion tasks
    into the default RQ queue.
    """

    if created:
        queue = django_rq.get_queue('default')
        queue.enqueue(create_video_thumbnail, instance.file.path, instance.thumbnail, second=1)
        queue.enqueue(convert_to_hls, instance.file.path)


@receiver(post_delete, sender=Video)
def auto_delete_video_on_delete(sender, instance, **kwargs):
    """
    Signal handler triggered after a Video instance is deleted.
    Removes the original video file and the associated HLS output directory from disk.
    """

    if instance.file:
        original = instance.file.path
        base, _ = os.path.splitext(original)
        if os.path.isfile(original):
            os.remove(original)
        if os.path.isdir(base):
            shutil.rmtree(base)
            