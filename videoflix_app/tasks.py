import subprocess
import os
from django.core.files.base import ContentFile


def create_video_thumbnail(source, thumbnail_field, second=1):
    base, _ = os.path.splitext(os.path.basename(source))
    thumbnail_filename = f"{base}_thumbnail.jpg"
    thumbnail_path = os.path.join(os.path.dirname(source), thumbnail_filename)
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(second),
        '-i', source,
        '-frames:v', '1',
        '-q:v', '2',
        thumbnail_path
    ]
    subprocess.run(cmd, check=True)
    with open(thumbnail_path, 'rb') as f:
        thumbnail_field.save(thumbnail_filename, ContentFile(f.read()), save=True)
    os.remove(thumbnail_path)


def convert_480p(source):
    base, ext = os.path.splitext(source)
    target = f"{base}_480p{ext}"
    cmd = ['ffmpeg', '-i', source, '-s', 'hd480', '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', '-strict', '-2', target]
    subprocess.run(cmd, check=True)
    
def convert_720p(source):
    base, ext = os.path.splitext(source)
    target = f"{base}_720p{ext}"
    cmd = ['ffmpeg', '-i', source, '-s', 'hd720', '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', '-strict', '-2', target]
    subprocess.run(cmd, check=True)
    
def convert_1080p(source):
    base, ext = os.path.splitext(source)
    target = f"{base}_1080p{ext}"
    cmd = ['ffmpeg', '-i', source, '-s', 'hd1080', '-c:v', 'libx264', '-crf', '23', '-c:a', 'aac', '-strict', '-2', target]
    subprocess.run(cmd, check=True)
    