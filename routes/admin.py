"""
Admin Routes - Controllers for admin operations

This module contains route handlers (controllers) for administrative tasks.
Uses centralized decorators and services from refactored architecture.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, send_file
from flask_login import login_required, current_user
from models import (
    db, User, Surgery, Specialty, StandardizedReason, Doctor,
    Clinic, LoginAudit, Ticket, Patient, REASON_CATEGORY_ANNULMENT,
    FpaModification, ActionAudit, Superuser, ROLE_SUPERUSER, ROLE_ADMIN, UrgencyThreshold
)
from datetime import datetime, time
from utils import admin_required, superuser_required
from services import AuditService, UserService
from repositories import TicketRepository, AuditRepository
import openpyxl
from io import BytesIO

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/ticket/<ticket_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_ticket(ticket_id):
    query = Ticket.query.filter_by(id=ticket_id)
    if not current_user.is_superuser:
        query = query.filter_by(clinic_id=current_user.clinic_id)
    ticket = query.first_or_404()

    # Bloquear edición de tickets Anulados o Vencidos
    from datetime import datetime
    ticket_is_readonly = False
    readonly_reason = ""

    if ticket.status == 'Anulado':
        ticket_is_readonly = True
        readonly_reason = "Este ticket está anulado y no puede ser modificado."
    elif ticket.current_fpa and ticket.current_fpa < datetime.now():
        ticket_is_readonly = True
        readonly_reason = "Este ticket está vencido y no puede ser modificado."

    if request.method == 'POST':
        if ticket_is_readonly:
            flash(readonly_reason, 'error')
            return redirect(url_for('tickets.detail', ticket_id=ticket.id))
        try:
            # --- Patient Data ---
            patient = ticket.patient
            patient_changes = []
            if patient.rut != request.form['rut']: patient_changes.append(f"RUT de '{patient.rut}' a '{request.form['rut']}'")
            patient.rut = request.form['rut']
            if patient.primer_nombre != request.form['primer_nombre']: patient_changes.append(f"Primer Nombre de '{patient.primer_nombre}' a '{request.form['primer_nombre']}'")
            patient.primer_nombre = request.form['primer_nombre']
            if patient.segundo_nombre != request.form['segundo_nombre']: patient_changes.append(f"Segundo Nombre de '{patient.segundo_nombre}' a '{request.form['segundo_nombre']}'")
            patient.segundo_nombre = request.form['segundo_nombre']
            if patient.apellido_paterno != request.form['apellido_paterno']: patient_changes.append(f"Apellido Paterno de '{patient.apellido_paterno}' a '{request.form['apellido_paterno']}'")
            patient.apellido_paterno = request.form['apellido_paterno']
            if patient.apellido_materno != request.form['apellido_materno']: patient_changes.append(f"Apellido Materno de '{patient.apellido_materno}' a '{request.form['apellido_materno']}'")
            patient.apellido_materno = request.form['apellido_materno']
            if patient.age != int(request.form['age']): patient_changes.append(f"Edad de '{patient.age}' a '{request.form['age']}'")
            patient.age = int(request.form['age'])
            if patient.sex != request.form['sex']: patient_changes.append(f"Sexo de '{patient.sex}' a '{request.form['sex']}'")
            patient.sex = request.form['sex']


            
            if patient_changes:
                AuditService.log_action(
                    user=current_user,
                    action=f"Editó paciente: {', '.join(patient_changes)}",
                    target_id=ticket.id,
                    target_type='Ticket'
                )

            # --- Ticket Data ---
            ticket_changes = []
            new_room = request.form.get('room', '').strip()
            # Fix for Issue #70: Use bed_number instead of room
            if ticket.bed_number != new_room:
                ticket_changes.append(f"Habitación/Cama de '{ticket.bed_number or ''}' a '{new_room}'")
                ticket.bed_number = new_room

            # NOTE: Status is NOT modifiable from this form
            # Use specific actions (annul ticket, etc.) to change status

            # NOTE: pavilion_end_time is intentionally not modifiable
            # It's set at ticket creation and should remain unchanged

            if ticket.surgery_id != int(request.form['surgery_id']): ticket_changes.append(f"Cirugía ID de '{ticket.surgery_id}' a '{request.form['surgery_id']}'")
            ticket.surgery_id = int(request.form['surgery_id'])

            doctor_id = request.form.get('doctor_id')
            new_doctor_id = int(doctor_id) if doctor_id else None
            if ticket.doctor_id != new_doctor_id: ticket_changes.append(f"Doctor ID de '{ticket.doctor_id}' a '{new_doctor_id}'")
            ticket.doctor_id = new_doctor_id

            if ticket_changes:
                AuditService.log_action(
                    user=current_user,
                    action=f"Editó ticket: {', '.join(ticket_changes)}",
                    target_id=ticket.id,
                    target_type='Ticket'
                )

            db.session.commit()
            flash('Ticket actualizado exitosamente.', 'success')
            return redirect(url_for('tickets.detail', ticket_id=ticket.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el ticket: {str(e)}', 'error')

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
                           annulment_reasons=annulment_reasons,
                           ticket_is_readonly=ticket_is_readonly,
                           readonly_reason=readonly_reason)

@admin_bp.route('/tickets')
@login_required
@admin_required
def manage_tickets():
    search_query = request.args.get('search', '')
    filters = {'search': search_query}
    query = _build_tickets_query(filters)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return render_template('admin/manage_tickets.html', tickets=tickets, search_query=search_query)

@admin_bp.route('/')
@login_required
@admin_required
def index():
    stats_user_query = User.query.filter_by(is_active=True)
    stats_doctor_query = Doctor.query.filter_by(is_active=True)
    stats_surgery_query = Surgery.query.filter_by(is_active=True)
    stats_specialty_query = Specialty.query.filter_by(is_active=True)
    stats_reason_query = StandardizedReason.query.filter_by(is_active=True)

    if not current_user.is_superuser:
        stats_user_query = stats_user_query.filter_by(clinic_id=current_user.clinic_id)
        stats_doctor_query = stats_doctor_query.filter_by(clinic_id=current_user.clinic_id)
        stats_surgery_query = stats_surgery_query.filter_by(clinic_id=current_user.clinic_id)
        stats_specialty_query = stats_specialty_query.filter_by(clinic_id=current_user.clinic_id)
        # Fix for Issue #69: stats_timeslot_query was undefined and causing crash
        # stats_timeslot_query = stats_timeslot_query.filter_by(clinic_id=current_user.clinic_id)
        stats_reason_query = stats_reason_query.filter_by(clinic_id=current_user.clinic_id)

    stats = {
        'users': stats_user_query.count(),
        'doctors': stats_doctor_query.count(),
        'surgeries': stats_surgery_query.count(),
        'specialties': stats_specialty_query.count(),
        'reasons': stats_reason_query.count(),
        'clinics': Clinic.query.filter_by(is_active=True).count(),
    }
    return render_template('admin/index.html', stats=stats)

# Clinic Management
@admin_bp.route('/clinics')
@login_required
@superuser_required
def clinics():
    clinics = Clinic.query.all()
    return render_template('admin/clinics.html', clinics=clinics)



@admin_bp.route('/users')
@login_required
@admin_required
def users():
    import os
    users_query = User.query
    if not current_user.is_superuser:
        users_query = users_query.filter_by(clinic_id=current_user.clinic_id)
    users = users_query.all()
    clinics = Clinic.query.filter_by(is_active=True).all()
    enable_demo_login = os.environ.get('ENABLE_DEMO_LOGIN', 'false').lower() == 'true'
    return render_template('admin/users.html', users=users, clinics=clinics, enable_demo_login=enable_demo_login)

@admin_bp.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    import os
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'clinical')

        enable_demo_login = os.environ.get('ENABLE_DEMO_LOGIN', 'false').lower() == 'true'

        # Determine clinic_id based on role and user permissions
        if role == ROLE_SUPERUSER:
            # Superusers must have clinic_id=None
            clinic_id = None
            # Only superusers can create other superusers
            if not current_user.is_superuser:
                flash('Solo los superusuarios pueden crear otros superusuarios.', 'error')
                return redirect(url_for('admin.users'))
        elif role == ROLE_ADMIN:
            # Only superusers can create admins
            if not current_user.is_superuser:
                flash('Solo los superusuarios pueden crear administradores.', 'error')
                return redirect(url_for('admin.users'))
            # Admins require a clinic_id
            clinic_id = request.form.get('clinic_id', type=int)
            if not clinic_id:
                flash('Debe seleccionar una clínica para este rol.', 'error')
                return redirect(url_for('admin.users'))
        else:
            # Non-superuser roles require a clinic_id
            if current_user.is_superuser:
                clinic_id = request.form.get('clinic_id', type=int)
            else:
                clinic_id = current_user.clinic_id

            if not clinic_id:
                flash('Debe seleccionar una clínica para este rol.', 'error')
                return redirect(url_for('admin.users'))

        # Validate required fields (password only required if demo login enabled)
        if enable_demo_login:
            if not all([username, email, password]):
                flash('Usuario, email y contraseña son obligatorios.', 'error')
                return redirect(url_for('admin.users'))
        else:
            if not all([username, email]):
                flash('Usuario y email son obligatorios.', 'error')
                return redirect(url_for('admin.users'))

        # Check for existing username
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('admin.users'))

        # Check for existing email
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado.', 'error')
            return redirect(url_for('admin.users'))

        # Create user
        user = User(username=username, email=email, role=role, clinic_id=clinic_id)
        if enable_demo_login and password:
            user.set_password(password)
        else:
            # SSO-only mode: set a random password that won't be used
            import secrets
            user.set_password(secrets.token_urlsafe(32))
        db.session.add(user)

        # Add to Superuser table if role is superuser
        if role == ROLE_SUPERUSER:
            # Check if email already exists in Superuser table
            if not Superuser.query.filter_by(email=email).first():
                superuser_entry = Superuser(email=email)
                db.session.add(superuser_entry)

        db.session.commit()

        flash(f'Usuario {username} creado exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear usuario: {str(e)}', 'error')

    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user_query = User.query.filter_by(id=user_id)
    if not current_user.is_superuser:
        user_query = user_query.filter_by(clinic_id=current_user.clinic_id)
    user = user_query.first_or_404()
    
    if user.username == ROLE_ADMIN:
        flash('No se puede desactivar el usuario administrador principal.', 'error')
        return redirect(url_for('admin.users'))
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "activado" if user.is_active else "desactivado"
        flash(f'Usuario {user.username} {status} exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado del usuario: {str(e)}', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Edit an existing user. Only accessible to admins and superusers."""
    try:
        # Get the user to edit with clinic filtering for non-superusers
        user_query = User.query.filter_by(id=user_id)
        if not current_user.is_superuser:
            user_query = user_query.filter_by(clinic_id=current_user.clinic_id)
        user = user_query.first_or_404()

        # Prevent editing the main admin user
        if user.username == ROLE_ADMIN:
            flash('No se puede editar el usuario administrador principal.', 'error')
            return redirect(url_for('admin.users'))

        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', 'clinical')
        password = request.form.get('password', '').strip()

        # Store old email to detect email changes
        old_email = user.email
        was_superuser = user.is_superuser

        # Determine clinic_id based on role and user permissions
        if role == ROLE_SUPERUSER:
            # Superusers must have clinic_id=None
            clinic_id = None
            # Only superusers can edit to superuser role
            if not current_user.is_superuser:
                flash('Solo los superusuarios pueden asignar el rol de superusuario.', 'error')
                return redirect(url_for('admin.users'))
        elif role == ROLE_ADMIN:
            # Only superusers can assign admin role
            if not current_user.is_superuser:
                flash('Solo los superusuarios pueden asignar el rol de administrador.', 'error')
                return redirect(url_for('admin.users'))
            # Admins require a clinic_id
            clinic_id = request.form.get('clinic_id', type=int)
            if not clinic_id:
                flash('Debe seleccionar una clínica para este rol.', 'error')
                return redirect(url_for('admin.users'))
        else:
            # Non-superuser roles require a clinic_id
            if current_user.is_superuser:
                clinic_id = request.form.get('clinic_id', type=int)
            else:
                clinic_id = current_user.clinic_id

            if not clinic_id:
                flash('Debe seleccionar una clínica para este rol.', 'error')
                return redirect(url_for('admin.users'))

        # Validate required fields
        if not all([username, email]):
            flash('Usuario y email son obligatorios.', 'error')
            return redirect(url_for('admin.users'))

        # Check if username is taken by another user
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            flash('El nombre de usuario ya existe.', 'error')
            return redirect(url_for('admin.users'))

        # Check if email is taken by another user
        existing_email = User.query.filter_by(email=email).first()
        if existing_email and existing_email.id != user_id:
            flash('El email ya está registrado.', 'error')
            return redirect(url_for('admin.users'))

        # Update user fields
        user.username = username
        user.email = email
        user.role = role
        user.clinic_id = clinic_id

        # Update password only if provided
        if password:
            user.set_password(password)

        # Manage Superuser table entries
        if role == ROLE_SUPERUSER:
            # If becoming a superuser or email changed, ensure Superuser entry exists
            superuser_entry = Superuser.query.filter_by(email=email).first()
            if not superuser_entry:
                # Create new Superuser entry
                superuser_entry = Superuser(email=email)
                db.session.add(superuser_entry)

            # If email changed and was previously a superuser, remove old email from Superuser table
            if was_superuser and old_email != email:
                old_superuser = Superuser.query.filter_by(email=old_email).first()
                if old_superuser:
                    db.session.delete(old_superuser)
        else:
            # If was superuser but no longer is, remove from Superuser table
            if was_superuser:
                superuser_entry = Superuser.query.filter_by(email=old_email).first()
                if superuser_entry:
                    db.session.delete(superuser_entry)

        db.session.commit()
        flash(f'Usuario {username} actualizado exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar usuario: {str(e)}', 'error')

    return redirect(url_for('admin.users'))

