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
        ┌──────────┴──────────┐
        │                     │
 POST /api/events     POST /api/events/bulk
        │                     │
        └──────────┬──────────┘
                   │
          Validation Layer
         (DRF Serializers)
                   │
            Service Layer
      (Business Logic)
                   │
        PostgreSQL (Events)
                   │
      aggregate_events Command
         (Background Worker)
                   │
      Incremental Aggregation
                   │
 PostgreSQL (EventAggregate)
                   │
      GET /api/events
      GET /api/metrics
```

The application follows a layered architecture that separates validation, business logic, database queries, and background processing. This separation keeps the code modular and easier to maintain.

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

Aggregation is implemented as a Django Management Command.

```
python manage.py aggregate_events
```

The command performs the following steps:

1. Read the last checkpoint.
2. Fetch only newly inserted events.
3. Group events by minute or hour.
4. Calculate:
   - Count
   - First Seen
   - Last Seen
5. Update EventAggregate using update_or_create().
6. Store the new checkpoint.

Because checkpoints are maintained, aggregation is incremental and idempotent.

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

Several optimizations were included:

- Composite database indexes
- Pagination for event listing
- Stable ordering using timestamp and id
- bulk_create(ignore_conflicts=True)
- Incremental aggregation
- Database-side GROUP BY operations
- Separation of read and write logic

These optimizations reduce memory usage, improve throughput, and allow the system to scale more effectively.

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

The current implementation is designed to scale through efficient database usage rather than application-level processing.

Possible future improvements include:

- Celery-based asynchronous aggregation
- Redis caching
- Kafka-based ingestion
- Database partitioning
- Horizontal scaling
- Prometheus monitoring
- OpenTelemetry tracing

These improvements can be added without significant architectural changes because responsibilities are already well separated.

---

# Design Summary

The architecture emphasizes correctness, maintainability, and performance by separating validation, business logic, querying, and background processing into dedicated layers.

Idempotent writes, incremental aggregation, database indexing, and precomputed metrics allow the service to handle high-volume event ingestion while providing efficient query performance. The overall design closely aligns with production backend development practices and satisfies the functional and architectural requirements of the assessment.