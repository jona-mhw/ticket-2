from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from models import (
    db, Ticket, Patient, Surgery, Specialty, Clinic,
    FpaModification, StandardizedReason, Doctor, DischargeTimeSlot,
    TICKET_STATUS_VIGENTE, TICKET_STATUS_ANULADO,
    REASON_CATEGORY_INITIAL, REASON_CATEGORY_MODIFICATION, REASON_CATEGORY_ANNULMENT
)
from datetime import datetime, timedelta, time
import json
from .utils import _build_tickets_query, calculate_time_remaining, apply_sorting_to_query, generate_prefix

tickets_bp = Blueprint('tickets', __name__)

def generate_ticket_id(clinic_id):
    """Generate unique ticket ID in format TH-PREFIX-YYYY-XXX"""
    clinic = Clinic.query.get(clinic_id)
    if not clinic:
        raise ValueError("Invalid clinic_id for generating ticket ID")

    current_year = datetime.now().year
    clinic_prefix = generate_prefix(clinic.name).upper()
    
    year_prefix = f"TH-{clinic_prefix}-{current_year}-"
    last_ticket = Ticket.query.filter(
        Ticket.id.like(f"{year_prefix}%"),
        Ticket.clinic_id == clinic_id
    ).order_by(Ticket.id.desc()).first()
    
    if last_ticket:
        last_number_str = last_ticket.id.split('-')[-1]
        last_number = int(last_number_str)
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"TH-{clinic_prefix}-{current_year}-{new_number:03d}"

def calculate_time_remaining(fpa):
    """Calculate detailed time remaining until FPA."""
    if not fpa:
        return None
    
    now = datetime.now()
    if fpa <= now:
        return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0, 'expired': True}
    
    time_diff = fpa - now
    days = time_diff.days
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'expired': False
    }