@admin_bp.route('/master-data')
@login_required
@superuser_required
def master_data():
    # Get clinic filter from query string (for superusers)
    selected_clinic_id = None

    if current_user.is_superuser:
        # Superuser can filter by clinic or see message to select one
        selected_clinic_id = request.args.get('clinic_id', type=int)

        if selected_clinic_id:
            # Filter by selected clinic
            clinic_id = selected_clinic_id
            specialties = Specialty.query.filter_by(clinic_id=clinic_id).all()
            surgeries = Surgery.query.filter_by(clinic_id=clinic_id).all()
            reasons = StandardizedReason.query.filter_by(clinic_id=clinic_id).all()
            doctors = Doctor.query.filter_by(clinic_id=clinic_id).all()
        else:
            # No clinic selected - show empty lists
            specialties = []
            surgeries = []
            reasons = []
            doctors = []
    else:
        # Regular admin - always use their clinic
        clinic_id = current_user.clinic_id
        selected_clinic_id = clinic_id
        specialties = Specialty.query.filter_by(clinic_id=clinic_id).all()
        surgeries = Surgery.query.filter_by(clinic_id=clinic_id).all()
        reasons = StandardizedReason.query.filter_by(clinic_id=clinic_id).all()
        doctors = Doctor.query.filter_by(clinic_id=clinic_id).all()

    adjustments = [] # StayAdjustmentCriterion is not used
    clinics = Clinic.query.filter_by(is_active=True).all()

    return render_template('admin/master_data.html',
                         specialties=specialties,
                         surgeries=surgeries,
                         adjustments=adjustments,
                         reasons=reasons,
                         doctors=doctors,
                         clinics=clinics,
                         selected_clinic_id=selected_clinic_id)

