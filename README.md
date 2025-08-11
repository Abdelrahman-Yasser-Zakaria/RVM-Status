# RVM Status & Discovery API

A lightweight Django + Django REST Framework (DRF) service that exposes a read‑only API for discovering active Reverse Vending Machines (RVMs) and identifying which machines have been used recently.

---
## ✨ Overview
Modern recycling infrastructures rely on Reverse Vending Machines to collect and process recyclables. This project provides a simple, extensible backend API to:
- List active RVM machines.
- Filter machines by location (substring search) and recent activity.
- Sort machines automatically by most recent usage (null / never‑used machines appear last per ordering rule).

Designed as a clean foundation that can be expanded with ingestion pipelines, usage tracking, health metrics, geospatial data, and real‑time updates.

---
## ✅ Core Features
- RVM model with fields: `id`, `name`, `location`, `is_active`, `last_usage`.
- RESTful endpoints (currently one collection endpoint) under `/api/rvms/` supporting:
  - Filter by location substring: `?loc=<text>` (case‑insensitive).
  - Exact location filter: `?location=<exact>` (DRF / FilterSet default).
  - Recent usage filter (past 24h): `?recent=true` (boolean forms like `1`, `true`, `True`).
- Only active (`is_active=True`) machines are returned.
- Ordered by `-last_usage` (most recently used first; `null` last by model ordering semantics on SQLite will co-locate nulls at the top; can be tuned in future for Postgres with `nulls_last`).
- Anonymous read‑only access (default DRF permission config).
- Extensible filtering via `django-filter`'s `FilterSet`.

---
## 🧱 Tech Stack
| Layer          | Technology                                     | Purpose                                 |
| -------------- | ---------------------------------------------- | --------------------------------------- |
| Language       | Python 3.13 (inferred from `__pycache__` tags) | Core runtime                            |
| Web Framework  | Django 5.2                                     | Project + ORM + admin                   |
| API Layer      | Django REST Framework                          | Serialization & viewsets                |
| Filtering      | django-filter                                  | Query param filtering (`loc`, `recent`) |
| Database (dev) | SQLite (default)                               | Zero‑config development storage         |

### Python/Django Apps
- `rvm_status`: Project configuration (settings, root URL routing, WSGI/ASGI stubs).
- `status`: Domain app containing model, serializer, viewset, filters, and API routing.

### Dependencies (explicit / implied)
Add these to `requirements.txt` (create if missing):
```
Django==5.2.4
djangorestframework==3.15.2
django-filter==24.3
```
(Adjust versions if your environment already pins them differently.)

---
## 📁 Directory Structure
```
RVM-Status/
├── manage.py                  # Django management script
├── db.sqlite3                 # Dev SQLite database (omit in production repos)
├── guide.md                   # Design & implementation planning guide
├── README.md                  # (This file)
├── rvm_status/                # Project settings & URL config
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py            # Installed apps, DB, REST framework settings
│   ├── urls.py                # Root URL includes API + admin
│   └── wsgi.py
└── status/                    # Domain app for RVM status
    ├── __init__.py
    ├── admin.py               # (Empty placeholder — could register RVM)
    ├── apps.py
    ├── models.py              # RVM model definition
    ├── serializers.py         # RVMSerializer (read‑only)
    ├── views.py               # RVMViewSet + filtering logic
    ├── urls.py                # DRF router exposing /api/rvms/
    ├── tests.py               # Placeholder for future tests
    └── migrations/
        ├── __init__.py
        └── 0001_initial.py    # Creates RVM table
```

---
## ⚙️ Setup Instructions
Follow these steps to install dependencies and run the project locally.

### 1. Clone the Repository
```
git clone https://github.com/Abdelrahman-Yasser-Zakaria/RVM-Status.git
cd RVM-Status
```

### 2. Create & Activate a Virtual Environment (Recommended)
```
python3 -m venv .venv
source .venv/bin/activate
```
(Windows PowerShell: `.venv\Scripts\Activate.ps1`)

### 3. Install Dependencies
If you created `requirements.txt` as suggested:
```
pip install -r requirements.txt
```
Or install directly:
```
pip install Django==5.2.4 djangorestframework==3.15.2 django-filter==24.3
```

### 4. Apply Migrations
```
python manage.py migrate
```

### 5. (Optional) Create Admin Superuser
```
python manage.py createsuperuser
```

### 6. Run the Development Server
```
python manage.py runserver
```
Visit: http://127.0.0.1:8000/api/rvms/

If empty, create some sample records via Django shell:
```
python manage.py shell
```
```python
from status.models import RVM
from django.utils import timezone
RVM.objects.create(name="RVM-01", location="Cairo", last_usage=timezone.now())
RVM.objects.create(name="RVM-02", location="Alexandria")
exit()
```
Refresh the endpoint. You should now see JSON output.

---
## 🧬 Models & Internal Logic

### RVM Model (`status.models.RVM`)
| Field        | Type                     | Purpose                        | Notes                                              |
| ------------ | ------------------------ | ------------------------------ | -------------------------------------------------- |
| `id`         | BigAutoField             | Primary key                    | Auto-generated                                     |
| `name`       | CharField(255)           | Human-friendly identifier      | Useful for technicians & debugging                 |
| `location`   | CharField(255)           | Geographic / site label        | Substring filtered via `loc`; exact via `location` |
| `is_active`  | BooleanField             | Operational availability flag  | Only active machines are exposed by API queryset   |
| `last_usage` | DateTimeField (nullable) | Timestamp of most recent usage | `null` means never used yet                        |

Meta ordering: `('-last_usage',)` gives most recently used first. In SQLite, `NULL` values naturally appear last under `DESC` ordering; in Postgres you may want to enforce `nulls_last` explicitly later.

