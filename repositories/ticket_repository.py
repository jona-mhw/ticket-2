"""
Ticket Repository - Data access layer for Tickets
"""
from models import db, Ticket, Patient, Surgery, Doctor
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_
from datetime import datetime, timedelta
import re


class TicketRepository:
    """Repository for Ticket database operations."""

    @staticmethod
    def get_by_id(ticket_id, clinic_id=None):
        """
        Get ticket by ID with optional clinic filtering.

        Args:
            ticket_id (str): Ticket ID
            clinic_id (int, optional): Filter by clinic

        Returns:
            Ticket or None
        """
        query = Ticket.query.filter_by(id=ticket_id)
        if clinic_id:
            query = query.filter_by(clinic_id=clinic_id)
        return query.first()

    @staticmethod
    def get_with_relations(ticket_id, clinic_id=None):
        """
        Get ticket with all related entities eagerly loaded.

        Args:
            ticket_id (str): Ticket ID
            clinic_id (int, optional): Filter by clinic

        Returns:
            Ticket or None
        """
        query = Ticket.query.options(
            joinedload(Ticket.patient),
            joinedload(Ticket.surgery).joinedload(Surgery.specialty),
            joinedload(Ticket.attending_doctor)
        ).filter_by(id=ticket_id)

        if clinic_id:
            query = query.filter_by(clinic_id=clinic_id)

        return query.first()

    @staticmethod
    def build_filtered_query(filters, current_user):
        """
        Build a filtered query based on search criteria.

        Args:
            filters (dict): Filter parameters
            current_user: Current logged-in user

        Returns:
            Query: SQLAlchemy query object
        """
        # Start with base query with eager loading
        query = Ticket.query.options(
            joinedload(Ticket.patient),
            joinedload(Ticket.surgery).joinedload(Surgery.specialty),
            joinedload(Ticket.attending_doctor)
        ).join(Patient, Ticket.patient_id == Patient.id)\
         .join(Surgery, Ticket.surgery_id == Surgery.id)\
         .outerjoin(Doctor, Ticket.doctor_id == Doctor.id)

        # Apply clinic filter for non-superusers
        if not current_user.is_superuser:
            query = query.filter(
                Ticket.clinic_id == current_user.clinic_id,
                Patient.clinic_id == current_user.clinic_id,
                Surgery.clinic_id == current_user.clinic_id
            )

        # Status filter
        if filters.get('status'):
            if filters['status'] == 'Vigente':
                query = query.filter(
                    Ticket.status == 'Vigente',
                    Ticket.current_fpa > datetime.now()
                )
            else:
                query = query.filter(
                    func.lower(Ticket.status) == func.lower(filters['status'])
                )

        # Search filter (ticket ID, patient name, RUT, bed number, or location)
        if filters.get('search'):
            search_query = filters['search'].strip()
            cleaned_search_rut = re.sub(r'[.-]', '', search_query)
            full_name_expr = Patient.primer_nombre + ' ' + Patient.apellido_paterno
            cleaned_db_rut = func.replace(func.replace(Patient.rut, '.', ''), '-', '')

            query = query.filter(
                db.or_(
                    Ticket.id.ilike(f"%{search_query}%"),
                    full_name_expr.ilike(f"%{search_query}%"),
                    cleaned_db_rut.ilike(f"%{cleaned_search_rut}%"),
                    Ticket.bed_number.ilike(f"%{search_query}%"),
                    Ticket.location.ilike(f"%{search_query}%")
                )
            )

        # Surgery filter
        if filters.get('surgery'):
            query = query.filter(Surgery.id == int(filters['surgery']))

        # Date range filters
        if filters.get('date_from'):
            try:
                date_from_obj = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                query = query.filter(Ticket.created_at >= date_from_obj)
            except (ValueError, TypeError):
                pass

        if filters.get('date_to'):
            try:
                date_to_obj = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                date_to_obj += timedelta(days=1)
                query = query.filter(Ticket.created_at < date_to_obj)
            except (ValueError, TypeError):
                pass

        return query

    @staticmethod
    def apply_sorting(query, sort_by='created_at', sort_dir='desc'):
        """
        Apply sorting to query.

        Args:
            query: SQLAlchemy query
            sort_by (str): Field to sort by
            sort_dir (str): Sort direction ('asc' or 'desc')

        Returns:
            Query: Sorted query
        """
        order_logic = None

        if sort_by == 'patient':
            order_logic = [Patient.apellido_paterno, Patient.apellido_materno, Patient.primer_nombre]
        elif sort_by == 'surgery':
            order_logic = [Surgery.name]
        elif sort_by == 'doctor':
            order_logic = [Doctor.name]
        elif sort_by == 'fpa':
            order_logic = [Ticket.current_fpa]
        elif sort_by == 'medical_discharge_date':
            order_logic = [Ticket.medical_discharge_date]
        elif hasattr(Ticket, sort_by):
            order_logic = [getattr(Ticket, sort_by)]

        if order_logic:
            if sort_dir == 'desc':
                query = query.order_by(*[db.desc(c) for c in order_logic if c is not None])
            else:
                query = query.order_by(*[db.asc(c) for c in order_logic if c is not None])
        else:
            query = query.order_by(db.desc(Ticket.created_at))

        return query

    @staticmethod
    def save(ticket):
        """
        Save ticket to database.

        Args:
            ticket: Ticket instance

        Returns:
            Ticket: Saved ticket
        """
        db.session.add(ticket)
        return ticket

    @staticmethod
    def delete(ticket):
        """
        Delete ticket from database.

        Args:
            ticket: Ticket instance
        """
        db.session.delete(ticket)