# Master Data Management
@admin_bp.route('/master-data/specialty', methods=['POST'])
@login_required
@superuser_required
def create_specialty():
    try:
        name = request.form.get('name', '').strip()
        if not name:
            flash('El nombre es obligatorio.', 'error')
        else:
            clinic_id = request.form.get('clinic_id', current_user.clinic_id) if current_user.is_superuser else current_user.clinic_id
            specialty = Specialty(name=name, clinic_id=clinic_id)
            db.session.add(specialty)
            db.session.commit()
            flash('Especialidad creada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear especialidad: {str(e)}', 'error')

    # Redirect back with clinic filter if present
    clinic_filter = request.form.get('clinic_id') if current_user.is_superuser else current_user.clinic_id
    return redirect(url_for('admin.master_data', clinic_id=clinic_filter))

@admin_bp.route('/master-data/specialty/<int:specialty_id>/toggle', methods=['POST'])
@login_required
@superuser_required
def toggle_specialty(specialty_id):
    specialty = Specialty.query.get_or_404(specialty_id)
    if not current_user.is_superuser and specialty.clinic_id != current_user.clinic_id:
        flash('No tiene permisos para modificar esta especialidad.', 'error')
        return redirect(url_for('admin.master_data'))

    clinic_filter = specialty.clinic_id if current_user.is_superuser else current_user.clinic_id

    try:
        specialty.is_active = not specialty.is_active
        db.session.commit()
        status = "activada" if specialty.is_active else "desactivada"
        flash(f'Especialidad {specialty.name} {status} exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado de la especialidad: {str(e)}', 'error')

    return redirect(url_for('admin.master_data', clinic_id=clinic_filter))

