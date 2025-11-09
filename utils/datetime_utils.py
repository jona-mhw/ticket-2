"""
DateTime Utilities - Helper functions for date and time operations
"""
from datetime import datetime


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

    now = datetime.now()
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
