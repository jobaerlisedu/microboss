import re
from django.urls.converters import StringConverter
from django.urls import register_converter


class HexUUIDConverter(StringConverter):
    """Matches UUIDs with or without hyphens."""
    regex = '[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}'

    def to_python(self, value):
        return value.replace('-', '')

    def to_url(self, value):
        return value.replace('-', '') if isinstance(value, str) else value.hex


register_converter(HexUUIDConverter, 'hexuuid')
