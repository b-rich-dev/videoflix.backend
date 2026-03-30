# Videoflix – Backend

REST-API für die Videoflix-Plattform. Gebaut mit **Django 6**, **Django REST Framework**, **SimpleJWT** und **ffmpeg**. Videos werden automatisch in HLS-Format (HTTP Live Streaming) in drei Auflösungen konvertiert und per Hintergrundjob verarbeitet.

---

## Inhaltsverzeichnis

- [Videoflix – Backend](#videoflix--backend)
  - [Inhaltsverzeichnis](#inhaltsverzeichnis)
  - [Technologie-Stack](#technologie-stack)
  - [Voraussetzungen](#voraussetzungen)
  - [Schnellstart mit Docker](#schnellstart-mit-docker)
  - [Umgebungsvariablen (.env)](#umgebungsvariablen-env)
  - [API-Endpunkte](#api-endpunkte)
    - [Authentifizierung](#authentifizierung)
      - [Registrierung – Request-Body](#registrierung--request-body)
      - [Login – Request-Body](#login--request-body)
    - [Videos](#videos)
      - [Video hochladen – Request (multipart/form-data)](#video-hochladen--request-multipartform-data)
      - [Video-Listen-Antwort](#video-listen-antwort)
  - [Authentifizierungskonzept](#authentifizierungskonzept)
  - [HLS-Videokonvertierung](#hls-videokonvertierung)
    - [Ablauf](#ablauf)
    - [Ausgabestruktur](#ausgabestruktur)
    - [Kodierungsparameter](#kodierungsparameter)
  - [Projektstruktur](#projektstruktur)
  - [Tests ausführen](#tests-ausführen)
  - [Lokale Entwicklung (ohne Docker)](#lokale-entwicklung-ohne-docker)

---

## Technologie-Stack

| Komponente            | Version / Paket                   |
| --------------------- | --------------------------------- |
| Python                | 3.12                              |
| Django                | 6.0.3                             |
| Django REST Framework | 3.16.1                            |
| SimpleJWT             | 5.5.1                             |
| Datenbank             | PostgreSQL (via psycopg2)         |
| Cache / Queue         | Redis + django-redis + django-rq  |
| Videokonvertierung    | ffmpeg (systemseitig installiert) |
| CORS                  | django-cors-headers 4.9.0         |
| Static Files          | whitenoise 6.12.0                 |
| Server                | Gunicorn 25.1.0                   |
| Containerisierung     | Docker + Docker Compose           |

---

## Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installiert und gestartet
- Eine `.env`-Datei im Projektverzeichnis (siehe [Umgebungsvariablen](#umgebungsvariablen-env))

---

## Schnellstart mit Docker

```bash
# 1. Repository klonen
git clone https://github.com/b-rich-dev/videoflix.backend
cd videoflix.backend

# 2. .env-Datei anlegen (siehe Abschnitt "Umgebungsvariablen")
cp .env.template .env   # oder manuell erstellen

# 3. Container bauen und starten
docker compose up --build
```

Das Entrypoint-Skript führt beim Start automatisch aus:
- `collectstatic` – statische Dateien einsammeln
- `makemigrations` + `migrate` – Datenbankmigrationen
- Anlegen eines Superusers (Zugangsdaten aus `.env`)
- Start von Gunicorn auf Port **8000**

Parallel startet der `rqworker`-Container und verarbeitet Hintergrundjobs (Video­konvertierung).

> Die API ist danach unter `http://localhost:8000/api/` erreichbar.
> Das Django-Admin-Interface ist unter `http://localhost:8000/admin/` erreichbar.

---

## Umgebungsvariablen (.env)

Erstelle eine `.env`-Datei im Projektverzeichnis mit folgendem Inhalt (Werte anpassen):

```env
# Django
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=sicheres-passwort
DJANGO_SUPERUSER_EMAIL=admin@example.com

SECRET_KEY=dein-geheimer-django-schluessel
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

# Datenbank (PostgreSQL)
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=sicheres-db-passwort
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0

# E-Mail (SMTP)
EMAIL_HOST=mail.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=email-passwort
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@example.com

# Frontend-URL (für Links in E-Mails)
FRONTEND_URL=http://127.0.0.1:5500
```

> **Hinweis:** Die `.env`-Datei niemals in die Versionskontrolle (Git) einchecken!

---

## API-Endpunkte

Alle Endpunkte sind unter dem Präfix `/api/` erreichbar.

### Authentifizierung

| Methode | Endpunkt                                  | Beschreibung                                    | Auth erforderlich |
| ------- | ----------------------------------------- | ----------------------------------------------- | ----------------- |
| POST    | `/api/register/`                          | Neuen Benutzer registrieren                     | Nein              |
| GET     | `/api/activate/<uidb64>/<token>/`         | E-Mail-Adresse aktivieren (per Link aus E-Mail) | Nein              |
| POST    | `/api/login/`                             | Einloggen, JWT-Cookies werden gesetzt           | Nein              |
| POST    | `/api/logout/`                            | Ausloggen, Refresh-Token wird invalidiert       | Ja (Cookie)       |
| POST    | `/api/token/refresh/`                     | Access-Token per Refresh-Token erneuern         | Ja (Cookie)       |
| POST    | `/api/password_reset/`                    | Passwort-Reset-E-Mail anfordern                 | Nein              |
| POST    | `/api/password_confirm/<uidb64>/<token>/` | Neues Passwort setzen                           | Nein              |

#### Registrierung – Request-Body

```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "confirmed_password": "securepassword"
}
```

#### Login – Request-Body

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Nach erfolgreichem Login werden zwei **HTTP-Only-Cookies** gesetzt:
- `access` – Access-Token (Gültigkeit: 60 Minuten)
- `refresh` – Refresh-Token (Gültigkeit: 7 Tage)

---

### Videos

| Methode | Endpunkt                                 | Beschreibung                                | Berechtigung             |
| ------- | ---------------------------------------- | ------------------------------------------- | ------------------------ |
| POST    | `/api/upload/`                           | Video hochladen                             | Eingeloggt + Staff/Admin |
| GET     | `/api/video/`                            | Liste aller Videos abrufen                  | Eingeloggt               |
| GET     | `/api/video/<id>/<auflösung>/index.m3u8` | HLS-Playlist für eine Auflösung abrufen     | Eingeloggt               |
| GET     | `/api/video/<id>/<auflösung>/<segment>/` | Einzelnes HLS-Segment (`.ts`-Datei) abrufen | Eingeloggt               |

**Gültige Auflösungen:** `480p`, `720p`, `1080p`

#### Video hochladen – Request (multipart/form-data)

| Feld          | Typ    | Pflicht | Beschreibung           |
| ------------- | ------ | ------- | ---------------------- |
| `title`       | string | Ja      | Titel des Videos       |
| `description` | string | Ja      | Beschreibung           |
| `category`    | string | Ja      | Kategorie              |
| `file`        | file   | Ja      | Videodatei (.mp4 etc.) |

#### Video-Listen-Antwort

```json
[
  {
    "id": 1,
    "created_at": "2026-03-30T12:00:00Z",
    "title": "Beispielvideo",
    "description": "Eine kurze Beschreibung",
    "thumbnail_url": "/media/thumbnails/beispielvideo_thumbnail.jpg",
    "category": "Action"
  }
]
```

---

## Authentifizierungskonzept

Die API verwendet **JWT-Tokens**, die ausschließlich in **HTTP-Only-Cookies** gespeichert werden. Das verhindert den Zugriff durch JavaScript und schützt vor XSS-Angriffen.

- **Access-Token** (`access`-Cookie): Wird bei jedem authentifizierten Request mitgeschickt, gültig für 60 Minuten.
- **Refresh-Token** (`refresh`-Cookie): Wird beim `/api/token/refresh/`-Endpunkt genutzt, um einen neuen Access-Token zu erhalten. Gültig für 7 Tage. Nach Rotation wird der alte Token in die Blacklist eingetragen.
- **Logout**: Trägt den Refresh-Token in die Blacklist ein, sodass er nicht mehr verwendet werden kann.

Die benutzerdefinierte Klasse `CookieJWTAuthentication` (`auth_app/api/authentication.py`) liest den Access-Token automatisch aus dem `access`-Cookie statt aus dem `Authorization`-Header.

---

## HLS-Videokonvertierung

Nach dem Upload eines Videos wird automatisch ein Hintergrundjob per **django-rq** (Redis Queue) gestartet, der das Video mit **ffmpeg** in das HLS-Format konvertiert.

### Ablauf

```
Upload (POST /api/upload/)
  └─► Signal: post_save (videoflix_app/signals.py)
        └─► RQ-Job: convert_to_hls (videoflix_app/tasks.py)
              └─► ffmpeg konvertiert in 3 Auflösungen
```

### Ausgabestruktur

Für jede hochgeladene Datei `media/videos/beispiel.mp4` entsteht folgende Struktur:

```
media/videos/
  beispiel.mp4                    ← Originaldatei
  beispiel/
    master.m3u8                   ← Master-Playlist (referenziert alle Auflösungen)
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
  beispiel_thumbnail.jpg          ← Auto-generiertes Vorschaubild (Frame bei 1s)
```

### Kodierungsparameter

| Auflösung | Abmessungen | Ziel-Bitrate | Codec Video | Codec Audio |
| --------- | ----------- | ------------ | ----------- | ----------- |
| 480p      | 854 × 480   | 1.000 kbps   | H.264       | AAC         |
| 720p      | 1280 × 720  | 3.000 kbps   | H.264       | AAC         |
| 1080p     | 1920 × 1080 | 6.000 kbps   | H.264       | AAC         |

Segment-Länge: **10 Sekunden** pro `.ts`-Datei.

---

## Projektstruktur

```
videoflix.backend/
│
├── auth_app/                    # Authentifizierungs-App
│   ├── api/
│   │   ├── authentication.py    # CookieJWTAuthentication
│   │   ├── serializers.py       # Registrierungs-Serializer
│   │   ├── tokens.py            # Token-Hilfsfunktionen
│   │   ├── urls.py              # Auth-URL-Konfiguration
│   │   └── views.py             # Alle Auth-Views
│   ├── templates/auth_app/
│   │   ├── activation_email.html
│   │   └── password_reset_email.html
│   └── tests/                   # Test-Suite Auth
│
├── videoflix_app/               # Video-App
│   ├── api/
│   │   ├── serializers.py       # VideoUploadSerializer
│   │   ├── urls.py              # Video-URL-Konfiguration
│   │   └── views.py             # VideoListView, HLSManifestView, …
│   ├── models.py                # Video-Modell
│   ├── signals.py               # post_save / post_delete Handler
│   ├── tasks.py                 # RQ-Jobs: convert_to_hls, create_video_thumbnail
│   └── tests/                   # Test-Suite Videos
│
├── core/
│   ├── settings.py              # Django-Konfiguration
│   └── urls.py                  # Root-URL-Konfiguration
│
├── media/                       # Hochgeladene Dateien – wird zur Laufzeit von Docker angelegt (nicht in Git)
├── static/                      # Statische Dateien
├── .env                         # Umgebungsvariablen (nicht in Git)
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
└── requirements.txt
```

---

## Tests ausführen

Die Tests laufen innerhalb des Docker-Containers:

```bash
# Alle Tests ausführen
docker compose exec web python manage.py test

# Nur Auth-Tests
docker compose exec web python manage.py test auth_app

# Nur Video-Tests
docker compose exec web python manage.py test videoflix_app
```

Die Test-Suite umfasst aktuell **60 Tests** (47 Auth + 13 Video):

| Bereich             | Tests |
|---------------------|-------|
| Registrierung       | 11    |
| Login / Logout      | 12    |
| Account-Aktivierung | 7     |
| Token-Refresh       | 5     |
| Passwort-Reset      | 12    |
| Videos              | 13    |

---

## Lokale Entwicklung (ohne Docker)

> Voraussetzung: Python 3.x, PostgreSQL und Redis müssen lokal laufen. `ffmpeg` muss im `PATH` verfügbar sein.

```bash
# Virtuelle Umgebung erstellen
python -m venv env

# Virtuelle Umgebung aktivieren
.\env\Scripts\Activate.ps1          # Windows
source env/bin/activate             # Linux/macOS

# Abhängigkeiten installieren
pip install -r requirements.txt

# Datenbank migrieren
python manage.py migrate

# Entwicklungsserver starten
python manage.py runserver

# RQ-Worker in einem zweiten Terminal starten
python manage.py rqworker default
```
