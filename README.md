# Data Ingestion & Aggregation Service

> **Python Backend Engineering Assessment – TechConsonance**

A production-oriented backend service built using **Django REST Framework** and **PostgreSQL** to ingest high-volume events, provide idempotent and concurrency-safe storage, aggregate events efficiently, and expose REST APIs for querying both raw and aggregated event data. The implementation follows the assessment requirements around correctness, concurrency handling, performance optimization, clean architecture, and automated testing. 

---

# Features

## Event Ingestion

* Single event ingestion (`POST /api/events/`)
* Bulk ingestion (`POST /api/events/bulk/`)
* Supports up to **5000 events per request**
* Payload validation
* JSON payload support
* UTC timestamp enforcement

---

## Idempotency

* Globally unique `event_id`
* Duplicate events safely ignored
* Database-level uniqueness constraint
* Safe under concurrent requests

---

## Query APIs

* Retrieve raw events
* Mandatory tenant filtering
* Source filtering
* Event type filtering
* Time window filtering
* Stable pagination

---

## Aggregation

* Minute-level aggregation
* Hour-level aggregation
* Background aggregation worker
* Incremental aggregation
* Idempotent aggregation
* Aggregated metrics API

---

## Health Monitoring

* Health endpoint
* Database readiness endpoint

---

## Testing

Pytest test suite covering:

* Event ingestion
* Bulk ingestion
* Aggregation
* Concurrency
* Idempotency
* Time window filtering
* Pagination

---

# Tech Stack

| Area                     | Tech                                                        |
| ------------------------ | ----------------------------------------------------------- |
| Language                 | Python 3.10+                                                |
| Backend Framework        | Django REST Framework                                       |
| Database                 | PostgreSQL                                                  |
| API Style                | REST APIs                                                   |
| Testing                  | Pytest                                                      |
| ORM                      | Django ORM                                                  |
| Background Processing    | Celery + Django Management Command                          |
| Message Broker           | Redis                                                       |
| Asynchronous I/O         | Celery Workers                                              |
| Bulk Insert              | `bulk_create(ignore_conflicts=True)`                        |
| Idempotency              | Unique DB Constraint (`event_id`)                           |
| Concurrency Safety       | Database Constraints + Transactions                         |
| Performance Optimization | Database Indexing + Bulk Insert + Query Optimization        |
| Pagination               | DRF Pagination                                              |
| Sorting                  | Stable Ordering (`timestamp`, `id`)                         |
| Aggregation              | Database `GROUP BY` Aggregation                             |
| Security                 | Input Validation + UTC Enforcement + Rate Limiting Strategy |
| Documentation            | README + Architecture Notes                                 |
| Version Control          | Git                                                         |


Project dependencies are defined in `requirements.txt`. 

---

# Project Structure

```text
data-ingestion-service/
│
├── config/
│   ├── __init__.py
│   ├── celery.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── events/
│   ├── management/
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── aggregate_events.py
│   │
│   ├── migrations/
│   │   ├── __init__.py
│   │   ├── 0001_initial.py
│   │   ├── 0002_eventaggregate.py
│   │   └── 0003_aggregationcheckpoint.py
│   │
│   ├── tests/
│   │   ├── test_ingestion.py
│   │   ├── test_bulk_ingestion.py
│   │   ├── test_aggregation.py
│   │   ├── test_concurrency.py
│   │   └── test_time_windows.py
│   │
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── filters.py
│   ├── models.py
│   ├── pagination.py
│   ├── selectors.py
│   ├── serializers.py
│   ├── services.py
│   ├── tasks.py
│   ├── urls.py
│   └── views.py
│
├── health/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── .env
├── .env.example
├── .gitattributes
├── .gitignore
├── ARCHITECTURE.md
├── db.sqlite3
├── manage.py
├── pytest.ini
├── README.md
├── requirements.txt
└── venv/
```

---

# System Architecture

```                        
                           Client
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
POST /api/events                    POST /api/events/bulk
        │                                       │
        └───────────────────┬───────────────────┘
                            │
                     Validation Layer
                            │
                     Service Layer
                            │
                            ▼
                 PostgreSQL Event Table
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
Manual CLI Command                 Async Celery Task
aggregate_events            aggregate_events_task.delay()
          │                                   │
          │                          Redis Message Broker
          │                                   │
          │                           Celery Worker
          │                                   │
          └─────────────────┬─────────────────┘
                            │
                            ▼
            Database-level GROUP BY Aggregation
                            │
                            ▼
             PostgreSQL EventAggregate Table
                            │
                            ▼
                   GET /api/metrics
```

---

# Database Schema

## Event

