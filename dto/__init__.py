"""
DTOs (Data Transfer Objects)

This package contains data transfer objects used to pass data between layers.
DTOs are simple data containers without business logic.
"""

from .ticket_dto import TicketDTO

__all__ = [
    'TicketDTO',
]
