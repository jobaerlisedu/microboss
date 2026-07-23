"""
cPanel Passenger WSGI entry point.
"""
import os
import sys

# Point to the project root
sys.path.insert(0, os.path.dirname(__file__))

# Set production settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
