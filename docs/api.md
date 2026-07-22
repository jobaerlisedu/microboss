# API Documentation

Base URL: `/api/v1/`

Authentication: Bearer JWT token or Session cookie.

## Auth

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register/` | POST | Register new user |
| `/auth/login/` | POST | Login, returns JWT |
| `/auth/logout/` | POST | Logout (invalidates refresh token) |
| `/auth/me/` | GET | Current user profile |
| `/auth/users/` | GET | List all users (admin) |
| `/auth/users/{id}/` | GET | User detail |
| `/auth/sessions/` | GET | Current user sessions |
| `/auth/sessions/all/` | GET | All sessions (admin) |
| `/auth/admin-reset-password/` | POST | Admin password reset |
| `/auth/password-reset/` | POST | Request password reset |
| `/auth/password-reset/confirm/` | POST | Confirm password reset |

## Entries

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/entries/` | GET, POST | List / Create entries |
| `/entries/{id}/` | GET, PUT, PATCH, DELETE | Entry detail |
| `/entries/stats/` | GET | Entry statistics |
| `/entries/by-month/` | GET | Entries grouped by month |

## Sponsors

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sponsors/` | GET, POST | List / Create sponsors |
| `/sponsors/{id}/` | GET, PUT, PATCH, DELETE | Sponsor detail |
| `/sponsors/{id}/track/` | GET | Sponsor tracking info |

## Content Lists

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/content-lists/` | GET, POST | List / Create content list items |
| `/content-lists/{id}/` | GET, PUT, PATCH, DELETE | Content list item detail |
| `/content-lists/stats/` | GET | Content list statistics |

## Assignments

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/assignments/` | GET, POST | List / Create assignments |
| `/assignments/{id}/` | GET, PUT, PATCH, DELETE | Assignment detail |
| `/assignments/{id}/status/` | PATCH | Update assignment status |
| `/assignments/stats/` | GET | Assignment statistics |

## Scripts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scripts/` | GET, POST | List / Create scripts |
| `/scripts/{id}/` | GET, PUT, PATCH, DELETE | Script detail |
| `/scripts/{id}/submit/` | POST | Submit script for approval |
| `/scripts/{id}/approve/` | POST | Approve script |
| `/scripts/stats/` | GET | Script statistics |

## Notifications

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notifications/` | GET | List notifications (paginated) |
| `/notifications/{id}/read/` | POST | Mark notification as read |
| `/notifications/read-all/` | POST | Mark all as read |
| `/notifications/devices/` | POST | Register device token |
| `/notifications/devices/unregister/` | POST | Unregister device token |

## Notices

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notices/` | GET | List notices |
| `/notices/{id}/` | GET | Notice detail |

## Reports

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reports/content-report/` | GET | Generate content report PDF |
| `/reports/script-pdf/{id}/` | GET | Generate script PDF |

## Leaders

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/leaders/` | GET | Leaderboard |
| `/leaders/user-entries/{id}/` | GET | User entries detail |

## JWT

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/token/` | POST | Obtain JWT token pair |
| `/api/token/refresh/` | POST | Refresh JWT token |
