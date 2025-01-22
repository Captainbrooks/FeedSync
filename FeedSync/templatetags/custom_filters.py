from django import template

from django.utils import timezone
from datetime import datetime

register = template.Library()

@register.filter
def time_ago(created_at):
    now = timezone.now()
    time_difference = now - created_at

    if time_difference.total_seconds() < 60:
        return "now"
    elif time_difference.total_seconds() < 3600:
        minutes = time_difference.total_seconds() // 60
        return f"{int(minutes)}m"
    elif time_difference.total_seconds() < 86400:
        hours = time_difference.total_seconds() // 3600
        return f"{int(hours)}h"
    else:
        days = time_difference.total_seconds() // 86400
        return f"{int(days)}d"
