"""
Tickets Routes - Controllers for ticket management

This module contains route handlers (controllers) for ticket operations.
All business logic has been moved to the services layer.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from models import (
    db, Ticket, Patient, Surgery, Specialty, Clinic,
    StandardizedReason, Doctor,
    # Issue #54: DischargeTimeSlot eliminado - se usa TimeBlockHelper
    TICKET_STATUS_VIGENTE, REASON_CATEGORY_INITIAL,
    REASON_CATEGORY_MODIFICATION, REASON_CATEGORY_ANNULMENT
)
from datetime import datetime
from services import TicketService, FPACalculator, AuditService
from repositories import TicketRepository, PatientRepository
from validators import TicketValidator
from dto import TicketDTO
from utils import calculate_time_remaining
from utils.time_blocks import TimeBlockHelper

tickets_bp = Blueprint('tickets', __name__)


@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new ticket."""
    clinics = Clinic.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        try:
            # Determine clinic
            if current_user.is_superuser:
                clinic_id = int(request.form.get('clinic_id'))
                clinic = Clinic.query.get_or_404(clinic_id)
            else:
                clinic_id = current_user.clinic_id
                clinic = current_user.clinic

            # Validate input
            errors = TicketValidator.validate_create(request.form)
            if errors:
                for error in errors:
                    flash(error, 'error')
                return redirect(url_for('tickets.create'))

            # Get or create patient
            patient, _ = PatientRepository.get_or_create(
                rut=request.form.get('rut').strip(),
                clinic_id=clinic_id
            )

            # Update patient info
            patient.primer_nombre = request.form.get('primer_nombre', '').strip()
            patient.segundo_nombre = request.form.get('segundo_nombre', '').strip()
            patient.apellido_paterno = request.form.get('apellido_paterno', '').strip()
            patient.apellido_materno = request.form.get('apellido_materno', '').strip()
            patient.age = int(request.form.get('age'))
            patient.sex = request.form.get('sex')
            patient.episode_id = request.form.get('episode_id', '').strip()

            # Get surgery
            surgery = Surgery.query.filter_by(
                id=int(request.form.get('surgery_id')),
                clinic_id=clinic_id
            ).first_or_404()

            # Prepare ticket data
            pavilion_end_time = datetime.strptime(
                request.form.get('pavilion_end_time'),
                '%Y-%m-%dT%H:%M'
            )
            medical_discharge_date = datetime.strptime(
                request.form.get('medical_discharge_date'),
                '%Y-%m-%d'
            ).date()

            # Calculate system FPA (automatic calculation)
            from datetime import time
            system_fpa, _ = FPACalculator.calculate(pavilion_end_time, surgery)

            # Determine if medical discharge date is different from system calculation
            # If different, use medical date as FPA (Issue #40)
            if medical_discharge_date != system_fpa.date():
                # Convert medical date to datetime with default time block (18:00)
                # This ensures the medical decision overrides the automatic calculation
                medical_fpa_datetime = datetime.combine(medical_discharge_date, time(18, 0))
                initial_fpa = medical_fpa_datetime
                current_fpa = medical_fpa_datetime
            else:
                # If dates match, use system calculated FPA (includes correct time)
                initial_fpa = system_fpa
                current_fpa = system_fpa

            ticket_data = {
                'patient': patient,
                'surgery': surgery,
                'clinic': clinic,
                'pavilion_end_time': pavilion_end_time,
                'medical_discharge_date': medical_discharge_date,
                'initial_fpa': initial_fpa,
                'current_fpa': current_fpa,
                'doctor_id': int(request.form.get('doctor_id')) if request.form.get('doctor_id') else None,
                'room': request.form.get('room', '').strip() or None,
                'initial_reason': request.form.get('initial_reason'),
                'initial_justification': request.form.get('initial_justification')
            }

            # Create ticket using service
            ticket = TicketService.create_ticket(ticket_data, current_user)
            db.session.commit()

            flash(f'Ticket {ticket.id} creado exitosamente.', 'success')
            return redirect(url_for('tickets.detail', ticket_id=ticket.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el ticket: {str(e)}', 'error')
            return redirect(url_for('tickets.create'))

    # GET request - load form data
    specialties_query = Specialty.query.filter_by(is_active=True)
    surgeries_query = Surgery.query.filter_by(is_active=True)
    doctors_query = Doctor.query.filter_by(is_active=True)
    reasons_query = StandardizedReason.query.filter_by(
        category=REASON_CATEGORY_INITIAL,
        is_active=True
    )

    if not current_user.is_superuser:
        specialties_query = specialties_query.filter_by(clinic_id=current_user.clinic_id)
        surgeries_query = surgeries_query.filter_by(clinic_id=current_user.clinic_id)
        doctors_query = doctors_query.filter_by(clinic_id=current_user.clinic_id)
        reasons_query = reasons_query.filter_by(clinic_id=current_user.clinic_id)

    specialties = specialties_query.order_by(Specialty.name).all()
    surgeries = surgeries_query.all()
    doctors = doctors_query.order_by(Doctor.name).all()
    initial_reasons = reasons_query.all()

    # Prepare data for JavaScript
    specialties_data = [{'id': s.id, 'name': s.name, 'clinic_id': s.clinic_id} for s in specialties]
    surgeries_data = [{'id': s.id, 'name': s.name, 'base_stay_hours': s.base_stay_hours,
                      'specialty_id': s.specialty_id, 'clinic_id': s.clinic_id} for s in surgeries]
    doctors_data = [{'id': d.id, 'name': d.name, 'specialty': d.specialty,
                    'clinic_id': d.clinic_id} for d in doctors]
    initial_reasons_data = [{'id': r.id, 'reason': r.reason, 'clinic_id': r.clinic_id} for r in initial_reasons]

    return render_template('tickets/create.html',
                         specialties_data=specialties_data,
                         surgeries_data=surgeries_data,
                         doctors_data=doctors_data,
                         initial_reasons_data=initial_reasons_data,
                         clinics=clinics)


@tickets_bp.route('/api/calculate-fpa', methods=['POST'])
@login_required
def api_calculate_fpa():
    """API endpoint to calculate FPA based on surgery and time."""
    data = request.get_json()
    surgery_id = data.get('surgery_id')
    pavilion_end_time_str = data.get('pavilion_end_time')
    clinic_id = data.get('clinic_id')

    if not current_user.is_superuser:
        clinic_id = current_user.clinic_id
    elif not clinic_id:
        return jsonify({'error': 'clinic_id es requerido para superusuarios'}), 400

    if not all([surgery_id, pavilion_end_time_str, clinic_id]):
        return jsonify({'error': 'Faltan datos requeridos'}), 400

    try:
        surgery = Surgery.query.filter_by(id=surgery_id, clinic_id=clinic_id).first()
        if not surgery:
            return jsonify({'error': 'Cirugía no encontrada'}), 404

        pavilion_end_time = datetime.fromisoformat(pavilion_end_time_str)
        system_fpa, _ = FPACalculator.calculate(pavilion_end_time, surgery)

        # Issue #54: Usar TimeBlockHelper en vez de buscar en BD
        block = TimeBlockHelper.get_block_for_time(system_fpa)

        return jsonify({
            'fpa_date_iso': system_fpa.date().isoformat(),
            'fpa_time': system_fpa.strftime('%H:%M'),
            'fpa_display_str': f"{system_fpa.strftime('%d/%m/%Y')} (Bloque: {block['label']})",
            'surgery_base_stay_hours': surgery.base_stay_hours
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tickets_bp.route('/<ticket_id>')
@login_required
def detail(ticket_id):
    """View ticket details."""
    ticket = TicketRepository.get_with_relations(
        ticket_id,
        clinic_id=None if current_user.is_superuser else current_user.clinic_id
    )

    if not ticket:
        flash('Ticket no encontrado', 'error')
        return redirect(url_for('tickets.list'))

    # Load reasons for the ticket's clinic
    reasons_query = StandardizedReason.query.filter_by(
        is_active=True,
        clinic_id=ticket.clinic_id
    )

    modification_reasons = reasons_query.filter_by(category='modification').all()
    annulment_reasons = reasons_query.filter_by(category='annulment').all()

    # Issue #54: Generar bloques dinámicamente con TimeBlockHelper
    discharge_time_slots = TimeBlockHelper.get_all_blocks()

    return render_template('tickets/detail.html',
                         ticket=ticket,
                         modification_reasons=modification_reasons,
                         annulment_reasons=annulment_reasons,
                         discharge_time_slots=discharge_time_slots)


@tickets_bp.route('/<ticket_id>/update_fpa', methods=['POST'])
@login_required
def update_fpa(ticket_id):
    """Modify ticket FPA."""
    ticket = TicketRepository.get_with_relations(
        ticket_id,
        clinic_id=None if current_user.is_superuser else current_user.clinic_id
    )

    if not ticket:
        flash('Ticket no encontrado', 'error')
        return redirect(url_for('tickets.list'))

    if not ticket.can_be_modified():
        flash('Este ticket no puede ser modificado.', 'error')
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))

    if ticket.get_modification_count() >= 5:
        flash('Se ha alcanzado el límite máximo de modificaciones (5).', 'error')
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))

    # Validate
    errors = TicketValidator.validate_fpa_modification(request.form)
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))

    try:
        new_fpa_date = datetime.strptime(request.form.get('new_fpa_date'), '%Y-%m-%d').date()

        # Issue #54: Usar discharge_end_hour directamente en vez de buscar en BD
        discharge_end_hour = request.form.get('discharge_end_hour')
        if not discharge_end_hour:
            flash('Rango horario no válido.', 'error')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))

        # Convertir hora a objeto time
        end_time = TimeBlockHelper.get_end_time(int(discharge_end_hour))

        # IMPORTANTE: El FPA representa el FIN del bloque horario
        # Ejemplo: bloque "14:00 - 16:00" → FPA = 16:00 → se calcula como bloque 14:00-16:00
        new_fpa = datetime.combine(new_fpa_date, end_time)
        reason = request.form.get('reason')
        justification = request.form.get('justification', '').strip()

        # Use service to modify
        TicketService.modify_fpa(ticket, new_fpa, reason, justification, current_user)

        # Recalculate overnight stays
        time_diff = new_fpa - ticket.pavilion_end_time
        overnight_stays = max(0, time_diff.days)
        if time_diff.seconds > 0:
            overnight_stays += 1
        ticket.overnight_stays = overnight_stays

        db.session.commit()
        flash('FPA modificada exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al modificar FPA: {str(e)}', 'error')

    return redirect(url_for('tickets.detail', ticket_id=ticket_id))


