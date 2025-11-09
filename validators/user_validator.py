"""
User Validator - Validation logic for user operations
"""
import re


class UserValidator:
    """Validator for user-related operations."""

    @staticmethod
    def validate_create(form_data):
        """
        Validate user creation data.

        Args:
            form_data: Form data dictionary

        Returns:
            list: List of error messages (empty if valid)
        """
        errors = []

        # Required fields
        required_fields = [
            ('username', 'Nombre de usuario'),
            ('email', 'Email'),
            ('password', 'Contraseña'),
            ('role', 'Rol'),
        ]

        for field, label in required_fields:
            if not form_data.get(field) or not str(form_data.get(field)).strip():
                errors.append(f'{label} es requerido')

        # Email format validation
        email = form_data.get('email', '')
        if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors.append('Email tiene formato inválido')

        # Password strength (minimum 8 characters)
        password = form_data.get('password', '')
        if password and len(password) < 8:
            errors.append('La contraseña debe tener al menos 8 caracteres')

        # Username validation (alphanumeric and underscores only)
        username = form_data.get('username', '')
        if username and not re.match(r'^[\w]+$', username):
            errors.append('El nombre de usuario solo puede contener letras, números y guiones bajos')

        return errors

    @staticmethod
    def validate_update(form_data):
        """
        Validate user update data.

        Args:
            form_data: Form data dictionary

        Returns:
            list: List of error messages (empty if valid)
        """
        errors = []

        # Email format validation if provided
        email = form_data.get('email', '')
        if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors.append('Email tiene formato inválido')

        # Password strength if provided
        password = form_data.get('password', '')
        if password and len(password) < 8:
            errors.append('La contraseña debe tener al menos 8 caracteres')

        return errors
