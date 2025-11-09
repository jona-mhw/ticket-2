"""
Audit Repository - Data access layer for Audit Logs
"""
from models import db, ActionAudit, LoginAudit
from datetime import datetime, timedelta


class AuditRepository:
    """Repository for Audit database operations."""

    @staticmethod
    def get_action_logs(user_id=None, clinic_id=None, limit=100, offset=0):
        """
        Get action audit logs with optional filtering.

        Args:
            user_id (int, optional): Filter by user
            clinic_id (int, optional): Filter by clinic
            limit (int): Maximum number of records
            offset (int): Offset for pagination

        Returns:
            list: List of ActionAudit records
        """
        query = ActionAudit.query.order_by(ActionAudit.timestamp.desc())

        if user_id:
            query = query.filter_by(user_id=user_id)

        if clinic_id:
            query = query.filter_by(clinic_id=clinic_id)

        return query.limit(limit).offset(offset).all()

    @staticmethod
    def get_login_logs(user_id=None, clinic_id=None, days=30):
        """
        Get login audit logs.

        Args:
            user_id (int, optional): Filter by user
            clinic_id (int, optional): Filter by clinic
            days (int): Number of days to look back

        Returns:
            list: List of LoginAudit records
        """
        since = datetime.utcnow() - timedelta(days=days)
        query = LoginAudit.query.filter(
            LoginAudit.timestamp >= since
        ).order_by(LoginAudit.timestamp.desc())

        if user_id:
            query = query.filter_by(user_id=user_id)

        if clinic_id:
            query = query.filter_by(clinic_id=clinic_id)

        return query.all()

    @staticmethod
    def count_actions_by_user(user_id, days=30):
        """
        Count actions performed by a user in the last N days.

        Args:
            user_id (int): User ID
            days (int): Number of days to look back

        Returns:
            int: Count of actions
        """
        since = datetime.utcnow() - timedelta(days=days)
        return ActionAudit.query.filter(
            ActionAudit.user_id == user_id,
            ActionAudit.timestamp >= since
        ).count()
