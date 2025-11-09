"""
Patient Service - Business logic for patient management
"""
from models import db, Patient


class PatientService:
    """Service for managing patients."""

    @staticmethod
    def get_or_create_patient(rut, clinic_id):
        """
        Get existing patient or create new one.

        Args:
            rut (str): Patient RUT
            clinic_id (int): Clinic ID

        Returns:
            tuple: (patient, created) where created is a boolean
        """
        patient = Patient.query.filter_by(rut=rut, clinic_id=clinic_id).first()
        if patient:
            return patient, False

        patient = Patient(rut=rut, clinic_id=clinic_id)
        db.session.add(patient)
        return patient, True

    @staticmethod
    def update_patient_info(patient, **kwargs):
        """
        Update patient information.

        Args:
            patient: Patient instance to update
            **kwargs: Fields to update

        Returns:
            Patient: Updated patient instance
        """
        for key, value in kwargs.items():
            if hasattr(patient, key):
                setattr(patient, key, value)
        return patient