| Field      | Type               |
| ---------- | ------------------ |
| event_id   | CharField (Unique) |
| tenant_id  | CharField          |
| source     | CharField          |
| event_type | CharField          |
| timestamp  | DateTimeField      |
| payload    | JSONField          |
| created_at | DateTimeField      |

---

## EventAggregate

| Field        | Type        |
| ------------ | ----------- |
| tenant_id    | CharField   |
| bucket_start | DateTime    |
| bucket_size  | minute/hour |
| source       | Optional    |
| event_type   | Optional    |
| count        | Integer     |
| first_seen   | DateTime    |
| last_seen    | DateTime    |

---

# API Endpoints

The project exposes event, metrics, health, and readiness endpoints through the configured URL routing.   

| Method | Endpoint            | Description            |
| ------ | ------------------- | ---------------------- |
| POST   | `/api/events/`      | Single event ingestion |
| POST   | `/api/events/bulk/` | Bulk ingestion         |
| GET    | `/api/events/`      | Query raw events       |
| GET    | `/api/metrics/`     | Aggregated metrics     |
| GET    | `/health/`          | Liveness check         |
| GET    | `/ready/`           | Database readiness     |

---

# PostgreSQL Configuration

Create a PostgreSQL database.

```sql
CREATE DATABASE event_ingestion_db;
```

Configure `.env`

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=events_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Celery + Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```
# Redis Setup

Run Redis using Docker:

```bash
docker run --name ingestion-redis -p 6379:6379 redis
```

Verify Redis is running before starting the Celery worker.
---

# Installation

Clone repository

```bash
git clone <repository-url>

cd data-ingestion-service
```

Create virtual environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Database Setup

```bash
python manage.py makemigrations

python manage.py migrate
```

---

# Running the Project

```bash
python manage.py runserver
```

Server

```
http://127.0.0.1:8000/
```

---

# Running Aggregation

### Option 1 – Manual Aggregation Command

```bash
python manage.py aggregate_events
```

### Option 2 – Celery Worker (Recommended)

Start the Celery worker:

```bash
celery -A config worker -l info -P solo
```

Bulk ingestion automatically triggers:

```python
aggregate_events_task.delay()
```

using Redis as the message broker.

The aggregation process is:

- Incremental
- Idempotent
- Executed asynchronously
- Database-driven using SQL `GROUP BY`

# Running Tests

Run complete test suite

```bash
pytest
```

Verbose

```bash
pytest -v
```

Specific module

```bash
pytest events/tests/test_ingestion.py
```

---

# Example Requests

## Single Event

```http
POST /api/events/
```

```json
{
    "event_id":"evt_001",
    "tenant_id":"tenant_1",
    "source":"web",
    "event_type":"click",
    "timestamp":"2026-07-07T12:00:00Z",
    "payload":{
        "page":"home"
    }
}
```

---

## Bulk Events

```http
POST /api/events/bulk/
```

```json
{
    "events":[
        {
            "event_id":"evt1",
            "tenant_id":"tenant_1",
            "source":"web",
            "event_type":"click",
            "timestamp":"2026-07-07T12:00:00Z",
            "payload":{}
        }
    ]
}
```

---

## Query Events

```http
GET /api/events/?tenant_id=tenant_1
```

Filter

```http
GET /api/events/?tenant_id=tenant_1&source=web
```

Time window

```http
GET /api/events/?tenant_id=tenant_1&from=2026-07-07T12:00:00Z&to=2026-07-07T13:00:00Z
```

---

## Query Metrics

```http
GET /api/metrics/?tenant_id=tenant_1&bucket_size=hour
```

---

# Performance Optimizations

* Composite database indexes for efficient filtering
* Batch inserts using `bulk_create(batch_size=1000, ignore_conflicts=True)`
* Database-backed uniqueness constraint for idempotent ingestion
* Lazy QuerySet evaluation using Django ORM
* Stable ordering (`timestamp`, `id`)
* Pagination to limit response size
* Database-level `GROUP BY` aggregation (no in-memory aggregation)
* Incremental aggregation using checkpoints
* Asynchronous aggregation with Celery and Redis

---

# Concurrency & Idempotency

The service is designed for concurrent workloads.

Implemented safeguards include:

* Database uniqueness constraint on `event_id`
* Transaction handling
* Duplicate detection
* Idempotent aggregation worker
* Safe bulk ingestion
* Incremental aggregation checkpoint

---

# Security Considerations

* Payload size validation
* UTC timestamp enforcement
* Input validation using DRF serializers
* Tenant-based filtering
* Database readiness endpoint
* Basic rate-limiting strategy documented (suitable for DRF throttling or API gateway integration)

