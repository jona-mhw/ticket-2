"""
Routes Utils - Compatibility wrappers for refactored code

This module provides backward compatibility wrappers for old function names.
All logic has been moved to services, repositories, and utils modules.

DEPRECATED: This file exists only for backward compatibility.
New code should import directly from services, repositories, and utils.
"""
from flask_login import current_user
from services import AuditService
from repositories import TicketRepository
from utils.datetime_utils import calculate_time_remaining
from utils.string_utils import generate_prefix


def log_action(action, target_id=None, target_type=None):
    """
    DEPRECATED: Use AuditService.log_action() instead.

    Wrapper for backward compatibility.
    """
    return AuditService.log_action(
        user=current_user,
        action=action,
        target_id=target_id,
        target_type=target_type
    )


def _build_tickets_query(filters):
    """
    DEPRECATED: Use TicketRepository.build_filtered_query() instead.

    Wrapper for backward compatibility.
    """
    return TicketRepository.build_filtered_query(filters, current_user)


def apply_sorting_to_query(query, sort_by, sort_dir):
    """
    DEPRECATED: Use TicketRepository.apply_sorting() instead.

    Wrapper for backward compatibility.
    """
    return TicketRepository.apply_sorting(query, sort_by, sort_dir)


# Re-export for backward compatibility
__all__ = [
    'log_action',
    'generate_prefix',
    '_build_tickets_query',
    'apply_sorting_to_query',
    'calculate_time_remaining',
]
