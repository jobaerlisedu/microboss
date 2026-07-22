# Deployment Guide

## Prerequisites

- Python 3.12+
- MySQL 8.0+
- Redis 7+ (for caching and background tasks)
- Node.js (for static asset building, if applicable)

## Development

```bash
# Clone and enter project
cd content-tracker/cms

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements/dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## Production (Docker)

```bash
# Build and start
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## Production (Manual)

```bash
# Install production dependencies
pip install -r requirements/prod.txt

# Set environment variables
export DJANGO_SETTINGS_MODULE=config.settings.prod
export DJANGO_SECRET_KEY=your-secret-key
export DB_NAME=content_tracker
export DB_USER=user
export DB_PASSWORD=password

# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## Environment Variables

See `.env.example` for all required variables.