@tickets_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    clinics = Clinic.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        try:
            if current_user.is_superuser:
                clinic_id_str = request.form.get('clinic_id')
                if not clinic_id_str:
                    flash('Debe seleccionar una clínica.', 'error')
                    return redirect(url_for('tickets.create'))
                clinic_id = int(clinic_id_str)
            else:
                clinic_id = current_user.clinic_id

            rut = request.form.get('rut', '').strip()
            primer_nombre = request.form.get('primer_nombre', '').strip()
            apellido_paterno = request.form.get('apellido_paterno', '').strip()
            age = int(request.form.get('age', 0))
            sex = request.form.get('sex', '')
            surgery_id = int(request.form.get('surgery_id'))
            medical_discharge_date = datetime.strptime(request.form.get('medical_discharge_date'), '%Y-%m-%d').date()
            pavilion_end_time = datetime.strptime(request.form.get('pavilion_end_time'), '%Y-%m-%dT%H:%M')

            if not all([rut, primer_nombre, apellido_paterno, age, sex, surgery_id, medical_discharge_date, clinic_id]):
                flash('Todos los campos obligatorios deben ser completados.', 'error')
                return redirect(url_for('tickets.create'))

            patient = Patient.query.filter_by(rut=rut, clinic_id=clinic_id).first()
            if not patient:
                patient = Patient(rut=rut, clinic_id=clinic_id)
                db.session.add(patient)
            
            patient.primer_nombre = primer_nombre
            patient.segundo_nombre = request.form.get('segundo_nombre', '').strip()
            patient.apellido_paterno = apellido_paterno
            patient.apellido_materno = request.form.get('apellido_materno', '').strip()
            patient.age = age
            patient.sex = sex
            patient.episode_id = request.form.get('episode_id', '').strip()

            surgery = Surgery.query.filter_by(id=surgery_id, clinic_id=clinic_id).first_or_404()
            ticket_id = generate_ticket_id(clinic_id)
            system_calculated_fpa, overnight_stays = Ticket().calculate_fpa(pavilion_end_time, surgery)
            
            final_fpa = system_calculated_fpa # Default to system calculated
            discharge_slot = DischargeTimeSlot.query.filter(
                DischargeTimeSlot.start_time <= final_fpa.time(),
                DischargeTimeSlot.end_time >= final_fpa.time(),
                DischargeTimeSlot.clinic_id == clinic_id
            ).first()

            ticket = Ticket(
                id=ticket_id, patient=patient, surgery_id=surgery_id,
                doctor_id=request.form.get('doctor_id', type=int),
                room=request.form.get('room', '').strip(),
                pavilion_end_time=pavilion_end_time,
                created_by=current_user.username, clinic_id=clinic_id,
                medical_discharge_date=medical_discharge_date,
                system_calculated_fpa=system_calculated_fpa,
                initial_fpa=final_fpa, 
                current_fpa=final_fpa, 
                overnight_stays=overnight_stays,
                discharge_slot_id=discharge_slot.id if discharge_slot else None,
                surgery_name_snapshot=surgery.name,
                surgery_base_hours_snapshot=surgery.base_stay_hours
            )
            
            db.session.add(ticket)
            db.session.commit()
            
            flash(f'Ticket {ticket_id} creado exitosamente.', 'success')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el ticket: {str(e)}', 'error')
    
    # GET request
    specialties_query = Specialty.query.filter_by(is_active=True)
    surgeries_query = Surgery.query.filter_by(is_active=True)
    doctors_query = Doctor.query.filter_by(is_active=True)
    # Razones de Discrepancia Inicial (para cuando el médico cambia la FPA calculada al crear)
    reasons_query = StandardizedReason.query.filter_by(category=REASON_CATEGORY_INITIAL, is_active=True)

    if not current_user.is_superuser:
        specialties_query = specialties_query.filter_by(clinic_id=current_user.clinic_id)
        surgeries_query = surgeries_query.filter_by(clinic_id=current_user.clinic_id)
        doctors_query = doctors_query.filter_by(clinic_id=current_user.clinic_id)
        reasons_query = reasons_query.filter_by(clinic_id=current_user.clinic_id)

    specialties = specialties_query.order_by(Specialty.name).all()
    surgeries = surgeries_query.all()
    doctors = doctors_query.order_by(Doctor.name).all()
    initial_reasons = reasons_query.all()

    # Preparar datos para JavaScript (incluir clinic_id)
    specialties_data = [{'id': s.id, 'name': s.name, 'clinic_id': s.clinic_id} for s in specialties]
    surgeries_data = [{'id': s.id, 'name': s.name, 'base_stay_hours': s.base_stay_hours, 'specialty_id': s.specialty_id, 'clinic_id': s.clinic_id} for s in surgeries]
    doctors_data = [{'id': d.id, 'name': d.name, 'specialty': d.specialty, 'clinic_id': d.clinic_id} for d in doctors]
    # Razones con clinic_id para filtrado dinámico en superusuarios
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
    data = request.get_json()
    surgery_id = data.get('surgery_id')
    pavilion_end_time_str = data.get('pavilion_end_time')
    clinic_id = data.get('clinic_id')

    # Para usuarios normales, usar su clinic_id; para superusuarios, requerir clinic_id en el request
    if not current_user.is_superuser:
        clinic_id = current_user.clinic_id
    elif not clinic_id:
        return jsonify({'error': 'clinic_id es requerido para superusuarios'}), 400

    if not all([surgery_id, pavilion_end_time_str, clinic_id]):
        return jsonify({'error': 'Faltan datos requeridos (surgery_id, pavilion_end_time, clinic_id)'}), 400

    try:
        surgery = Surgery.query.filter_by(id=surgery_id, clinic_id=clinic_id).first()
        if not surgery:
            return jsonify({'error': 'Cirugía no encontrada para la clínica especificada'}), 404

        pavilion_end_time = datetime.fromisoformat(pavilion_end_time_str)

        system_fpa, _ = Ticket().calculate_fpa(pavilion_end_time, surgery)

        slot = DischargeTimeSlot.query.filter(
            DischargeTimeSlot.start_time <= system_fpa.time(),
            DischargeTimeSlot.end_time >= system_fpa.time(),
            DischargeTimeSlot.clinic_id == clinic_id
        ).first()

        return jsonify({
            'fpa_date_iso': system_fpa.date().isoformat(),
            'fpa_time': system_fpa.strftime('%H:%M'),
            'fpa_display_str': f"{system_fpa.strftime('%d/%m/%Y')} (Bloque: {slot.name if slot else 'N/A'})",
            'surgery_base_stay_hours': surgery.base_stay_hours
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tickets_bp.route('/<ticket_id>')
@login_required
def detail(ticket_id):
    # Eager loading de todas las relaciones necesarias para evitar N+1 queries
    query = Ticket.query.options(
        joinedload(Ticket.patient),
        joinedload(Ticket.surgery).joinedload(Surgery.specialty),
        joinedload(Ticket.attending_doctor),
        joinedload(Ticket.discharge_time_slot),
        joinedload(Ticket.clinic)
    ).filter_by(id=ticket_id)

    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)
    ticket = query.first_or_404()
    
    reasons_query = StandardizedReason.query.filter_by(is_active=True)
    slots_query = DischargeTimeSlot.query.filter_by(is_active=True)
    
    clinic_id_to_filter = ticket.clinic_id
    
    reasons_query = reasons_query.filter_by(clinic_id=clinic_id_to_filter)
    slots_query = slots_query.filter_by(clinic_id=clinic_id_to_filter)

    modification_reasons = reasons_query.filter_by(category='modification').all()
    annulment_reasons = reasons_query.filter_by(category='annulment').all()
    discharge_time_slots = slots_query.order_by(DischargeTimeSlot.start_time).all()
    
    return render_template('tickets/detail.html', 
                         ticket=ticket, 
                         modification_reasons=modification_reasons, annulment_reasons=annulment_reasons,
                         discharge_time_slots=discharge_time_slots)

@tickets_bp.route('/<ticket_id>/update_fpa', methods=['POST'])
@login_required
def update_fpa(ticket_id):
    query = Ticket.query.options(
        joinedload(Ticket.patient),
        joinedload(Ticket.surgery),
        joinedload(Ticket.discharge_time_slot)
    ).filter_by(id=ticket_id)
    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)
    ticket = query.first_or_404()
    
    if not ticket.can_be_modified():
        flash('Este ticket no puede ser modificado.', 'error')
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))
    
    if ticket.get_modification_count() >= 5:
        flash('Se ha alcanzado el límite máximo de modificaciones (5).', 'error')
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))
    
    try:
        new_fpa_date_str = request.form.get('new_fpa_date')
        discharge_slot_id = request.form.get('discharge_slot_id')
        reason = request.form.get('reason')
        justification = request.form.get('justification', '').strip()
        
        if not all([new_fpa_date_str, discharge_slot_id, reason]):
            flash('La fecha, el rango horario y la razón son obligatorios.', 'error')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))

        new_fpa_date = datetime.strptime(new_fpa_date_str, '%Y-%m-%d').date()
        slot = DischargeTimeSlot.query.get(discharge_slot_id)
        if not slot:
            flash('Rango horario no válido.', 'error')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))

        new_fpa = datetime.combine(new_fpa_date, slot.start_time)
        
        modification = FpaModification(
            ticket_id=ticket_id,
            clinic_id=ticket.clinic_id,
            previous_fpa=ticket.current_fpa,
            new_fpa=new_fpa,
            reason=reason,
            justification=justification,
            modified_by=current_user.username
        )
        
        ticket.current_fpa = new_fpa
        ticket.discharge_slot_id = discharge_slot_id

        time_diff = new_fpa - ticket.pavilion_end_time
        overnight_stays = max(0, time_diff.days)
        if time_diff.seconds > 0:
            overnight_stays += 1
        ticket.overnight_stays = overnight_stays
        
        db.session.add(modification)
        db.session.commit()
        
        flash('FPA modificada exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al modificar FPA: {str(e)}', 'error')
    
    return redirect(url_for('tickets.detail', ticket_id=ticket_id))