@admin_bp.route('/master-data/surgery', methods=['POST'])
@login_required
@superuser_required
def create_surgery():
    try:
        name = request.form.get('name', '').strip()
        specialty_id = request.form.get('specialty_id', type=int)
        base_stay_hours = request.form.get('base_stay_hours', type=int)
        if not all([name, specialty_id, base_stay_hours]):
            flash('Nombre, especialidad y horas base son obligatorios.', 'error')
        else:
            clinic_id = request.form.get('clinic_id', current_user.clinic_id) if current_user.is_superuser else current_user.clinic_id
            surgery = Surgery(name=name, specialty_id=specialty_id, base_stay_hours=base_stay_hours, clinic_id=clinic_id)
            db.session.add(surgery)
            db.session.commit()
            flash('Cirugía creada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear cirugía: {str(e)}', 'error')

    # Redirect back with clinic filter if present
    clinic_filter = request.form.get('clinic_id') if current_user.is_superuser else current_user.clinic_id
    return redirect(url_for('admin.master_data', clinic_id=clinic_filter))

@admin_bp.route('/master-data/surgery/<int:surgery_id>/toggle', methods=['POST'])
@login_required
@superuser_required
def toggle_surgery(surgery_id):
    surgery = Surgery.query.get_or_404(surgery_id)
    if not current_user.is_superuser and surgery.clinic_id != current_user.clinic_id:
        flash('No tiene permisos para modificar esta cirugía.', 'error')
        return redirect(url_for('admin.master_data'))

    clinic_filter = surgery.clinic_id if current_user.is_superuser else current_user.clinic_id

    try:
        surgery.is_active = not surgery.is_active
        db.session.commit()
        status = "activada" if surgery.is_active else "desactivada"
        flash(f'Cirugía {surgery.name} {status} exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado de la cirugía: {str(e)}', 'error')

    return redirect(url_for('admin.master_data', clinic_id=clinic_filter))

