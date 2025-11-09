"""
Ticket Validator - Validation logic for ticket operations
"""
from datetime import datetime


class TicketValidator:
    """Validator for ticket-related operations."""

    @staticmethod
    def validate_create(form_data):
        """
        Validate ticket creation data.

        Args:
            form_data: Form data dictionary or request.form

        Returns:
            list: List of error messages (empty if valid)
        """
        errors = []

        # Required fields
        required_fields = [
            ('rut', 'RUT del paciente'),
            ('primer_nombre', 'Primer nombre'),
            ('apellido_paterno', 'Apellido paterno'),
            ('age', 'Edad'),
            ('sex', 'Sexo'),
            ('surgery_id', 'Cirugía'),
            ('medical_discharge_date', 'Fecha de alta médica'),
            ('pavilion_end_time', 'Hora de fin de pabellón'),
        ]

        for field, label in required_fields:
            if not form_data.get(field) or not str(form_data.get(field)).strip():
                errors.append(f'{label} es requerido')

        # Age validation
        try:
            age = int(form_data.get('age', 0))
            if age < 0 or age > 150:
                errors.append('Edad debe estar entre 0 y 150 años')
        except (ValueError, TypeError):
            errors.append('Edad debe ser un número válido')

        # Date validations
        try:
            pavilion_end_time = datetime.strptime(
                form_data.get('pavilion_end_time', ''),
                '%Y-%m-%dT%H:%M'
            )
            # Pavilion end time shouldn't be in the future
            if pavilion_end_time > datetime.now():
                errors.append('La hora de fin de pabellón no puede estar en el futuro')
        except (ValueError, TypeError):
            errors.append('Hora de fin de pabellón inválida')

        try:
            datetime.strptime(
                form_data.get('medical_discharge_date', ''),
                '%Y-%m-%d'
            )
        except (ValueError, TypeError):
            errors.append('Fecha de alta médica inválida')

        return errors

    @staticmethod
    def validate_fpa_modification(form_data):
        """
        Validate FPA modification data.

        Args:
            form_data: Form data dictionary

        Returns:
            list: List of error messages (empty if valid)
        """
        errors = []

        # Required fields
        if not form_data.get('new_fpa'):
            errors.append('Nueva FPA es requerida')

        if not form_data.get('reason'):
            errors.append('Razón de modificación es requerida')

        # Date validation
        try:
            new_fpa = datetime.strptime(
                form_data.get('new_fpa', ''),
                '%Y-%m-%dT%H:%M'
            )
            # FPA should be in the future
            if new_fpa <= datetime.now():
                errors.append('La nueva FPA debe estar en el futuro')
        except (ValueError, TypeError):
            errors.append('Nueva FPA inválida')

        return errors

    @staticmethod
    def validate_annulment(form_data):
        """
        Validate ticket annulment data.

        Args:
            form_data: Form data dictionary

        Returns:
            list: List of error messages (empty if valid)
        """
        errors = []

        if not form_data.get('annulled_reason'):
            errors.append('Razón de anulación es requerida')

        return errors
