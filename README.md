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

| Component   | Technology                       |
| ----------- | -------------------------------- |
| Language    | Python 3.14                      |
| Framework   | Django 6 + Django REST Framework |
| Database    | PostgreSQL                       |
| ORM         | Django ORM                       |
| Testing     | Pytest                           |
| Environment | python-dotenv                    |
| Driver      | psycopg2-binary                  |

Project dependencies are defined in `requirements.txt`. 

---

# Project Structure

```text
data-ingestion-service/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
│
├── events/
│   ├── management/
│   │   └── commands/
│   │       └── aggregate_events.py
│   │
│   ├── tests/
│   │   ├── test_ingestion.py
│   │   ├── test_bulk_ingestion.py
│   │   ├── test_aggregation.py
│   │   ├── test_concurrency.py
│   │   └── test_time_windows.py
│   │
│   ├── models.py
│   ├── serializers.py
│   ├── selectors.py
│   ├── services.py
│   ├── filters.py
│   ├── pagination.py
│   ├── views.py
│   └── urls.py
│
├── health/
│   ├── views.py
│   └── urls.py
│
├── .env
├── .env.example
├── manage.py
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# System Architecture

```text
                Client
                   │
        ┌──────────┴──────────┐
        │                     │
 POST /events          POST /events/bulk
        │                     │
        └──────────┬──────────┘
                   │
            Validation Layer
                   │
            Service Layer
                   │
          PostgreSQL (Event)
                   │
       aggregate_events Command
                   │
        Database Aggregation
                   │
      PostgreSQL (EventAggregate)
                   │
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
DB_NAME=event_ingestion_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

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

# Running Aggregation Worker

The project implements aggregation using a Django Management Command as required by the assessment.

Run:

```bash
python manage.py aggregate_events
```

This command:

* Aggregates raw events
* Creates minute buckets
* Creates hour buckets
* Is incremental
* Is idempotent

---

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

* Composite database indexes
* Database-backed uniqueness constraints
* `bulk_create(ignore_conflicts=True)` for high-throughput ingestion
* Pagination for raw event queries
* Database-level aggregation
* Incremental aggregation worker
* Stable ordering (`timestamp`, `id`)
* Query optimization using Django ORM

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

---

# Assumptions

* PostgreSQL is available locally.
* Events belong to a single tenant.
* Event timestamps are supplied in UTC.
* Aggregation is executed periodically using the management command.
* Duplicate events share the same `event_id`.

---

# Future Improvements

* Celery + Redis background workers
* Async ingestion pipeline
* Kafka integration
* Prometheus metrics
* OpenTelemetry tracing
* Docker & Docker Compose
* CI/CD pipeline
* Authentication & Authorization
* Distributed rate limiting
* Horizontal scaling with multiple aggregation workers
* API versioning
* OpenAPI / Swagger documentation

---

# Assessment Coverage

| Requirement                      | Status |
| -------------------------------- | ------ |
| Event ingestion                  | ✅      |
| Bulk ingestion                   | ✅      |
| Idempotency                      | ✅      |
| Concurrency handling             | ✅      |
| PostgreSQL support               | ✅      |
| Aggregation worker               | ✅      |
| Incremental aggregation          | ✅      |
| Metrics API                      | ✅      |
| Health endpoint                  | ✅      |
| Readiness endpoint               | ✅      |
| Pagination                       | ✅      |
| Filtering                        | ✅      |
| UTC enforcement                  | ✅      |
| Payload validation               | ✅      |
| Automated tests                  | ✅      |
| Performance optimizations        | ✅      |
| Production-oriented architecture | ✅      |

---

## License

This project was developed as part of the **TechConsonance Python Backend Engineering Assessment** and demonstrates a production-oriented backend implementation aligned with the assessment objectives.
