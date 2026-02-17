"""
DateTime Utilities - Helper functions for date and time operations

DECISIÓN DE TIMEZONE (2026-02-16):
    La aplicación almacena y compara todos los datetimes en UTC (naive).
    Cloud Run usa UTC por defecto, por lo que datetime.utcnow() es consistente.
    La conversión a hora Chile (America/Santiago) solo ocurre en la capa de presentación
    mediante el filtro Jinja2 'datetime_local' definido en app.py.
    Los usuarios ingresan horas locales (Chile) que se almacenan tal cual como naive UTC,
    lo cual funciona correctamente porque el servidor opera en UTC.
"""
from datetime import datetime


def utcnow():
    """Return current UTC time. Single source of truth for 'now' across the app."""
    return datetime.utcnow()


def calculate_time_remaining(fpa):
    """
    Calculate detailed time remaining until FPA.

    Args:
        fpa: datetime object representing the FPA (Fecha Probable de Alta)

    Returns:
        dict: Dictionary with days, hours, minutes, seconds, and expired flag
        None: if fpa is None
    """
    if not fpa:
        return None

    now = utcnow()
    if fpa <= now:
        return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0, 'expired': True}

    time_diff = fpa - now
    days = time_diff.days
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'expired': False
    }
