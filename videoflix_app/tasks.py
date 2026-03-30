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


def convert_to_hls(source):
    """Konvertiert ein Video in das HLS-Format (480p, 720p, 1080p) und erstellt eine Master-Playlist."""
    base, _ = os.path.splitext(source)

    resolutions = [
        ('480p',  'hd480',  '854x480',   '1000000'),
        ('720p',  'hd720',  '1280x720',  '3000000'),
        ('1080p', 'hd1080', '1920x1080', '6000000'),
    ]

    for name, scale, resolution, bandwidth in resolutions:
        output_dir = os.path.join(base, name)
        os.makedirs(output_dir, exist_ok=True)
        playlist = os.path.join(output_dir, 'index.m3u8')
        segments = os.path.join(output_dir, 'segment_%03d.ts')
        cmd = [
            'ffmpeg', '-y',
            '-i', source,
            '-s', scale,
            '-c:v', 'libx264',
            '-crf', '23',
            '-c:a', 'aac',
            '-hls_time', '10',
            '-hls_list_size', '0',
            '-hls_segment_filename', segments,
            playlist,
        ]
        subprocess.run(cmd, check=True)

    master_path = os.path.join(base, 'master.m3u8')
    with open(master_path, 'w') as f:
        f.write('#EXTM3U\n')
        f.write('#EXT-X-VERSION:3\n')
        f.write('#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=854x480\n')
        f.write('480p/index.m3u8\n')
        f.write('#EXT-X-STREAM-INF:BANDWIDTH=3000000,RESOLUTION=1280x720\n')
        f.write('720p/index.m3u8\n')
        f.write('#EXT-X-STREAM-INF:BANDWIDTH=6000000,RESOLUTION=1920x1080\n')
        f.write('1080p/index.m3u8\n')
    