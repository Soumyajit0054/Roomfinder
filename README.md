# RoomFinder

Find and list rooms for rent. Flask + MySQL web app, installable as a PWA, with a JSON API and an Expo (React Native) mobile app.

Roles: **tenant** (search, favorites, rental requests), **owner** (manage properties and requests), **admin** (users, properties, requests).

## Backend

Requirements: Python 3.10+, MySQL 8, and (for government-ID OCR at registration) Tesseract and Poppler.

```bash
pip install -r requirements.txt
cp .env.example .env          # then edit the values
mysql -u <user> -p -e "CREATE DATABASE roomfinder"
mysql -u <user> -p roomfinder < sql/roomfinder.sql
flask --app app run --host 0.0.0.0 --port 5000
```

Existing databases created before the government-ID feature need `sql/add_government_id_fields.sql` once.

### Configuration (environment variables or `.env`)

| Variable | Purpose | Default |
|---|---|---|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | MySQL connection | `localhost`, `3306`, `root`, empty, `roomfinder` |
| `SECRET_KEY` | Signs web sessions and API tokens. **Set this**; if unset a random key is used per process | random |
| `UPLOAD_FOLDER` | Where uploaded files are stored | `static/uploads` |
| `UPLOAD_BASE_URL` | Public base URL for images in API responses (e.g. a CDN) | this server |
| `API_TOKEN_MAX_AGE` | Mobile token lifetime in seconds | 30 days |
| `FLASK_DEBUG` | `1` enables debug mode | off |

Never commit `.env`. Uploaded files (photos and ID documents) are git-ignored.

### Tests

```bash
python -m unittest discover tests     # database is mocked; MySQL not required
```

## PWA

The site serves a web manifest and service worker, so it can be installed from a browser. Installing and offline support need HTTPS (or `localhost`).

## JSON API (`/api/v1`)

Bearer-token auth: `POST /api/v1/auth/login` returns a token to send as `Authorization: Bearer <token>`.

- Auth: `auth/login`, `auth/register`, `auth/countries`, `auth/me`, `profile`
- Public: `properties` (filters: `location`, `min_rent`, `max_rent`, `room_type`, `furnished`, `limit`, `offset`), `properties/<id>`
- Tenant: `favorites`, `requests`, `properties/<id>/request`
- Owner (`/owner/...`): dashboard, property CRUD with photo upload, requests with accept/reject
- Admin (`/admin/...`): dashboard, users, properties, requests

## Mobile app (`mobile/`)

Expo + React Navigation + TypeScript.

```bash
cd mobile
npm install
cp .env.example .env     # set EXPO_PUBLIC_API_URL to your server (LAN IP when testing on a phone)
npx expo start
```

Icons are Bootstrap Icons generated into `src/icons.generated.ts` (`npm run icons`).

## Deployment notes

- Run behind HTTPS with a production server, e.g. `gunicorn app:app`, and set `SECRET_KEY`.
- Use a managed MySQL instance and keep it off the public internet.
- Serve uploaded files from private or object storage; ID documents should not be publicly reachable.
