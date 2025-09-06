from datetime import datetime
from zoneinfo import ZoneInfo
from flask import current_app

def localtime(value, tz="America/New_York"):
    """
    Convert a UTC datetime to local time zone string.
    """
    if value is None:
        return ""
    return value.astimezone(ZoneInfo(tz)).strftime("%Y-%m-%d %H:%M")

def register_filters(app):
    app.add_template_filter(localtime)
