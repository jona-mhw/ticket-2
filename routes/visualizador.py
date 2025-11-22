from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, Ticket, Patient, Surgery, Clinic
from datetime import datetime
from sqlalchemy import or_
from .utils import _build_tickets_query, apply_sorting_to_query
from services import UrgencyCalculator

visualizador_bp = Blueprint('visualizador', __name__, url_prefix='/visualizador')

@visualizador_bp.route('/dashboard')
@login_required
def dashboard():
    if not (current_user.role in ['admin', 'visualizador'] or current_user.is_superuser):
        return "Acceso no autorizado", 403

    filters = {
        'status': request.args.get('status', ''),
        'search': request.args.get('search', ''),
        'surgery': request.args.get('surgery', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', ''),
        'compliance': request.args.get('compliance', ''),
        'clinic_id': request.args.get('clinic_id', ''),
        'room': request.args.get('room', ''),
        'urgency': request.args.get('urgency', '')
    }

    # Columnas visibles (por defecto o desde query params)
    visible_columns = request.args.getlist('cols') or ['patient', 'rut', 'room', 'fpa', 'time_slot', 'status', 'countdown']

    query = _build_tickets_query(filters)

    # Filtrar solo vigentes y ordenar por FPA
    query = query.filter(Ticket.status == 'Vigente').order_by(Ticket.current_fpa.asc())

    tickets = query.all()

    # Calcular tiempo restante y clasificar por urgencia
    for ticket in tickets:
        UrgencyCalculator.calculate_urgency(ticket)

    # Ordenar: vigentes (normal) primero, luego por FPA
    urgency_priority = {'normal': 0, 'warning': 1, 'critical': 2, 'scheduled': 3, 'expired': 4, 'unknown': 5}
    tickets.sort(key=lambda t: (urgency_priority.get(t.urgency_level, 99), t.current_fpa if t.current_fpa else datetime.max))

    # Filtrar por urgencia si se especifica
    if filters['urgency']:
        tickets = [t for t in tickets if t.urgency_level == filters['urgency']]

    # Estadísticas
    stats = {
        'total': len(tickets),
        'critical': len([t for t in tickets if t.urgency_level == 'critical']),
        'warning': len([t for t in tickets if t.urgency_level == 'warning']),
        'normal': len([t for t in tickets if t.urgency_level == 'normal']),
        'expired': len([t for t in tickets if t.urgency_level == 'expired']),
        'scheduled': len([t for t in tickets if t.urgency_level == 'scheduled'])
    }

    surgeries_query = Surgery.query.filter_by(is_active=True)
    if not current_user.is_superuser:
        surgeries_query = surgeries_query.filter_by(clinic_id=current_user.clinic_id)
    surgeries = surgeries_query.all()

    clinics = Clinic.query.filter_by(is_active=True).all()

    return render_template(
        'visualizador/dashboard.html',
        tickets=tickets,
        surgeries=surgeries,
        clinics=clinics,
        filters=filters,
        stats=stats,
        visible_columns=visible_columns
    )