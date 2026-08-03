import os
import importlib

# Determine which settings module to load
env = os.environ.get('DJANGO_SETTINGS_MODULE', '')

if env:
    try:
        importlib.import_module(env)
        settings_module = env
    except ImportError:
        settings_module = 'config.settings.dev'
elif 'prod' in env:
    settings_module = 'config.settings.prod'
else:
    settings_module = 'config.settings.dev'

# Load the settings module
mod = importlib.import_module(settings_module)

# Copy all public names into this namespace
for attr in dir(mod):
    if attr.isupper():
        globals()[attr] = getattr(mod, attr)
