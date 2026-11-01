import re

from django import template

register = template.Library()

_LEADING_SYMBOLS = re.compile(r'^[^\w(]+', re.UNICODE)


@register.filter
def plain_title(value):
    """Group names are stored with emoji and dashes for social posts; headings read better without."""
    text = _LEADING_SYMBOLS.sub('', str(value or ''))
    return re.sub(r'\s*[–—]\s*', ', ', text).strip()


@register.filter
def days_left(seconds):
    """'6 days left', '1 day left', or hours in the last day."""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return 'Closed'
    if seconds <= 0:
        return 'Closed'
    days = seconds // 86400
    if days >= 1:
        return f"{days} day{'s' if days != 1 else ''} left"
    hours = max(1, seconds // 3600)
    return f"{hours} hour{'s' if hours != 1 else ''} left"
