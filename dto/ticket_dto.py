"""
Ticket DTO - Data Transfer Object for Ticket operations
"""
from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class TicketDTO:
    """
    Data Transfer Object for Ticket creation and updates.

    This class encapsulates ticket data being transferred between layers,
    decoupling the presentation layer from the business logic layer.
    """
    patient: object
    surgery: object
    clinic: object
    pavilion_end_time: datetime
    medical_discharge_date: datetime.date
    doctor_id: Optional[int] = None
    discharge_slot_id: Optional[int] = None
    room: Optional[str] = None
    status: str = 'Vigente'
    initial_fpa: Optional[datetime] = None
    current_fpa: Optional[datetime] = None
    initial_reason: Optional[str] = None
    initial_justification: Optional[str] = None

    @classmethod
    def from_form(cls, form_data, patient, surgery, clinic):
        """
        Create TicketDTO from form data.

        Args:
            form_data: Flask request.form or dict
            patient: Patient model instance
            surgery: Surgery model instance
            clinic: Clinic model instance

        Returns:
            TicketDTO: Populated DTO instance
        """
        pavilion_end_time = datetime.strptime(
            form_data.get('pavilion_end_time'),
            '%Y-%m-%dT%H:%M'
        )

        medical_discharge_date = datetime.strptime(
            form_data.get('medical_discharge_date'),
            '%Y-%m-%d'
        ).date()

        doctor_id = form_data.get('doctor_id')
        doctor_id = int(doctor_id) if doctor_id else None

        discharge_slot_id = form_data.get('discharge_slot_id')
        discharge_slot_id = int(discharge_slot_id) if discharge_slot_id else None

        # Handle custom FPA if provided
        initial_fpa = None
        current_fpa = None
        if form_data.get('custom_fpa'):
            try:
                custom_fpa = datetime.strptime(
                    form_data.get('custom_fpa'),
                    '%Y-%m-%dT%H:%M'
                )
                initial_fpa = custom_fpa
                current_fpa = custom_fpa
            except (ValueError, TypeError):
                pass

        return cls(
            patient=patient,
            surgery=surgery,
            clinic=clinic,
            pavilion_end_time=pavilion_end_time,
            medical_discharge_date=medical_discharge_date,
            doctor_id=doctor_id,
            discharge_slot_id=discharge_slot_id,
            room=form_data.get('room', '').strip() or None,
            status=form_data.get('status', 'Vigente'),
            initial_fpa=initial_fpa,
            current_fpa=current_fpa,
            initial_reason=form_data.get('initial_reason'),
            initial_justification=form_data.get('initial_justification')
        )
