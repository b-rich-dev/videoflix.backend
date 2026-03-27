from django.apps import AppConfig


class VideoflixAppConfig(AppConfig):
    name = 'videoflix_app'
    
    def ready(self):
        import videoflix_app.signals  # Import signals to connect them
