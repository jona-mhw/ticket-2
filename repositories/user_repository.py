"""
User Repository - Data access layer for Users
"""
from models import db, User, Superuser


class UserRepository:
    """Repository for User database operations."""

    @staticmethod
    def get_by_id(user_id):
        """Get user by ID."""
        return User.query.get(user_id)

    @staticmethod
    def get_by_username(username):
        """Get user by username."""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_all_by_clinic(clinic_id):
        """Get all users for a clinic."""
        return User.query.filter_by(clinic_id=clinic_id).all()

    @staticmethod
    def get_all_superusers():
        """Get all superusers (users with clinic_id=None and in Superuser table)."""
        superuser_emails = [su.email for su in Superuser.query.all()]
        return User.query.filter(
            User.clinic_id.is_(None),
            User.email.in_(superuser_emails)
        ).all()

    @staticmethod
    def save(user):
        """
        Save user to database.

        Args:
            user: User instance

        Returns:
            User: Saved user
        """
        db.session.add(user)
        return user

    @staticmethod
    def delete(user):
        """
        Delete user from database.

        Args:
            user: User instance
        """
        db.session.delete(user)