### Serializer (`status.serializers.RVMSerializer`)
ModelSerializer exposing: `id, name, location, is_active, last_usage`. All fields are currently read-only (see `read_only_fields = fields`) making the API effectively read-only even if POST were attempted.

### Filtering Layer (`RVMFilter` in `status.views`)
Implements:
- `loc`: Case-insensitive substring match on `location` using `icontains`.
- `recent`: Boolean flag; when truthy restricts to records with `last_usage >= now - 24h` and non-null.
- `location`: (Implicit via FilterSet) exact match if provided.

### ViewSet (`RVMViewSet`)
- Base queryset: `RVM.objects.filter(is_active=True)` ensures inactive machines never appear.
- Filter backend: `django-filter` integrates the `RVMFilter` enabling declarative query params.
- Permissions: Controlled by global REST framework setting `DjangoModelPermissionsOrAnonReadOnly`, allowing anonymous safe-method access.

### URL Routing
- `status/urls.py` registers the viewset on `/api/rvms/` via DRF's `DefaultRouter`.
- Project root (`rvm_status/urls.py`) includes a redirect from `/` to `/api/rvms/` and mounts the admin at `/admin/`.

### Ordering & Recency Logic
- Ordering is handled at model Meta level; DRF respects queryset ordering.
- Recency filter computes cutoff using `timezone.now() - timedelta(hours=24)` ensuring timezone awareness with `USE_TZ = True`.
- Null `last_usage` rows excluded from `recent=true` filter because the filter applies `last_usage__isnull=False`.

### Permission Behavior
`DjangoModelPermissionsOrAnonReadOnly` means:
- Anonymous users: read-only (GET/HEAD/OPTIONS) permitted.
- Authenticated users: need model permissions for unsafe methods (not exposed presently due to serializer read-only fields anyway).

### Extensibility Hooks
- To allow creation/update: remove fields from `read_only_fields` and adjust permissions.
- To add pagination: define `REST_FRAMEWORK['PAGE_SIZE']` or a custom pagination class.
- To add more filters: add fields to `RVMFilter.Meta.fields` or custom methods.

---
## 🔗 API Reference

| Endpoint     | Method(s) | Description                         | Query Params                | Auth              |
| ------------ | --------- | ----------------------------------- | --------------------------- | ----------------- |
| `/api/rvms/` | GET       | List active RVMs ordered by recency | `loc`, `location`, `recent` | Anonymous read OK |
| `/`          | GET       | Redirects (302) to `/api/rvms/`     | —                           | Anonymous         |
| `/admin/`    | GET       | Django admin site (requires login)  | —                           | Superuser         |

Example: `/api/rvms/?loc=alex&recent=true`

Future detail endpoint (not yet implemented) would follow `/api/rvms/<id>/` if `lookup_field` is left default.

### Response Schema (List)
```
[
  {
    "id": 1,
    "name": "RVM-01",
    "location": "Cairo",
    "is_active": true,
    "last_usage": "2025-08-11T13:30:00Z"  # ISO8601, timezone-aware
  },
  ...
]
```

### Error Handling
- Invalid filters are silently ignored by django-filter (param names not defined are disregarded) maintaining robustness.
- No custom 4xx/5xx error formatting yet; DRF defaults apply.

---

---
## 🔍 API Usage
Base path: `/api/rvms/`

Example list (GET):
```
GET /api/rvms/
[
  {
    "id": 1,
    "name": "RVM-01",
    "location": "Cairo",
    "is_active": true,
    "last_usage": "2025-08-11T13:30:00Z"
  },
  ...
]
```

### Query Parameters
| Param      | Type   | Description                                  | Example                     |
| ---------- | ------ | -------------------------------------------- | --------------------------- |
| `loc`      | string | Case-insensitive substring match on location | `/api/rvms/?loc=alex`       |
| `location` | string | Exact location match                         | `/api/rvms/?location=Cairo` |
| `recent`   | bool   | Machines used in past 24h                    | `/api/rvms/?recent=true`    |

Combinations allowed, e.g.: `/api/rvms/?loc=cai&recent=1`

### HTTP Status Codes
- 200 OK: Successful retrieval.
- 404 Not used (DRF router handles detail routes if added in future).

### Authentication & Permissions
- Anonymous read‑only allowed (`GET`, `HEAD`, `OPTIONS`).
- Mutating operations (POST/PUT/PATCH/DELETE) currently blocked by read‑only permission for anonymous users (would require auth setup if create/edit endpoints are enabled later).

---
## 🧪 Testing (To Be Expanded)
A placeholder `tests.py` exists. Suggested future tests:
1. Only active RVMs returned.
2. Ordering by `last_usage` desc.
3. `loc` substring filter behavior.
4. `recent` 24h boundary inclusion.
5. Empty list returns 200 + `[]`.

Run tests:
```
python manage.py test status
```

---
## 🛡️ Security & Production Notes
- Replace the development `SECRET_KEY` via environment variable before deploying.
- Set `DEBUG=False` and configure `ALLOWED_HOSTS`.
- Use Postgres or another production-grade DB instead of SQLite.
- Consider rate limiting / caching if exposed publicly.
- Add CI pipeline to run tests & linting.

---
## ♻️ Data Model Summary
| Field        | Type                     | Notes                              |
| ------------ | ------------------------ | ---------------------------------- |
| `id`         | BigAutoField             | Primary key                        |
| `name`       | CharField(255)           | Human-readable identifier          |
| `location`   | CharField(255)           | City / site; substring filterable  |
| `is_active`  | BooleanField             | Only active machines listed        |
| `last_usage` | DateTimeField (nullable) | Used for recency filter & ordering |

---