@tickets_bp.route('/<ticket_id>/annul', methods=['POST'])
@login_required
def annul_ticket(ticket_id):
    query = Ticket.query.options(
        joinedload(Ticket.patient),
        joinedload(Ticket.surgery)
    ).filter_by(id=ticket_id)
    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)
    ticket = query.first_or_404()

    if not ticket.can_be_modified():
        flash('Este ticket no puede ser anulado.', 'error')
        return redirect(url_for('tickets.detail', ticket_id=ticket_id))
    try:
        annulled_reason = request.form.get('annulled_reason')
        if not annulled_reason:
            flash('La razón de anulación es obligatoria.', 'error')
            return redirect(url_for('tickets.detail', ticket_id=ticket_id))
            
        ticket.status = 'Anulado'
        ticket.annulled_at = datetime.utcnow()
        ticket.annulled_by = current_user.username
        ticket.annulled_reason = annulled_reason
        
        db.session.commit()
        flash(f'Ticket {ticket.id} anulado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al anular el ticket: {str(e)}', 'error')
        
    return redirect(url_for('tickets.detail', ticket_id=ticket_id))


@tickets_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    filters = {
        'status': request.args.get('status', ''),
        'search': request.args.get('search', ''),
        'surgery': request.args.get('surgery', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
        'compliance': request.args.get('compliance', '')
    }
    sort_by = request.args.get('sort_by', 'created_at')
    sort_dir = request.args.get('sort_dir', 'desc')

    query = _build_tickets_query(filters)
    query = apply_sorting_to_query(query, sort_by, sort_dir)

    total = query.count()
    tickets = query.offset((page - 1) * per_page).limit(per_page).all()
    
    for ticket in tickets:
        ticket.is_scheduled = False
        if ticket.status == 'Vigente' and ticket.current_fpa:
            if datetime.now() < ticket.pavilion_end_time:
                ticket.is_scheduled = True
                ticket.time_remaining = None
            else:
                ticket.time_remaining = calculate_time_remaining(ticket.current_fpa)
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
                         search_query=filters.get('search', ''),
                         date_from=filters.get('date_from', ''),
                         date_to=filters.get('date_to', ''),
                         page=page,
                         per_page=per_page,
                         total=total)

