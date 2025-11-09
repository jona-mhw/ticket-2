"""
User Service - Business logic for user management
"""
from models import db, User, Superuser
from .audit_service import AuditService


class UserService:
    """Service for managing users."""

    @staticmethod
    def create_user(username, email, password, role, clinic_id=None):
        """
        Create a new user.

        Args:
            username (str): Username
            email (str): Email address
            password (str): Password (will be hashed)
            role (str): User role
            clinic_id (int, optional): Clinic ID for non-superusers

        Returns:
            User: Created user instance
        """
        user = User(
            username=username,
            email=email,
            role=role,
            clinic_id=clinic_id,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        return user

    @staticmethod
    def update_user(user, **kwargs):
        """
        Update user fields.

        Args:
            user: User instance to update
            **kwargs: Fields to update

        Returns:
            User: Updated user instance
        """
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        return user

    @staticmethod
    def deactivate_user(user, admin_user):
        """
        Deactivate a user.

        Args:
            user: User instance to deactivate
            admin_user: Admin performing the action

        Returns:
            User: Updated user instance
        """
        user.is_active = False
        AuditService.log_action(
            user=admin_user,
            action=f"Desactivó usuario {user.username}",
            target_id=user.id,
            target_type='User'
        )
        return user

    @staticmethod
    def activate_user(user, admin_user):
        """
        Activate a user.

        Args:
            user: User instance to activate
            admin_user: Admin performing the action

        Returns:
            User: Updated user instance
        """
        user.is_active = True
        AuditService.log_action(
            user=admin_user,
            action=f"Activó usuario {user.username}",
            target_id=user.id,
            target_type='User'
        )
        return user
