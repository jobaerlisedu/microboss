from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Weaker security for local dev
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
