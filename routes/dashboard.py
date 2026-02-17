from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Ticket, Surgery, FpaModification, Clinic, Doctor, db, TICKET_STATUS_VIGENTE, TICKET_STATUS_ANULADO
from sqlalchemy import func
from datetime import datetime, timedelta
from utils.datetime_utils import utcnow
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Only admins and superusers can access the dashboard
    if not (current_user.is_admin() or current_user.is_superuser):
        flash('Acceso denegado. Solo administradores y superusuarios pueden acceder al dashboard.', 'error')
        return redirect(url_for('tickets.nursing_board'))
    now = utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    # Issue #89: Handle date range and surgery filters
    # Issue #88: Handle clinic filter for superusers
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    surgery_id = request.args.get('surgery_id')
    clinic_id = request.args.get('clinic_id') if current_user.is_superuser else None

    # Validate surgery belongs to the selected clinic to avoid incorrect filtering (Issue: Reset selection)
    if surgery_id:
        try:
            active_clinic_id = int(clinic_id) if clinic_id else (current_user.clinic_id if not current_user.is_superuser else None)
            
            if active_clinic_id:
                surg = Surgery.query.get(surgery_id)
                if surg and surg.clinic_id != active_clinic_id:
                    surgery_id = None # Reset filter if surgery doesn't belong to clinic
        except (ValueError, TypeError):
            pass

    # Build base queries with clinic filtering for non-superusers
    def apply_clinic_filter(query):
        """Apply clinic filter only for non-superusers, or selected clinic for superusers"""
        if not current_user.is_superuser:
            return query.filter(Ticket.clinic_id == current_user.clinic_id)
        elif clinic_id:
            # Superuser selected a specific clinic
            try:
                return query.filter(Ticket.clinic_id == int(clinic_id))
            except (ValueError, TypeError):
                pass
        return query

    def apply_date_range_filter(query):
        """Apply date range filters if provided"""
        if date_from:
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(Ticket.created_at >= start_date)
            except ValueError:
                pass
        if date_to:
            try:
                end_date = datetime.strptime(date_to, '%Y-%m-%d')
                # Include the entire end date
                end_date = end_date.replace(hour=23, minute=59, second=59)
                query = query.filter(Ticket.created_at <= end_date)
            except ValueError:
                pass
        return query

    def apply_surgery_filter(query):
        """Apply surgery filter if provided"""
        if surgery_id:
            try:
                query = query.filter(Ticket.surgery_id == int(surgery_id))
            except (ValueError, TypeError):
                pass
        return query

    # KPIs - Issue #86: Redefined KPI criteria, Issue #89: Apply filters
    # Base query with clinic and filter filters applied
    def base_query():
        q = Ticket.query
        q = apply_clinic_filter(q)
        q = apply_date_range_filter(q)
        q = apply_surgery_filter(q)
        return q

    # 1. Vigentes: Tickets with time remaining (discharge_date > now), ordered DESC
    active_tickets_count = base_query().filter(
        Ticket.status == TICKET_STATUS_VIGENTE,
        Ticket.current_fpa > now
    ).count()

    # 2. Creados Hoy: Tickets created today (00:01 - 23:59)
    today_start = now.replace(hour=0, minute=1, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    created_today_count = base_query().filter(
        Ticket.created_at >= today_start,
        Ticket.created_at <= today_end
    ).count()

    # 3. Vencidos: Tickets that reached their discharge date (discharge_date <= now), ordered DESC
    overdue_tickets_count = base_query().filter(
        Ticket.status == TICKET_STATUS_VIGENTE,
        Ticket.current_fpa <= now
    ).count()

    # 4. Anulados: Tickets with annulled status
    annulled_tickets_count = base_query().filter_by(status=TICKET_STATUS_ANULADO).count()

    # Total tickets for other calculations
    total_tickets_query = base_query()

    kpis = {
        'vigentes': active_tickets_count,
        'creados_hoy': created_today_count,
        'vencidos': overdue_tickets_count,
        'anulados': annulled_tickets_count,
        # Legacy names for backward compatibility
        'active_tickets': active_tickets_count,
        'annulled_tickets': annulled_tickets_count,
        'overdue_tickets': overdue_tickets_count,
        'total_tickets': total_tickets_query.count(),
        'monthly_tickets': apply_clinic_filter(Ticket.query.filter(Ticket.created_at >= start_of_month)).count(),
        'weekly_tickets': apply_clinic_filter(Ticket.query.filter(Ticket.created_at >= start_of_week)).count()
    }

    next_24h = now + timedelta(hours=24)
    near_deadline = apply_clinic_filter(Ticket.query.filter(
        Ticket.status == 'Vigente',
        Ticket.current_fpa <= next_24h,
        Ticket.current_fpa > now
    )).count()

    kpis['near_deadline'] = near_deadline

    recent_tickets_query = base_query()
    recent_tickets = recent_tickets_query.order_by(Ticket.created_at.desc()).limit(8).all()

    # Get all surgeries for the filter dropdown
    surgeries_query = Surgery.query
    if not current_user.is_superuser:
        surgeries_query = surgeries_query.filter_by(clinic_id=current_user.clinic_id)
    elif clinic_id:
        # If superuser selected a clinic, filter surgeries by that clinic
        try:
            surgeries_query = surgeries_query.filter_by(clinic_id=int(clinic_id))
        except (ValueError, TypeError):
            pass
            
    surgeries = surgeries_query.filter_by(is_active=True).order_by(Surgery.name).all()

    # Get all clinics for the filter dropdown (for superusers only)
    clinics = []
    if current_user.is_superuser:
        clinics = Clinic.query.filter_by(is_active=True).order_by(Clinic.name).all()

    # Surgery stats
    surgery_stats_query = db.session.query(
        Surgery.name,
        func.count(Ticket.id).label('ticket_count')
    ).join(Ticket)
    if not current_user.is_superuser:
        surgery_stats_query = surgery_stats_query.filter(Ticket.clinic_id == current_user.clinic_id)
    # Apply filters to surgery stats
    if date_from:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
            surgery_stats_query = surgery_stats_query.filter(Ticket.created_at >= start_date)
        except ValueError:
            pass
    if date_to:
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            surgery_stats_query = surgery_stats_query.filter(Ticket.created_at <= end_date)
        except ValueError:
            pass
    if surgery_id:
        try:
            surgery_stats_query = surgery_stats_query.filter(Ticket.surgery_id == int(surgery_id))
        except (ValueError, TypeError):
            pass
    surgery_stats = surgery_stats_query.group_by(Surgery.id, Surgery.name).order_by(func.count(Ticket.id).desc()).limit(5).all()

    # Doctors with most FPA modifications (respects all active filters)
    doctor_mods_query = db.session.query(
        Doctor.name, func.count(FpaModification.id).label('mod_count')
    ).join(Ticket, FpaModification.ticket_id == Ticket.id
    ).join(Doctor, Ticket.doctor_id == Doctor.id)
    if not current_user.is_superuser:
        doctor_mods_query = doctor_mods_query.filter(Ticket.clinic_id == current_user.clinic_id)
    elif clinic_id:
        try:
            doctor_mods_query = doctor_mods_query.filter(Ticket.clinic_id == int(clinic_id))
        except (ValueError, TypeError):
            pass
    if date_from:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
            doctor_mods_query = doctor_mods_query.filter(Ticket.created_at >= start_date)
        except ValueError:
            pass
    if date_to:
        try:
            end_date = datetime.strptime(date_to, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
            doctor_mods_query = doctor_mods_query.filter(Ticket.created_at <= end_date)
        except ValueError:
            pass
    if surgery_id:
        try:
            doctor_mods_query = doctor_mods_query.filter(Ticket.surgery_id == int(surgery_id))
        except (ValueError, TypeError):
            pass
    doctor_modifications = doctor_mods_query.group_by(
        Doctor.id, Doctor.name
    ).order_by(func.count(FpaModification.id).desc()).limit(10).all()

    # Modification stats
    total_mods_query = FpaModification.query
    if not current_user.is_superuser:
        total_mods_query = total_mods_query.filter_by(clinic_id=current_user.clinic_id)
    total_modifications = total_mods_query.count()

    avg_modifications = round(total_modifications / kpis['total_tickets'] if kpis['total_tickets'] > 0 else 0, 1)

    tickets_with_mods_query = db.session.query(Ticket.id).join(FpaModification)
    if not current_user.is_superuser:
        tickets_with_mods_query = tickets_with_mods_query.filter(Ticket.clinic_id == current_user.clinic_id)
    tickets_with_mods = tickets_with_mods_query.distinct().count()

    modification_stats = {
        'total_modifications': total_modifications,
        'avg_modifications_per_ticket': avg_modifications,
        'tickets_with_modifications': tickets_with_mods
    }

    chart_data = {
        'surgery_distribution': [{'surgery': s.name, 'count': s.ticket_count} for s in surgery_stats]
    }

    return render_template('dashboard.html',
                         kpis=kpis,
                         recent_tickets=recent_tickets,
                         surgery_stats=surgery_stats,
                         modification_stats=modification_stats,
                         doctor_modifications=doctor_modifications,
                         chart_data=json.dumps(chart_data),
                         surgeries=surgeries,
                         clinics=clinics)