@admin_bp.route('/master-data/adjustment', methods=['POST'])
@login_required
@superuser_required
def create_adjustment():
    try:
        name = request.form.get('name', '').strip()
        hours_adjustment = request.form.get('hours_adjustment', type=int)
        category = request.form.get('category', '').strip()
        if not name or not hours_adjustment or not category:
            flash('Todos los campos son obligatorios.', 'error')
        else:
            clinic_id = request.form.get('clinic_id', current_user.clinic_id) if current_user.is_superuser else current_user.clinic_id
            adjustment = StayAdjustmentCriterion(name=name, hours_adjustment=hours_adjustment, category=category, clinic_id=clinic_id)
            db.session.add(adjustment)
            db.session.commit()
            flash('Criterio de ajuste creado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear criterio de ajuste: {str(e)}', 'error')
    return redirect(url_for('admin.master_data'))

@admin_bp.route('/master-data/adjustment/<int:adjustment_id>/toggle', methods=['POST'])
@login_required
@superuser_required
def toggle_adjustment(adjustment_id):
    adjustment = StayAdjustmentCriterion.query.get_or_404(adjustment_id)
    if not current_user.is_superuser and adjustment.clinic_id != current_user.clinic_id:
        flash('No tiene permisos para modificar este criterio.', 'error')
        return redirect(url_for('admin.master_data'))
    try:
        adjustment.is_active = not adjustment.is_active
        db.session.commit()
        status = "activado" if adjustment.is_active else "desactivado"
        flash(f'Criterio de ajuste {adjustment.name} {status} exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado del criterio: {str(e)}', 'error')
    return redirect(url_for('admin.master_data'))

