"""
Patient Repository - Data access layer for Patients
"""
from models import db, Patient


class PatientRepository:
    """Repository for Patient database operations."""

    @staticmethod
    def get_by_rut(rut, clinic_id):
        """
        Get patient by RUT and clinic.

        Args:
            rut (str): Patient RUT
            clinic_id (int): Clinic ID

        Returns:
            Patient or None
        """
        return Patient.query.filter_by(rut=rut, clinic_id=clinic_id).first()

    @staticmethod
    def get_or_create(rut, clinic_id):
        """
        Get existing patient or create new one.

        Args:
            rut (str): Patient RUT
            clinic_id (int): Clinic ID

        Returns:
            tuple: (patient, created) where created is a boolean
        """
        patient = PatientRepository.get_by_rut(rut, clinic_id)
        if patient:
            return patient, False

        patient = Patient(rut=rut, clinic_id=clinic_id)
        db.session.add(patient)
        return patient, True

    @staticmethod
    def save(patient):
        """
        Save patient to database.

        Args:
            patient: Patient instance

        Returns:
            Patient: Saved patient
        """
        db.session.add(patient)
        return patient
