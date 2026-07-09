# Architecture Notes

## Data Ingestion & Aggregation Service

## Overview

This project implements a production-oriented **Data Ingestion and Aggregation Service** using **Django REST Framework** and **PostgreSQL**. The architecture focuses on correctness, idempotency, concurrency safety, scalability, and maintainability while satisfying the requirements of the Python Backend Engineering Assessment. 

The system accepts incoming events through REST APIs, validates them, stores them safely in PostgreSQL, periodically aggregates them into minute and hour buckets, and exposes APIs for querying both raw events and aggregated metrics.

---

# High-Level Architecture

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
                    (DRF Serializers)
                            │
                     Service Layer
                   (Business Logic)
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
             ┌──────────────┴──────────────┐
             │                             │
       GET /api/events              GET /api/metrics
```

The application follows a layered architecture that separates request validation, business logic, database access, and background processing. Event ingestion is handled synchronously for immediate persistence, while aggregation can be executed either manually through a Django management command or asynchronously through Celery workers using Redis as the message broker. This separation keeps the application modular, maintainable, and scalable.

---

# Architectural Layers

## 1. API Layer

The API layer is implemented using Django REST Framework GenericAPIView and APIView classes.

Responsibilities include:

- Accepting HTTP requests
- Returning HTTP responses
- Delegating business logic
- Triggering serializers

The API layer intentionally contains minimal business logic.

---

## 2. Validation Layer

Incoming requests pass through DRF serializers before reaching the database.

Validation includes:

- Required field validation
- UTC timestamp enforcement
- JSON payload validation
- Maximum payload size validation
- Maximum bulk size (5000 events)

Keeping validation inside serializers ensures consistent behavior across endpoints.

---

## 3. Service Layer

The service layer contains write operations.

Responsibilities include:

- Single event ingestion
- Bulk ingestion
- Transaction handling
- Duplicate detection
- Idempotent inserts

This keeps business rules separate from the HTTP layer.

---

## 4. Selector Layer

Selectors contain all read-only database queries.

Responsibilities include:

- Event filtering
- Metrics filtering
- Stable ordering
- Query optimization

Separating selectors from services makes read operations reusable and improves code organization.

---

# Database Design

The system stores data in three tables.

## Event

The Event table stores every raw event received by the service.

Each record contains:

- Unique event_id
- Tenant identifier
- Event source
- Event type
- UTC timestamp
- JSON payload

A database-level UNIQUE constraint on event_id guarantees idempotency.

Composite indexes were created on frequently queried fields including tenant_id, timestamp, source, and event_type to improve query performance.

---

## EventAggregate

Instead of calculating metrics on every API request, aggregated data is precomputed and stored inside the EventAggregate table.

Each aggregate row represents:

- Tenant
- Minute or hour bucket
- Source
- Event type
- Event count
- First event timestamp
- Last event timestamp

This significantly reduces the cost of metrics queries.

---

## AggregationCheckpoint

AggregationCheckpoint stores the last processed timestamp for each bucket size.

This allows the aggregation worker to process only newly ingested events instead of scanning the complete Event table every execution.

---

# Idempotency Strategy

The assessment requires duplicate requests to be handled safely.

For single-event ingestion, a UNIQUE constraint on event_id combined with transactional handling ensures that duplicate submissions cannot create duplicate rows.

For bulk ingestion, Django's `bulk_create(ignore_conflicts=True)` is used. Duplicate records are ignored efficiently by PostgreSQL without failing the entire request.

This approach remains safe even under concurrent requests.

---

# Aggregation Strategy

The application supports two mechanisms for event aggregation.

## 1. Django Management Command

```bash
python manage.py aggregate_events
```

The management command can be executed manually or scheduled using cron or other schedulers.

## 2. Celery Background Worker

Bulk event ingestion triggers asynchronous aggregation using:

```python
aggregate_events_task.delay()
```

Celery publishes the task to Redis, where a worker processes it independently of the API request lifecycle.

Both implementations perform the same workflow:

1. Read the aggregation checkpoint.
2. Fetch only newly ingested events.
3. Perform database-side `GROUP BY` aggregation.
4. Compute:
   - Count
   - First Seen
   - Last Seen
5. Update the `EventAggregate` table.
6. Persist the latest checkpoint.

Because checkpoints are maintained, aggregation remains incremental and idempotent even if the worker or command is executed multiple times.

---

# API Design Decisions

The application exposes separate endpoints for writes and reads.

### Event APIs

- POST /api/events
- POST /api/events/bulk
- GET /api/events

Raw event queries always require tenant_id and support filtering, pagination, and stable ordering.

### Metrics API

GET /api/metrics never performs in-memory aggregation.

Instead, it reads directly from the EventAggregate table, allowing efficient queries even with large datasets.

---

# Performance Considerations

The implementation includes several production-oriented optimizations to improve throughput and reduce database load.

Implemented optimizations include:

- Composite indexes on frequently filtered columns (`tenant_id`, `timestamp`, `source`, and `event_type`)
- Batch inserts using `bulk_create(batch_size=1000, ignore_conflicts=True)`
- Lazy QuerySet evaluation through Django ORM
- Stable ordering using `timestamp` and `id`
- Pagination to limit response sizes
- Database-level `GROUP BY` aggregation instead of Python-side processing
- Incremental aggregation using checkpoints
- Asynchronous aggregation using Celery workers and Redis
- Database transactions and uniqueness constraints for concurrency-safe writes

These optimizations minimize database round-trips, reduce memory consumption, and improve scalability under high-volume ingestion workloads.

---

# Concurrency Handling

Concurrent requests are handled primarily through database guarantees.

The application relies on:

- Database uniqueness constraints
- Atomic database transactions
- Ignore-conflicts bulk insertion
- Idempotent aggregation

This approach avoids race conditions while keeping the implementation simple and reliable.

---

# Security and Abuse Prevention

Several validation mechanisms help protect the service.

Implemented protections include:

- Maximum payload size (64 KB)
- Maximum bulk size (5000 events)
- Required tenant filtering
- UTC timestamp enforcement
- Input validation using serializers

A production deployment should additionally enable DRF throttling or API gateway rate limiting to protect against abuse.

---

# Scalability

The current implementation is designed to scale both vertically and horizontally.

Current scalability features include:

- PostgreSQL indexing
- Incremental aggregation
- Asynchronous Celery workers
- Redis message broker
- Bulk database operations
- Precomputed metrics
- Separation of read and write responsibilities

Potential future enhancements include:

- Celery Beat for scheduled aggregation
- Kafka-based event streaming
- PostgreSQL table partitioning
- Read replicas
- Distributed Celery workers
- Prometheus monitoring
- OpenTelemetry tracing
- Kubernetes deployment

---
# Design Summary

The architecture emphasizes correctness, maintainability, performance, and scalability through a layered design that separates validation, business logic, query logic, and background processing.

Database constraints and transactions ensure idempotent, concurrency-safe writes, while composite indexes, batch inserts, and database-level aggregation improve query performance and ingestion throughput. Aggregation can be executed either synchronously through a Django management command or asynchronously through Celery workers backed by Redis, providing flexibility for both development and production deployments.

The resulting architecture closely follows production backend engineering practices and satisfies the functional, concurrency, asynchronous processing, and performance requirements of the assessment..