@admin_bp.route('/master-data/reason', methods=['POST'])
@login_required
@superuser_required
def create_reason():
    try:
        reason = request.form.get('reason', '').strip()
        category = request.form.get('category', '').strip()
        if not reason or not category:
            flash('Razón y categoría son obligatorios.', 'error')
        else:
            clinic_id = request.form.get('clinic_id', current_user.clinic_id) if current_user.is_superuser else current_user.clinic_id
            standardized_reason = StandardizedReason(reason=reason, category=category, clinic_id=clinic_id)
            db.session.add(standardized_reason)
            db.session.commit()
            flash('Razón estandarizada creada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear razón estandarizada: {str(e)}', 'error')

    # Redirect back with clinic filter if present
    clinic_filter = request.form.get('clinic_id') if current_user.is_superuser else current_user.clinic_id
    return redirect(url_for('admin.master_data', clinic_id=clinic_filter))

@admin_bp.route('/master-data/reason/<int:reason_id>/toggle', methods=['POST'])
@login_required
@superuser_required
def toggle_reason(reason_id):
    reason = StandardizedReason.query.get_or_404(reason_id)
    if not current_user.is_superuser and reason.clinic_id != current_user.clinic_id:
        flash('No tiene permisos para modificar esta razón.', 'error')
        return redirect(url_for('admin.master_data'))

    clinic_filter = reason.clinic_id if current_user.is_superuser else current_user.clinic_id

    try:
        reason.is_active = not reason.is_active
        db.session.commit()
        status = "activada" if reason.is_active else "desactivada"
        flash(f'Razón estandarizada {status} exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado de la razón: {str(e)}', 'error')

    return redirect(url_for('admin.master_data', clinic_id=clinic_filter))

