from django import template

register = template.Library()

EN_MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]


@register.filter
def bn_date(date_obj):
    if not date_obj:
        return ''
    d, m, y = date_obj.day, date_obj.month, date_obj.year
    return f'{d} {EN_MONTHS[m - 1]} {y}'


@register.filter
def bn_number(num):
    return str(num) if num is not None else ''


@register.filter
def get_item(d, key):
    val = d.get(key) if isinstance(d, dict) else None
    return val if val is not None else ''

@register.filter
def split(value, delimiter):
    return value.split(delimiter) if value else []

@register.filter
def list_index(lst, i):
    try:
        return lst[i]
    except (IndexError, TypeError, ValueError):
        return ''
