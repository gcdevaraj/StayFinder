# 🏠 StayFinder — Backend API

**StayFinder** is a full-stack platform helping students and working professionals find PGs, private hostels, and government hostels in Bengaluru and other cities.

---

## 📁 Project Structure

```
stayfinder-py/
├── app.py                   # Flask app factory & entry point
├── database.py              # SQLite connection, schema DDL, helpers
├── requirements.txt
├── .env.example
│
├── middleware/
│   └── auth.py              # JWT helpers, @authenticate, @require_admin
│
├── routes/
│   ├── auth.py              # /api/auth  — register, login, refresh, me
│   ├── properties.py        # /api/properties — CRUD, search, save
│   └── other.py             # reviews · enquiries · govt · areas · amenities · admin
│
└── scripts/
    └── seed.py              # Seeds DB with realistic data
```

---

## ⚡ Quick Start

```bash
# 1. Clone / copy the project
cd stayfinder-py

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Copy env file and configure
cp .env.example .env

# 4. Initialise DB and seed data
python scripts/seed.py

# 5. Start the server
python app.py
```

Server starts at **http://localhost:4000**

---

## 🔐 Test Credentials (after seed)

| Role  | Email                     | Password   |
|-------|---------------------------|------------|
| Admin | admin@stayfinder.in       | Admin@123  |
| Owner | ramesh@owner.com          | Owner@123  |
| User  | test@user.com             | Test@123   |

---

## 🗄️ Database Schema

Built with **SQLite** (zero-config, file-based). Swap to PostgreSQL in production by adding a migration layer.

### Tables

| Table                | Purpose                                      |
|----------------------|----------------------------------------------|
| `users`              | All users (role: user / owner / admin)       |
| `properties`         | PG & hostel listings                         |
| `rooms`              | Room types & prices per property             |
| `property_images`    | Images for each property                     |
| `amenities`          | Master amenity list (WiFi, AC, Meals…)       |
| `property_amenities` | Many-to-many: property ↔ amenities           |
| `reviews`            | User reviews with rating + comment           |
| `enquiries`          | Contact enquiries from users to owners       |
| `saved_properties`   | User wishlist / bookmarks                    |
| `govt_hostels`       | Government hostel listings                   |
| `area_guides`        | Neighbourhood info, prices, safety scores    |
| `refresh_tokens`     | Rotating JWT refresh tokens                  |

### ER Diagram (simplified)

```
users ──< properties ──< rooms
  │            │──< property_images
  │            │──< property_amenities >── amenities
  │            │──< reviews
  │            │──< enquiries
  │            └──< saved_properties
  │
  └──< refresh_tokens

govt_hostels  (standalone)
area_guides   (standalone)
```

---

## 📡 API Reference

### Auth  `/api/auth`

| Method | Endpoint              | Auth | Description              |
|--------|-----------------------|------|--------------------------|
| POST   | `/register`           | —    | Create account           |
| POST   | `/login`              | —    | Login, get tokens        |
| POST   | `/refresh`            | —    | Rotate access token      |
| POST   | `/logout`             | ✓    | Invalidate refresh token |
| GET    | `/me`                 | ✓    | Get current user         |
| PATCH  | `/me`                 | ✓    | Update profile           |
| POST   | `/change-password`    | ✓    | Change password          |

**Register / Login response:**
```json
{
  "user": { "id": "...", "name": "John", "email": "...", "role": "user" },
  "accessToken": "eyJ...",
  "refreshToken": "eyJ..."
}
```

---

### Properties  `/api/properties`

| Method | Endpoint                | Auth         | Description                  |
|--------|-------------------------|--------------|------------------------------|
| GET    | `/`                     | optional     | List/search properties       |
| GET    | `/:id`                  | optional     | Single property detail       |
| POST   | `/`                     | owner/admin  | Create property listing      |
| PATCH  | `/:id`                  | owner/admin  | Update property              |
| DELETE | `/:id`                  | owner/admin  | Delete property              |
| GET    | `/saved`                | ✓            | Get user's saved properties  |
| POST   | `/:id/save`             | ✓            | Save / bookmark property     |
| DELETE | `/:id/save`             | ✓            | Remove from saved            |
| GET    | `/owner/mine`           | owner        | Owner's own listings         |

**Query parameters for `GET /`:**

| Param      | Type   | Example              | Description               |
|------------|--------|----------------------|---------------------------|
| `type`     | string | `PG`                 | PG / Private Hostel / Govt Hostel |
| `gender`   | string | `Women`              | Men / Women / Co-ed       |
| `area`     | string | `Koramangala`        | Partial match on area     |
| `city`     | string | `Bengaluru`          | Filter by city            |
| `priceMin` | int    | `5000`               | Minimum rent              |
| `priceMax` | int    | `15000`              | Maximum rent              |
| `amenities`| string | `WiFi,AC,Meals`      | Comma-sep, AND filter     |
| `available`| bool   | `true`               | Only show available       |
| `search`   | string | `whitefield hostel`  | Full-text search          |
| `sortBy`   | string | `price-asc`          | rating / price-asc / price-desc / newest |
| `page`     | int    | `1`                  | Pagination                |
| `limit`    | int    | `12`                 | Results per page (max 50) |