@admin_bp.route('/master-data/doctor', methods=['POST'])
@login_required
@superuser_required
def create_doctor():
    try:
        name = request.form.get('name', '').strip()
        specialty = request.form.get('specialty', '').strip()
        rut = request.form.get('rut', '').strip()
        if not name:
            flash('El nombre del médico es obligatorio.', 'error')
        else:
            clinic_id = request.form.get('clinic_id', current_user.clinic_id) if current_user.is_superuser else current_user.clinic_id
            doctor = Doctor(name=name, specialty=specialty, rut=rut, clinic_id=clinic_id)
            db.session.add(doctor)
            db.session.commit()
            flash('Médico creado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear médico: {str(e)}', 'error')

    # Redirect back with clinic filter if present
    clinic_filter = request.form.get('clinic_id') if current_user.is_superuser else current_user.clinic_id
    return redirect(url_for('admin.master_data', clinic_id=clinic_filter))

@admin_bp.route('/master-data/doctor/<int:doctor_id>/toggle', methods=['POST'])
@login_required
@superuser_required
def toggle_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    if not current_user.is_superuser and doctor.clinic_id != current_user.clinic_id:
        flash('No tiene permisos para modificar este médico.', 'error')
        return redirect(url_for('admin.master_data'))

    clinic_filter = doctor.clinic_id if current_user.is_superuser else current_user.clinic_id

    try:
        doctor.is_active = not doctor.is_active
        db.session.commit()
        status = "activado" if doctor.is_active else "desactivado"
        flash(f'Médico {doctor.name} {status} exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado del médico: {str(e)}', 'error')

    return redirect(url_for('admin.master_data', clinic_id=clinic_filter))


@admin_bp.route('/audit/logins')
@login_required
@admin_required
def login_audit():
    page = request.args.get('page', 1, type=int)
    logs_query = LoginAudit.query
    if not current_user.is_superuser:
        logs_query = logs_query.filter_by(clinic_id=current_user.clinic_id)
    logs = logs_query.order_by(LoginAudit.timestamp.desc()).paginate(page=page, per_page=20)

    # Get clinic information for logs (for superusers)
    clinics_dict = {}
    if current_user.is_superuser:
        all_clinics = Clinic.query.all()
        clinics_dict = {clinic.id: clinic.name for clinic in all_clinics}

    return render_template('admin/audit_log.html', logs=logs, clinics_dict=clinics_dict)


@admin_bp.route('/exportar')
@login_required
@superuser_required
def export_page():
    """Displays the export confirmation page."""
    return render_template('admin/export_confirmation.html')


