"""
Ticket Service - Business logic for ticket management

This service handles all ticket-related business logic including creation,
modification, and cancellation.
"""
from datetime import datetime
from models import db, Ticket, FpaModification
from .fpa_calculator import FPACalculator
from .audit_service import AuditService
from utils.string_utils import generate_prefix


class TicketService:
    """Service for managing tickets (patient discharge tracking)."""

    @staticmethod
    def generate_ticket_id(clinic):
        """
        Generate unique ticket ID in format TH-PREFIX-YYYY-XXX.

        Args:
            clinic: Clinic model instance

        Returns:
            str: Generated ticket ID (e.g., "TH-SANT-2025-001")
        """
        current_year = datetime.now().year
        clinic_prefix = generate_prefix(clinic.name).upper()

        year_prefix = f"TH-{clinic_prefix}-{current_year}-"
        last_ticket = Ticket.query.filter(
            Ticket.id.like(f"{year_prefix}%"),
            Ticket.clinic_id == clinic.id
        ).order_by(Ticket.id.desc()).first()

        if last_ticket:
            last_number_str = last_ticket.id.split('-')[-1]
            last_number = int(last_number_str)
            new_number = last_number + 1
        else:
            new_number = 1

        return f"TH-{clinic_prefix}-{current_year}-{new_number:03d}"

    @staticmethod
    def create_ticket(ticket_data, user):
        """
        Create a new ticket with all business logic applied.

        Args:
            ticket_data (dict): Dictionary containing ticket data
            user: Current user creating the ticket

        Returns:
            Ticket: Created ticket instance
        """
        # Calculate system FPA (automatic calculation for reference)
        system_fpa, system_overnight_stays = FPACalculator.calculate(
            ticket_data['pavilion_end_time'],
            ticket_data['surgery']
        )

        # Use initial_fpa and current_fpa from ticket_data if provided (Issue #40)
        # This allows the medical decision to override the automatic calculation
        initial_fpa = ticket_data.get('initial_fpa', system_fpa)
        current_fpa = ticket_data.get('current_fpa', system_fpa)

        # Recalculate overnight_stays based on the actual FPA being used
        if 'initial_fpa' in ticket_data and ticket_data['initial_fpa'] != system_fpa:
            # Medical FPA is different, recalculate overnight stays
            time_diff = initial_fpa - ticket_data['pavilion_end_time']
            overnight_stays = max(0, time_diff.days)
            if time_diff.seconds > 0:
                overnight_stays += 1
        else:
            # Using system FPA, use system calculated overnight stays
            overnight_stays = system_overnight_stays

        # Generate ticket ID
        ticket_id = TicketService.generate_ticket_id(ticket_data['clinic'])

        # Issue #87: medical_discharge_date is now automatically set to initial_fpa.date()
        # (no more manual override allowed)

        # Create ticket
        ticket = Ticket(
            id=ticket_id,
            patient_id=ticket_data['patient'].id,
            surgery_id=ticket_data['surgery'].id,
            doctor_id=ticket_data.get('doctor_id'),
            clinic_id=ticket_data['clinic'].id,
            pavilion_end_time=ticket_data['pavilion_end_time'],
            medical_discharge_date=ticket_data['initial_fpa'].date(),
            system_calculated_fpa=system_fpa,
            initial_fpa=initial_fpa,
            current_fpa=current_fpa,
            overnight_stays=overnight_stays,
            original_overnight_stays=overnight_stays,
            original_fpa_date=initial_fpa.date(),
            bed_number=ticket_data.get('bed_number'),
            location=ticket_data.get('location'),
            status=ticket_data.get('status', 'Vigente'),
            created_by=user.username,
            surgery_name_snapshot=ticket_data['surgery'].name,
            surgery_base_hours_snapshot=ticket_data['surgery'].base_stay_hours,
        )

        db.session.add(ticket)

        # Log creation
        AuditService.log_action(
            user=user,
            action=f"Creó ticket para paciente {ticket_data['patient'].full_name}",
            target_id=ticket_id,
            target_type='Ticket'
        )

        return ticket

    @staticmethod
    def modify_fpa(ticket, new_fpa, reason, justification, user):
        """
        Modify the FPA of a ticket.

        Args:
            ticket: Ticket instance to modify
            new_fpa (datetime): New FPA value
            reason (str): Standardized reason for modification
            justification (str): Additional justification text
            user: User performing the modification

        Returns:
            FpaModification: Created modification record
        """
        if not ticket.can_be_modified():
            raise ValueError("El ticket no puede ser modificado (no está vigente)")

        # Save previous FPA before updating ticket (needed for audit log)
        previous_fpa = ticket.current_fpa

        # Create modification record
        modification = FpaModification(
            ticket_id=ticket.id,
            clinic_id=ticket.clinic_id,
            previous_fpa=previous_fpa,
            new_fpa=new_fpa,
            reason=reason,
            justification=justification,
            modified_by=user.username
        )

        # Update ticket
        ticket.current_fpa = new_fpa

        db.session.add(modification)

        # Log modification
        AuditService.log_action(
            user=user,
            action=f"Modificó FPA de {previous_fpa} a {new_fpa}. Razón: {reason}",
            target_id=ticket.id,
            target_type='Ticket'
        )

        return modification

    @staticmethod
    def annul_ticket(ticket, reason, user):
        """
        Annul a ticket.

        Args:
            ticket: Ticket instance to annul
            reason (str): Reason for annulment
            user: User performing the annulment

        Returns:
            Ticket: Updated ticket instance
        """
        ticket.status = 'Anulado'
        ticket.annulled_at = datetime.utcnow()
        ticket.annulled_by = user.username
        ticket.annulled_reason = reason

        # Log annulment
        AuditService.log_action(
            user=user,
            action=f"Anuló ticket. Razón: {reason}",
            target_id=ticket.id,
            target_type='Ticket'
        )

        return ticket

    @staticmethod
    def restore_ticket(ticket, user):
        """
        Restore an annulled ticket to active status.

        Args:
            ticket: Ticket instance to restore
            user: User performing the restoration

        Returns:
            Ticket: Updated ticket instance
        """
        ticket.status = 'Vigente'
        ticket.annulled_at = None
        ticket.annulled_by = None
        ticket.annulled_reason = None

        # Log restoration
        AuditService.log_action(
            user=user,
            action="Restauró ticket anulado",
            target_id=ticket.id,
            target_type='Ticket'
        )

        return ticket
