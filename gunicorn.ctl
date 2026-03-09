[program:gunicorn]
command=/usr/local/bin/gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
directory=/app
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gunicorn.log
stderr_logfile=/var/log/gunicorn-error.log
