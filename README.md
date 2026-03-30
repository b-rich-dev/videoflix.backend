# Videoflix – Backend

REST API for the Videoflix platform. Built with **Django 6**, **Django REST Framework**, **SimpleJWT** and **ffmpeg**. Videos are automatically converted to HLS format (HTTP Live Streaming) at three resolutions and processed via background jobs.

---

## Table of Contents

- [Videoflix – Backend](#videoflix--backend)
  - [Table of Contents](#table-of-contents)
  - [Tech Stack](#tech-stack)
  - [Prerequisites](#prerequisites)
  - [Quick Start with Docker](#quick-start-with-docker)
  - [Environment Variables (.env)](#environment-variables-env)
  - [API Endpoints](#api-endpoints)
    - [Authentication](#authentication)
      - [Registration – Request Body](#registration--request-body)
      - [Login – Request Body](#login--request-body)
    - [Videos](#videos)
      - [Upload Video – Request (multipart/form-data)](#upload-video--request-multipartform-data)
      - [Video List Response](#video-list-response)
  - [Authentication Concept](#authentication-concept)
  - [HLS Video Conversion](#hls-video-conversion)
    - [Flow](#flow)
    - [Output Structure](#output-structure)
    - [Encoding Parameters](#encoding-parameters)
  - [Project Structure](#project-structure)
  - [Running Tests](#running-tests)
  - [Local Development (without Docker)](#local-development-without-docker)

---

## Tech Stack

| Component             | Version / Package                 |
| --------------------- | --------------------------------- |
| Python                | 3.12                              |
| Django                | 6.0.3                             |
| Django REST Framework | 3.16.1                            |
| SimpleJWT             | 5.5.1                             |
| Database              | PostgreSQL (via psycopg2)         |
| Cache / Queue         | Redis + django-redis + django-rq  |
| Video Conversion      | ffmpeg (installed system-wide)    |
| CORS                  | django-cors-headers 4.9.0         |
| Static Files          | whitenoise 6.12.0                 |
| Server                | Gunicorn 25.1.0                   |
| Containerization      | Docker + Docker Compose           |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- A `.env` file in the project directory (see [Environment Variables](#environment-variables-env))

---

## Quick Start with Docker

```bash
# 1. Clone the repository
git clone https://github.com/b-rich-dev/videoflix.backend
cd videoflix.backend

# 2. Create the .env file (see "Environment Variables" section)
cp .env.template .env   # or create manually

# 3. Build and start the containers
docker compose up --build
```

The entrypoint script automatically runs on startup:
- `collectstatic` – collect static files
- `makemigrations` + `migrate` – database migrations
- Create a superuser (credentials from `.env`)
- Start Gunicorn on port **8000**

The `rqworker` container starts in parallel and processes background jobs (video conversion).

> The API is then available at `http://localhost:8000/api/`.
> The Django admin interface is available at `http://localhost:8000/admin/`.

---

## Environment Variables (.env)

Create a `.env` file in the project directory with the following content (adjust values as needed):

```env
# Django
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=secure-password
DJANGO_SUPERUSER_EMAIL=admin@example.com

SECRET_KEY=your-secret-django-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

# Database (PostgreSQL)
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=secure-db-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

# Email (SMTP)
EMAIL_HOST=mail.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=email-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@example.com

# Frontend URL (for links in emails)
FRONTEND_URL=http://127.0.0.1:5500
```

> **Note:** Never commit the `.env` file to version control (Git)!

---

## API Endpoints

All endpoints are available under the `/api/` prefix.

### Authentication

| Method | Endpoint                                  | Description                                       | Auth Required |
| ------ | ----------------------------------------- | ------------------------------------------------- | ------------- |
| POST   | `/api/register/`                          | Register a new user                               | No            |
| GET    | `/api/activate/<uidb64>/<token>/`         | Activate email address (via link from email)      | No            |
| POST   | `/api/login/`                             | Log in, JWT cookies are set                       | No            |
| POST   | `/api/logout/`                            | Log out, refresh token is invalidated             | Yes (Cookie)  |
| POST   | `/api/token/refresh/`                     | Renew access token using refresh token            | Yes (Cookie)  |
| POST   | `/api/password_reset/`                    | Request a password reset email                    | No            |
| POST   | `/api/password_confirm/<uidb64>/<token>/` | Set a new password                                | No            |

#### Registration – Request Body

```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "confirmed_password": "securepassword"
}
```

#### Login – Request Body

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

After a successful login, two **HTTP-Only cookies** are set:
- `access` – access token (valid for 60 minutes)
- `refresh` – refresh token (valid for 7 days)

---

### Videos

| Method | Endpoint                                    | Description                                  | Permission               |
| ------ | ------------------------------------------- | -------------------------------------------- | ------------------------ |
| POST   | `/api/upload/`                              | Upload a video                               | Logged in + Staff/Admin  |
| GET    | `/api/video/`                               | Retrieve list of all videos                  | Logged in                |
| GET    | `/api/video/<id>/<resolution>/index.m3u8`   | Retrieve HLS playlist for a resolution       | Logged in                |
| GET    | `/api/video/<id>/<resolution>/<segment>/`   | Retrieve a single HLS segment (`.ts` file)   | Logged in                |

**Valid resolutions:** `480p`, `720p`, `1080p`

#### Upload Video – Request (multipart/form-data)

| Field         | Type   | Required | Description            |
| ------------- | ------ | -------- | ---------------------- |
| `title`       | string | Yes      | Title of the video     |
| `description` | string | Yes      | Description            |
| `category`    | string | Yes      | Category               |
| `file`        | file   | Yes      | Video file (.mp4 etc.) |

#### Video List Response

```json
[
  {
    "id": 1,
    "created_at": "2026-03-30T12:00:00Z",
    "title": "Sample Video",
    "description": "A short description",
    "thumbnail_url": "/media/thumbnails/sample_thumbnail.jpg",
    "category": "Action"
  }
]
```

---

## Authentication Concept

The API uses **JWT tokens** stored exclusively in **HTTP-Only cookies**. This prevents access by JavaScript and protects against XSS attacks.

- **Access token** (`access` cookie): Sent with every authenticated request, valid for 60 minutes.
- **Refresh token** (`refresh` cookie): Used at the `/api/token/refresh/` endpoint to obtain a new access token. Valid for 7 days. After rotation, the old token is added to the blacklist.
- **Logout**: Adds the refresh token to the blacklist so it can no longer be used.

The custom class `CookieJWTAuthentication` (`auth_app/api/authentication.py`) automatically reads the access token from the `access` cookie instead of the `Authorization` header.

---

## HLS Video Conversion

After a video is uploaded, a background job is automatically started via **django-rq** (Redis Queue), which converts the video to HLS format using **ffmpeg**.

### Flow

```
Upload (POST /api/upload/)
  └─► Signal: post_save (videoflix_app/signals.py)
        └─► RQ Job: convert_to_hls (videoflix_app/tasks.py)
              └─► ffmpeg converts to 3 resolutions
```

### Output Structure

For each uploaded file `media/videos/example.mp4`, the following structure is created:

```
media/videos/
  example.mp4                     ← Original file
  example/
    master.m3u8                   ← Master playlist (references all resolutions)
    480p/
      index.m3u8
      segment_000.ts
      segment_001.ts
      ...
    720p/
      index.m3u8
      segment_000.ts
      ...
    1080p/
      index.m3u8
      segment_000.ts
      ...
  example_thumbnail.jpg           ← Auto-generated preview image (frame at 1s)
```

### Encoding Parameters

| Resolution | Dimensions  | Target Bitrate | Video Codec | Audio Codec |
| ---------- | ----------- | -------------- | ----------- | ----------- |
| 480p       | 854 × 480   | 1,000 kbps     | H.264       | AAC         |
| 720p       | 1280 × 720  | 3,000 kbps     | H.264       | AAC         |
| 1080p      | 1920 × 1080 | 6,000 kbps     | H.264       | AAC         |

Segment length: **10 seconds** per `.ts` file.

---

## Project Structure

```
videoflix.backend/
│
├── auth_app/                    # Authentication app
│   ├── api/
│   │   ├── authentication.py    # CookieJWTAuthentication
│   │   ├── serializers.py       # Registration serializer
│   │   ├── tokens.py            # Token helper functions
│   │   ├── urls.py              # Auth URL configuration
│   │   └── views.py             # All auth views
│   ├── templates/auth_app/
│   │   ├── activation_email.html
│   │   └── password_reset_email.html
│   └── tests/                   # Auth test suite
│
├── videoflix_app/               # Video app
│   ├── api/
│   │   ├── serializers.py       # VideoUploadSerializer
│   │   ├── urls.py              # Video URL configuration
│   │   └── views.py             # VideoListView, HLSManifestView, …
│   ├── models.py                # Video model
│   ├── signals.py               # post_save / post_delete handlers
│   ├── tasks.py                 # RQ jobs: convert_to_hls, create_video_thumbnail
│   └── tests/                   # Video test suite
│
├── core/
│   ├── settings.py              # Django configuration
│   └── urls.py                  # Root URL configuration
│
├── media/                       # Uploaded files – created at runtime by Docker (not in Git)
├── static/                      # Static files
├── .env                         # Environment variables (not in Git)
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
└── requirements.txt
```

---

## Running Tests

Tests run inside the Docker container:

```bash
# Run all tests
docker compose exec web python manage.py test

# Auth tests only
docker compose exec web python manage.py test auth_app

# Video tests only
docker compose exec web python manage.py test videoflix_app
```

The test suite currently contains **60 tests** (47 auth + 13 video):

| Area                | Tests |
|---------------------|-------|
| Registration        | 11    |
| Login / Logout      | 12    |
| Account Activation  | 7     |
| Token Refresh       | 5     |
| Password Reset      | 12    |
| Videos              | 13    |

---

## Local Development (without Docker)

> Requirements: Python 3.12, PostgreSQL and Redis must be running locally. `ffmpeg` must be available in the `PATH`.

```bash
# Create virtual environment
python -m venv env

# Activate virtual environment
.\env\Scripts\Activate.ps1          # Windows
source env/bin/activate             # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start development server
python manage.py runserver

# Start RQ worker in a second terminal
python manage.py rqworker default
```
