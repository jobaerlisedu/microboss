from django.core.cache import cache
from ..models import SiteConfig


def get_config(key, default=''):
    cache_key = f'site_config_{key}'
    val = cache.get(cache_key)
    if val is not None:
        return val
    try:
        obj = SiteConfig.objects.get(key=key)
        cache.set(cache_key, obj.value, 300)
        return obj.value
    except SiteConfig.DoesNotExist:
        return default


def set_config(key, value, description=''):
    obj, _ = SiteConfig.objects.update_or_create(key=key, defaults={'value': value, 'description': description})
    cache.set(f'site_config_{key}', value, 300)
    return obj