@admin_bp.route('/exportar/descargar')
@login_required
@superuser_required
def export_full_database_action():
    """Exports all data from the database to an Excel file, with each table in a separate sheet."""
    try:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # Define the models to export in the desired order
        models_to_export = [
            Clinic, User, Specialty, Surgery, Doctor, Patient, 
            Ticket, FpaModification, LoginAudit, ActionAudit
        ]

        for model in models_to_export:
            table_name = model.__tablename__
            ws = wb.create_sheet(title=table_name)
            
            # Get headers from the model's columns
            headers = [column.key for column in model.__table__.columns]
            ws.append(headers)

            # Query all records for the model
            records = model.query.all()

            for record in records:
                row = []
                for header in headers:
                    val = getattr(record, header)
                    # Make datetime objects timezone-naive for Excel
                    if isinstance(val, datetime):
                        val = val.replace(tzinfo=None)
                    row.append(val)
                ws.append(row)

        # Save the workbook to a BytesIO stream
        mem_file = BytesIO()
        wb.save(mem_file)
        mem_file.seek(0)

        return send_file(
            mem_file,
            as_attachment=True,
            download_name=f'full_database_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        flash(f'Ocurrió un error al generar el archivo Excel: {str(e)}', 'error')
        return redirect(url_for('admin.index'))


@admin_bp.route('/configuracion/umbrales-colores', methods=['GET'])
@login_required
@admin_required
def color_thresholds():
    """Configuración de umbrales de colores para tarjetas de tickets."""
    if current_user.is_superuser:
        # Superusers can see global and all clinic-specific configurations
        global_threshold = UrgencyThreshold.query.filter_by(clinic_id=None).first()
        clinic_thresholds = UrgencyThreshold.query.filter(UrgencyThreshold.clinic_id.isnot(None)).all()
        clinics = Clinic.query.filter_by(is_active=True).all()
    else:
        # Admins can only see their clinic's configuration
        global_threshold = UrgencyThreshold.query.filter_by(clinic_id=None).first()
        clinic_thresholds = UrgencyThreshold.query.filter_by(clinic_id=current_user.clinic_id).all()
        clinics = [current_user.clinic] if current_user.clinic else []

    # Create default if doesn't exist
    if not global_threshold:
        global_threshold = UrgencyThreshold(
            clinic_id=None,
            green_threshold_hours=8,
            yellow_threshold_hours=4,
            red_threshold_hours=2
        )

    return render_template('admin/color_thresholds.html',
                         global_threshold=global_threshold,
                         clinic_thresholds=clinic_thresholds,
                         clinics=clinics)


@admin_bp.route('/configuracion/umbrales-colores/guardar', methods=['POST'])
@login_required
@admin_required
def save_color_thresholds():
    """Guarda la configuración de umbrales de colores."""
    try:
        clinic_id = request.form.get('clinic_id')

        # Validate permissions
        if clinic_id and clinic_id != 'global':
            clinic_id = int(clinic_id)
            if not current_user.is_superuser and clinic_id != current_user.clinic_id:
                flash('No tiene permisos para modificar esta configuración.', 'error')
                return redirect(url_for('admin.color_thresholds'))
        elif clinic_id == 'global':
            clinic_id = None

        # Validate that only superusers can modify global config
        if clinic_id is None and not current_user.is_superuser:
            flash('Solo los superusuarios pueden modificar la configuración global.', 'error')
            return redirect(url_for('admin.color_thresholds'))

        # Get or create threshold
        if clinic_id is None:
            threshold = UrgencyThreshold.query.filter_by(clinic_id=None).first()
        else:
            threshold = UrgencyThreshold.query.filter_by(clinic_id=clinic_id).first()

        if not threshold:
            threshold = UrgencyThreshold(clinic_id=clinic_id)
            db.session.add(threshold)

        # Update values
        green_hours = int(request.form.get('green_threshold_hours', 8))
        yellow_hours = int(request.form.get('yellow_threshold_hours', 4))
        red_hours = int(request.form.get('red_threshold_hours', 2))

        # Validate threshold order
        if not (red_hours < yellow_hours < green_hours):
            flash('Los umbrales deben estar en orden: Rojo < Amarillo < Verde', 'error')
            return redirect(url_for('admin.color_thresholds'))

        threshold.green_threshold_hours = green_hours
        threshold.yellow_threshold_hours = yellow_hours
        threshold.red_threshold_hours = red_hours
        threshold.updated_at = datetime.utcnow()
        threshold.updated_by = current_user.username

        db.session.commit()

        # Log the action
        config_type = "global" if clinic_id is None else f"clínica {clinic_id}"
        AuditService.log_action(
            user=current_user,
            action=f"Configuró umbrales de colores ({config_type}): Verde>{green_hours}h, Amarillo>{yellow_hours}h, Rojo<{red_hours}h",
            target_id=str(threshold.id),
            target_type='UrgencyThreshold'
        )

        flash('Configuración de umbrales guardada exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar configuración: {str(e)}', 'error')

    return redirect(url_for('admin.color_thresholds'))


@admin_bp.route('/api/umbrales-colores')
@login_required
def get_color_thresholds_api():
    """API endpoint to get color thresholds for current user's clinic."""
    clinic_id = current_user.clinic_id if not current_user.is_superuser else request.args.get('clinic_id', type=int)
    threshold = UrgencyThreshold.get_thresholds_for_clinic(clinic_id)

    return jsonify({
        'green_threshold_hours': threshold.green_threshold_hours,
        'yellow_threshold_hours': threshold.yellow_threshold_hours,
        'red_threshold_hours': threshold.red_threshold_hours
    })