---

### Reviews  `/api/properties/:id/reviews`

| Method | Endpoint   | Auth | Description      |
|--------|------------|------|------------------|
| GET    | `/`        | —    | List reviews     |
| POST   | `/`        | ✓    | Post a review    |
| DELETE | `/:rid`    | ✓    | Delete review    |

---

### Enquiries  `/api/enquiries`

| Method | Endpoint                               | Auth  | Description              |
|--------|----------------------------------------|-------|--------------------------|
| POST   | `/api/properties/:id/enquiries`        | ✓     | Send enquiry to owner    |
| GET    | `/api/enquiries/mine`                  | ✓     | My sent enquiries        |
| GET    | `/api/enquiries/received`              | owner | Enquiries on my listings |
| PATCH  | `/api/enquiries/:id/status`            | owner | Update enquiry status    |

---

### Government Hostels  `/api/govt-hostels`

| Method | Endpoint | Auth  | Description             |
|--------|----------|-------|-------------------------|
| GET    | `/`      | —     | List (filter supported) |
| GET    | `/:id`   | —     | Single hostel detail    |
| POST   | `/`      | admin | Add hostel              |
| DELETE | `/:id`   | admin | Deactivate hostel       |

**Query params:** `eligibility` (SC/ST / OBC / Women / Minority / Labour), `costType` (Free / Subsidized / Paid), `search`

---

### Area Guides  `/api/areas`

| Method | Endpoint  | Auth  | Description         |
|--------|-----------|-------|---------------------|
| GET    | `/`       | —     | List all areas      |
| GET    | `/:name`  | —     | Area + live stats   |
| POST   | `/`       | admin | Add area guide      |

---

### Amenities  `/api/amenities`

| Method | Endpoint | Auth  | Description         |
|--------|----------|-------|---------------------|
| GET    | `/`      | —     | List all amenities  |
| POST   | `/`      | admin | Create amenity      |

**Query params:** `category` (basic / comfort / security / food / transport)

---

### Admin  `/api/admin`

| Method | Endpoint                         | Auth  | Description             |
|--------|----------------------------------|-------|-------------------------|
| GET    | `/stats`                         | admin | Dashboard stats         |
| GET    | `/users`                         | admin | All users (paginated)   |
| PATCH  | `/users/:id`                     | admin | Update role/verified    |
| DELETE | `/users/:id`                     | admin | Delete user             |
| GET    | `/properties`                    | admin | All properties          |
| PATCH  | `/properties/:id/verify`         | admin | Verify/unverify         |
| PATCH  | `/properties/:id/feature`        | admin | Feature/unfeature       |
| DELETE | `/properties/:id`                | admin | Delete property         |
| GET    | `/reviews`                       | admin | Recent reviews          |
| DELETE | `/reviews/:id`                   | admin | Remove review           |

---

## 🔒 Authentication Flow

```
Client                           Server
  │── POST /api/auth/login ──────▶ Validate credentials
  │◀─ { accessToken, refreshToken } ─
  │
  │── GET /api/... (Bearer <accessToken>) ──▶ Verify JWT (15 min)
  │
  │   [Token expires]
  │── POST /api/auth/refresh { refreshToken } ──▶ Rotate tokens
  │◀─ { new accessToken, new refreshToken } ─
```

---

## 🚀 Production Deployment

### Switch to PostgreSQL

1. Install `psycopg2-binary`
2. Replace `database.py` connection with `psycopg2`
3. Update `.env` with `DATABASE_URL`

### Run with Gunicorn (WSGI)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:4000 "app:create_app()"
```

### Environment variables (production)

```env
FLASK_ENV=production
JWT_SECRET=<64-char random string>
REFRESH_TOKEN_SECRET=<64-char random string>
DATABASE_PATH=/var/data/stayfinder.db
FRONTEND_URL=https://yourdomain.com
```

### Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name api.stayfinder.in;

    location / {
        proxy_pass http://127.0.0.1:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /uploads/ {
        alias /var/data/uploads/;
    }
}
```

---

## 🧩 Connecting to the Frontend

In your `stayfinder.html` frontend, replace the hardcoded data arrays with `fetch` calls:

```javascript
// List properties with filters
const res = await fetch('http://localhost:4000/api/properties/?type=PG&area=Koramangala&priceMax=12000');
const { data, meta } = await res.json();

// Authenticated request
const res = await fetch('/api/auth/me', {
  headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
});

// Post an enquiry
await fetch(`/api/properties/${id}/enquiries`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ message: 'I am interested in a double room' })
});
```

---

## 📊 Seeded Data Summary

| Entity           | Count | Details                                    |
|------------------|-------|--------------------------------------------|
| Users            | 8     | 1 admin, 5 owners, 1 test user + register  |
| Properties       | 10    | PGs, hostels across 9 Bengaluru areas      |
| Rooms            | 30    | Single / Double / Triple / Dorm options    |
| Amenities        | 17    | Across 5 categories                        |
| Reviews          | 8     | Ratings 3–5 stars                          |
| Govt Hostels     | 8     | SC/ST, OBC, Women, Labour, Minority        |
| Area Guides      | 12    | All major Bengaluru neighbourhoods         |