@tickets_bp.route('/<ticket_id>/pdf')
@login_required
def export_pdf(ticket_id):
    query = Ticket.query.filter_by(id=ticket_id)
    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)
    ticket = query.first_or_404()
    # ... PDF generation logic remains the same ...

@tickets_bp.route('/<ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    query = Ticket.query.filter_by(id=ticket_id)
    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)
    ticket = query.first_or_404()

    if not (current_user.is_admin() or current_user.username == ticket.created_by or current_user.is_superuser):
        flash('No tiene permiso para editar este ticket.', 'danger')
        return redirect(url_for('tickets.nursing_board'))

    if request.method == 'POST':
        # ... (logic for editing ticket)
        pass

    # GET Request
    surgeries_query = Surgery.query.filter_by(is_active=True)
    doctors_query = Doctor.query.filter_by(is_active=True)
    reasons_query = StandardizedReason.query.filter_by(category=REASON_CATEGORY_ANNULMENT, is_active=True)

    if not current_user.is_superuser:
        surgeries_query = surgeries_query.filter_by(clinic_id=current_user.clinic_id)
        doctors_query = doctors_query.filter_by(clinic_id=current_user.clinic_id)
        reasons_query = reasons_query.filter_by(clinic_id=current_user.clinic_id)

    surgeries = surgeries_query.all()
    doctors = doctors_query.all()
    annulment_reasons = reasons_query.all()
    
    return render_template('admin/edit_ticket.html', 
                           ticket=ticket,
                           surgeries=surgeries,
                           doctors=doctors,
                           annulment_reasons=annulment_reasons)

@tickets_bp.route('/manage')
@login_required
def manage_my_tickets():
    if current_user.is_admin():
        return redirect(url_for('admin.manage_tickets'))

    search_query = request.args.get('search', '')
    query = Ticket.query.filter(Ticket.created_by == current_user.username)

    if search_query:
        search_term = f"%{search_query}%"
        query = query.join(Patient).filter(
            db.or_(
                Ticket.id.ilike(search_term),
                Patient.rut.ilike(search_term),
                Patient.primer_nombre.ilike(search_term),
                Patient.apellido_paterno.ilike(search_term)
            )
        )

    tickets = query.order_by(Ticket.created_at.desc()).all()

    return render_template('tickets/manage_my_tickets.html', tickets=tickets, search_query=search_query)

