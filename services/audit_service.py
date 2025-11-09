"""
Audit Service - Business logic for audit logging

This service centralizes all audit logging functionality.
"""
from models import db, ActionAudit


class AuditService:
    """Service for logging user actions and maintaining audit trail."""

    @staticmethod
    def log_action(user, action, target_id=None, target_type=None):
        """
        Logs an action performed by a user.

        Args:
            user: User model instance (must be authenticated)
            action (str): Description of the action performed
            target_id (str, optional): ID of the target entity
            target_type (str, optional): Type of the target entity (e.g., 'Ticket', 'User')

        Returns:
            ActionAudit: The created audit log entry
        """
        if not user or not user.is_authenticated:
            return None

        log_entry = ActionAudit(
            user_id=user.id,
            username=user.username,
            clinic_id=user.clinic_id,
            action=action,
            target_id=str(target_id) if target_id else None,
            target_type=target_type
        )
        db.session.add(log_entry)
        return log_entry
