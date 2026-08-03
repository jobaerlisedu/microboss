# Content Tracker — Architecture

## Overview

Content Tracker is a Django 5.2 ERP/CRM system for managing digital content production, including entry tracking, sponsor assignment, and content management.

## Architecture Principles

- **Modular design** with loosely coupled apps
- **API-first** with RESTful JSON endpoints (DRF) + HTMX-driven web UI
- **Domain-driven** layout separating business logic from presentation
- **Tenant-ready** architecture with organization isolation built into models

## Project Layout

```
microboss/
├── apps/              # Django apps (presentation layer)
│   ├── accounts/      # Auth: User model, JWT views, session management
│   ├── cms/           # HTMX web UI: all CMS views and admin panel
│   ├── content/       # ContentEntry model, CRUD, stats
│   ├── sponsors/      # Sponsor model, tracking
│   ├── leaders/       # Leaderboard queries
│   ├── reports/       # Report builder, PDF generation (WeasyPrint)
│   ├── analytics/     # Dashboard KPIs and analytics
│   ├── audit/         # AuditLog, request context middleware
│   ├── notices/       # Notice model
│   ├── notifications/ # In-app + FCM push, device tokens
│   ├── hr/            # Duty roster, shift, leave management
│   └── common/        # Shared: BaseModel, mixins, pagination, permissions
├── config/            # Django configuration
│   ├── settings/      # Environment-specific settings (base/dev/prod)
│   ├── urls.py        # Root URL configuration
│   ├── asgi.py        # ASGI entry point
│   └── wsgi.py        # WSGI entry point
├── infrastructure/    # Cross-cutting concerns
│   └── middleware/     # Custom middleware
├── templates/         # Django templates
├── static/            # Static assets (CSS, JS, images)
├── media/             # User-uploaded files
├── locale/            # Translation files (Bengali)
├── docker/            # Docker config
├── scripts/           # Ops/dev scripts
├── docs/              # Documentation
├── tests/             # Integration tests
└── requirements/      # Python dependency files
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2, Python 3.12 |
| API | Django REST Framework 3.17 |
| Auth | SimpleJWT (JWT) + Session |
| Database | MySQL 8 (utf8mb4) |
| Frontend | HTMX + server-rendered Django templates |
| PDF | WeasyPrint (with HTML fallback) |
| Push | Firebase Cloud Messaging (optional) |
| Cache | Redis (optional) |
| Translation | Bengali (bn), locale files |

## Key Design Decisions

1. **UUID primary keys** — all models use UUID for distributed compatibility
2. **Soft deletes** — BaseModel provides `deleted_at` and `is_active` for recoverability
3. **Audit trail** — All model changes are logged to AuditLog via signals
4. **Unified API** — DRF with consistent pagination, filtering, and throttling
5. **HTMX-driven UI** — Server-rendered HTML with AJAX partial page updates