@tickets_bp.route('/nursing')
@login_required
def nursing_board():
    session['last_ticket_view'] = 'tickets.nursing_board'
    """Vista optimizada para estación de enfermería - diseño tipo tablero con cards visuales."""
    filters = {
        'status': request.args.get('status', ''),  # No filtrar por defecto, _build_tickets_query se encarga
        'search': request.args.get('search', ''),
        'room': request.args.get('room', ''),
        'urgency': request.args.get('urgency', '')  # critical, warning, normal
    }

    query = _build_tickets_query(filters)

    # Filtrar solo vigentes (no anulados) y ordenar por urgencia (FPA más cercano primero)
    query = query.filter(Ticket.status == TICKET_STATUS_VIGENTE).order_by(Ticket.current_fpa.asc())

    tickets = query.all()

    # Calcular tiempo restante y clasificar por urgencia
    for ticket in tickets:
        if ticket.current_fpa:
            if datetime.now() < ticket.pavilion_end_time:
                ticket.is_scheduled = True
                ticket.time_remaining = None
                ticket.urgency_level = 'scheduled'
            else:
                ticket.is_scheduled = False
                ticket.time_remaining = calculate_time_remaining(ticket.current_fpa)

                # Clasificar urgencia
                if ticket.time_remaining and ticket.time_remaining['expired']:
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

    # Ordenar: vigentes (normal) primero, luego por FPA
    urgency_priority = {'normal': 0, 'warning': 1, 'critical': 2, 'scheduled': 3, 'expired': 4, 'unknown': 5}
    tickets.sort(key=lambda t: (urgency_priority.get(t.urgency_level, 99), t.current_fpa if t.current_fpa else datetime.max))

    # Filtrar por urgencia si se especifica
    if filters['urgency']:
        tickets = [t for t in tickets if t.urgency_level == filters['urgency']]

    # Estadísticas rápidas
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
    session['last_ticket_view'] = 'tickets.nursing_list'
    """Vista de lista mejorada para estación de enfermería - formato tabla con selector de columnas."""
    filters = {
        'status': request.args.get('status', ''),
        'search': request.args.get('search', ''),
        'room': request.args.get('room', ''),
        'urgency': request.args.get('urgency', '')
    }

    # Columnas visibles (por defecto o desde query params)
    visible_columns = request.args.getlist('cols') or ['patient', 'rut', 'room', 'fpa', 'time_slot', 'status', 'countdown']

    query = _build_tickets_query(filters)
    query = query.filter(Ticket.status == TICKET_STATUS_VIGENTE).order_by(Ticket.current_fpa.asc())
    tickets = query.all()

    # Calcular tiempo restante y clasificar por urgencia
    for ticket in tickets:
        if ticket.current_fpa:
            if datetime.now() < ticket.pavilion_end_time:
                ticket.is_scheduled = True
                ticket.time_remaining = None
                ticket.urgency_level = 'scheduled'
            else:
                ticket.is_scheduled = False
                ticket.time_remaining = calculate_time_remaining(ticket.current_fpa)

                if ticket.time_remaining and ticket.time_remaining['expired']:
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

    # Ordenar: vigentes (normal) primero, luego por FPA
    urgency_priority = {'normal': 0, 'warning': 1, 'critical': 2, 'scheduled': 3, 'expired': 4, 'unknown': 5}
    tickets.sort(key=lambda t: (urgency_priority.get(t.urgency_level, 99), t.current_fpa if t.current_fpa else datetime.max))

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

@tickets_bp.route('/api/update-room', methods=['POST'])
@login_required
def api_update_room():
    """API endpoint para actualizar la cama del paciente desde el tablero de enfermería."""
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    room = data.get('room', '').strip()

    if not ticket_id:
        return jsonify({'error': 'ticket_id es requerido'}), 400

    # Buscar ticket
    query = Ticket.query.filter_by(id=ticket_id)
    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)

    ticket = query.first()
    if not ticket:
        return jsonify({'error': 'Ticket no encontrado'}), 404

    try:
        # Actualizar cama del ticket
        ticket.room = room if room else None
        db.session.commit()
        return jsonify({
            'success': True,
            'room': room if room else 'Sin cama',
            'message': f'Cama actualizada a: {room if room else "Sin cama"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
