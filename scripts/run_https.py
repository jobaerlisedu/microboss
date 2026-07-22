"""Run Django development server with HTTPS using self-signed cert."""
import os
import sys
import ssl
import socket
from wsgiref import simple_server

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
from django.core.wsgi import get_wsgi_application
from django.conf import settings

django.setup()
application = get_wsgi_application()

HOST = '0.0.0.0'
PORT = 8443
CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs')
CERT_FILE = os.path.join(CERT_DIR, 'server.crt')
KEY_FILE = os.path.join(CERT_DIR, 'server.key')

if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
    print(f'Certificate files not found in {CERT_DIR}')
    print('Run: python manage.py runserver 0.0.0.0:8000')
    sys.exit(1)

# Create an HTTPS server
server = simple_server.WSGIServer(
    (HOST, PORT),
    simple_server.WSGIRequestHandler,
)
server.socket = ssl.wrap_socket(
    server.socket,
    certfile=CERT_FILE,
    keyfile=KEY_FILE,
    server_side=True,
    ssl_version=ssl.PROTOCOL_TLS_SERVER,
)

print(f'HTTPS server running on https://127.0.0.1:{PORT}/')
print(f'HTTPS server running on https://localhost:{PORT}/')
print(f'Press Ctrl+C to stop')

try:
    server.serve_forever()
except KeyboardInterrupt:
    print('\nShutting down...')
    server.shutdown()