@tickets_bp.route('/<ticket_id>/annul', methods=['POST'])
@login_required
def annul_ticket(ticket_id):
    """Annul a ticket."""
    ticket = TicketRepository.get_with_relations(
        ticket_id,
        clinic_id=None if current_user.is_superuser else current_user.clinic_id
    )

    if not ticket:
        flash('Ticket no encontrado', 'error')
        return redirect(url_for('tickets.list'))

    if not ticket.can_be_modified():
        flash('Este ticket no puede ser anulado.', 'error')
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))

    # Validate
    errors = TicketValidator.validate_annulment(request.form)
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))

    try:
        reason = request.form.get('annulled_reason')
        TicketService.annul_ticket(ticket, reason, current_user)
        db.session.commit()
        flash(f'Ticket {ticket.id} anulado exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al anular el ticket: {str(e)}', 'error')

    return redirect(url_for('tickets.detail', ticket_id=ticket_id))


@tickets_bp.route('/')
@login_required
def list():
    """List tickets with filters and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    filters = {
        'status': request.args.get('status', ''),
        'search': request.args.get('search', ''),
        'surgery': request.args.get('surgery', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
    }
    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')

    query = TicketRepository.build_filtered_query(filters, current_user)
    query = TicketRepository.apply_sorting(query, sort_by, sort_dir)

    total = query.count()
    tickets = query.offset((page - 1) * per_page).limit(per_page).all()

    # Add time remaining data
    for ticket in tickets:
        if ticket.status == 'Vigente' and ticket.current_fpa:
            ticket.is_scheduled = datetime.now() < ticket.pavilion_end_time
            ticket.time_remaining = None if ticket.is_scheduled else calculate_time_remaining(ticket.current_fpa)
        else:
            ticket.time_remaining = None

    surgeries_query = Surgery.query.filter_by(is_active=True)
    if not current_user.is_superuser:
        surgeries_query = surgeries_query.filter_by(clinic_id=current_user.clinic_id)
    surgeries = surgeries_query.all()

    return render_template('tickets/list.html',
                         tickets=tickets,
                         surgeries=surgeries,
                         filters=filters,
                         page=page,
                         per_page=per_page,
                         total=total)


@tickets_bp.route('/nursing')
@login_required
def nursing_board():
    """Nursing board view - visual cards with urgency levels."""
    session['last_ticket_view'] = 'tickets.nursing_board'

    filters = {
        'status': request.args.get('status', ''),
        'search': request.args.get('search', ''),
        'room': request.args.get('room', ''),
        'urgency': request.args.get('urgency', '')
    }

    query = TicketRepository.build_filtered_query(filters, current_user)
    query = query.order_by(Ticket.current_fpa.asc())
    tickets = query.all()

    # Calculate urgency levels
    for ticket in tickets:
        if ticket.current_fpa:
            ticket.is_scheduled = datetime.now() < ticket.pavilion_end_time
            ticket.time_remaining = None if ticket.is_scheduled else calculate_time_remaining(ticket.current_fpa)

            if ticket.is_scheduled:
                ticket.urgency_level = 'scheduled'
            elif ticket.time_remaining and ticket.time_remaining['expired']:
                ticket.urgency_level = 'expired'
            elif ticket.time_remaining:
                total_hours = ticket.time_remaining['days'] * 24 + ticket.time_remaining['hours']
                if total_hours <= 1:
                    ticket.urgency_level = 'critical'
                elif total_hours <= 6:
                    ticket.urgency_level = 'warning'
                else:
                    ticket.urgency_level = 'normal'
        else:
            ticket.time_remaining = None
            ticket.urgency_level = 'unknown'

    # Sort by urgency
    urgency_priority = {'normal': 0, 'warning': 1, 'critical': 2, 'scheduled': 3, 'expired': 4, 'unknown': 5}
    tickets.sort(key=lambda t: (urgency_priority.get(t.urgency_level, 99),
                               t.current_fpa if t.current_fpa else datetime.max))

    # Filter by urgency if specified
    if filters['urgency']:
        tickets = [t for t in tickets if t.urgency_level == filters['urgency']]

    # Calculate stats
    stats = {
        'total': len(tickets),
        'critical': len([t for t in tickets if t.urgency_level == 'critical']),
        'warning': len([t for t in tickets if t.urgency_level == 'warning']),
        'normal': len([t for t in tickets if t.urgency_level == 'normal']),
        'expired': len([t for t in tickets if t.urgency_level == 'expired']),
        'scheduled': len([t for t in tickets if t.urgency_level == 'scheduled'])
    }

    return render_template('tickets/nursing_board.html',
                         tickets=tickets,
                         filters=filters,
                         stats=stats)


@tickets_bp.route('/nursing-list')
@login_required
def nursing_list():
    """Nursing list view - table format with customizable columns."""
    session['last_ticket_view'] = 'tickets.nursing_list'

    filters = {
        'status': request.args.get('status', ''),
        'search': request.args.get('search', ''),
        'room': request.args.get('room', ''),
        'urgency': request.args.get('urgency', '')
    }

    visible_columns = request.args.getlist('cols') or [
        'patient', 'rut', 'room', 'fpa', 'time_slot', 'status', 'countdown'
    ]

    query = TicketRepository.build_filtered_query(filters, current_user)
    query = query.order_by(Ticket.current_fpa.asc())
    tickets = query.all()

    # Calculate urgency (same logic as nursing_board)
    for ticket in tickets:
        if ticket.current_fpa:
            ticket.is_scheduled = datetime.now() < ticket.pavilion_end_time
            ticket.time_remaining = None if ticket.is_scheduled else calculate_time_remaining(ticket.current_fpa)

            if ticket.is_scheduled:
                ticket.urgency_level = 'scheduled'
            elif ticket.time_remaining and ticket.time_remaining['expired']:
                ticket.urgency_level = 'expired'
            elif ticket.time_remaining:
                total_hours = ticket.time_remaining['days'] * 24 + ticket.time_remaining['hours']
                ticket.urgency_level = 'critical' if total_hours <= 1 else 'warning' if total_hours <= 6 else 'normal'
        else:
            ticket.time_remaining = None
            ticket.urgency_level = 'unknown'

    urgency_priority = {'normal': 0, 'warning': 1, 'critical': 2, 'scheduled': 3, 'expired': 4, 'unknown': 5}
    tickets.sort(key=lambda t: (urgency_priority.get(t.urgency_level, 99),
                               t.current_fpa if t.current_fpa else datetime.max))

    if filters['urgency']:
        tickets = [t for t in tickets if t.urgency_level == filters['urgency']]

    stats = {
        'total': len(tickets),
        'critical': len([t for t in tickets if t.urgency_level == 'critical']),
        'warning': len([t for t in tickets if t.urgency_level == 'warning']),
        'normal': len([t for t in tickets if t.urgency_level == 'normal']),
        'expired': len([t for t in tickets if t.urgency_level == 'expired']),
        'scheduled': len([t for t in tickets if t.urgency_level == 'scheduled'])
    }

    return render_template('tickets/nursing_list.html',
                         tickets=tickets,
                         filters=filters,
                         stats=stats,
                         visible_columns=visible_columns)


@tickets_bp.route('/api/update-bed-location', methods=['POST'])
@login_required
def api_update_bed_location():
    """API endpoint to update patient bed number and location from nursing board."""
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    field = data.get('field')  # 'bed_number' or 'location'
    value = data.get('value', '').strip()

    if not ticket_id:
        return jsonify({'error': 'ticket_id es requerido'}), 400

    if not field or field not in ['bed_number', 'location']:
        return jsonify({'error': 'field debe ser bed_number o location'}), 400

    # Validaciones de longitud
    if field == 'bed_number' and value and len(value) > 10:
        return jsonify({'error': 'Número de cama no puede exceder 10 caracteres'}), 400
    if field == 'location' and value and len(value) > 50:
        return jsonify({'error': 'Ubicación no puede exceder 50 caracteres'}), 400

    ticket = TicketRepository.get_by_id(
        ticket_id,
        clinic_id=None if current_user.is_superuser else current_user.clinic_id
    )

    if not ticket:
        return jsonify({'error': 'Ticket no encontrado'}), 404

    try:
        # Actualizar el campo correspondiente
        if field == 'bed_number':
            ticket.bed_number = value if value else None
            field_label = 'cama'
            display_value = value if value else 'Sin asignar'
        else:  # location
            ticket.location = value if value else None
            field_label = 'ubicación'
            display_value = value if value else 'Sin especificar'

        AuditService.log_action(
            user=current_user,
            action=f"Actualizó {field_label} a: {display_value}",
            target_id=ticket_id,
            target_type='Ticket'
        )
        db.session.commit()

        return jsonify({
            'success': True,
            'field': field,
            'value': display_value,
            'message': f'{field_label.capitalize()} actualizada correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@tickets_bp.route('/manage-my-tickets')
@login_required
def manage_my_tickets():
    """Manage tickets created by the current user."""
    search_query = request.args.get('search', '').strip()
    
    # Build query for tickets created by current user
    query = Ticket.query.filter_by(created_by=current_user.username)
    
    # Apply clinic filter for non-superusers
    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)
    
    # Apply search filter if provided
    if search_query:
        query = query.join(Patient).filter(
            db.or_(
                Ticket.id.like(f'%{search_query}%'),
                Patient.rut.like(f'%{search_query}%'),
                db.func.concat(
                    Patient.primer_nombre, ' ',
                    Patient.segundo_nombre, ' ',
                    Patient.apellido_paterno, ' ',
                    Patient.apellido_materno
                ).like(f'%{search_query}%')
            )
        )
    
    # Order by creation date descending
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    return render_template('tickets/manage_my_tickets.html',
                         tickets=tickets,
                         search_query=search_query)
