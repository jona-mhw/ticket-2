"""
Repositories Layer - Data Access

This package contains all data access logic.
Repositories handle database queries and should return domain models.
"""

from .ticket_repository import TicketRepository
from .user_repository import UserRepository
from .patient_repository import PatientRepository
from .audit_repository import AuditRepository

__all__ = [
    'TicketRepository',
    'UserRepository',
    'PatientRepository',
    'AuditRepository',
]
