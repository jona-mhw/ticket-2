from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import json

# --- Constants ---
# User Roles
ROLE_ADMIN = 'admin'
ROLE_CLINICAL = 'clinical'
ROLE_VISUALIZADOR = 'visualizador'
ROLE_SUPERUSER = 'superuser'

# Ticket Statuses
TICKET_STATUS_VIGENTE = 'Vigente'
TICKET_STATUS_ANULADO = 'Anulado'

# Standardized Reason Categories
REASON_CATEGORY_INITIAL = 'initial'  # Discrepancia inicial al crear ticket
REASON_CATEGORY_MODIFICATION = 'modification'
REASON_CATEGORY_ANNULMENT = 'annulment'

# --- End Constants ---

db = SQLAlchemy()

# Define Superuser first to be available in User model property
class Superuser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Superuser {self.email}>'

class Clinic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    users = db.relationship('User', backref='clinic', lazy=True)
    specialties = db.relationship('Specialty', backref='clinic', lazy=True)
    surgeries = db.relationship('Surgery', backref='clinic', lazy=True)

    doctors = db.relationship('Doctor', backref='clinic', lazy=True)
    standardized_reasons = db.relationship('StandardizedReason', backref='clinic', lazy=True)
    patients = db.relationship('Patient', backref='clinic', lazy=True)
    tickets = db.relationship('Ticket', backref='clinic', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='clinical')  # 'admin', 'clinical' or 'visualizador'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        # Fallback for legacy plain text passwords
        if not self.password.startswith('scrypt:') and not self.password.startswith('pbkdf2:'):
            if self.password == password:
                # Upgrade password to hash
                self.set_password(password)
                db.session.commit()
                return True
            return False
        return check_password_hash(self.password, password)
    
    def is_admin(self):
        # Admin role or superuser status
        if not self.role:
            return self.is_superuser
        
        role_lower = self.role.lower()
        return role_lower in ['admin', 'superuser', 'superusuario'] or self.is_superuser

    @property
    def is_superuser(self):
        if not hasattr(self, '_is_superuser'):
            # Check by role string first (case-insensitive)
            if self.role and self.role.lower() in ['superuser', 'superusuario']:
                self._is_superuser = True
            # Fallback to clinic_id + Superuser table check
            elif self.clinic_id is not None:
                self._is_superuser = False
            else:
                try:
                    self._is_superuser = Superuser.query.filter_by(email=self.email).first() is not None
                except Exception:
                    # The query failed, likely because the table doesn't exist.
                    # This can happen during initial migrations.
                    db.session.rollback()
                    self._is_superuser = False
        return self._is_superuser

class Specialty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    surgeries = db.relationship('Surgery', backref='specialty', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'clinic_id': self.clinic_id
        }

class Surgery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    base_stay_hours = db.Column(db.Integer, nullable=False)
    specialty_id = db.Column(db.Integer, db.ForeignKey('specialty.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    applies_ticket_home = db.Column(db.Boolean, default=True)
    is_ambulatory = db.Column(db.Boolean, default=False)
    ambulatory_cutoff_hour = db.Column(db.Integer, nullable=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'base_stay_hours': self.base_stay_hours,
            'specialty_id': self.specialty_id
        }

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    specialty = db.Column(db.String(100), nullable=True)
    rut = db.Column(db.String(12), nullable=True)  # Formato: 12.345.678-9
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)

    tickets = db.relationship('Ticket', backref='attending_doctor', lazy=True)

# Issue #54: DischargeTimeSlot eliminado - se usa TimeBlockHelper en vez de BD
# Los bloques horarios son FIJOS (24 bloques de 2h) y se calculan dinámicamente

class StandardizedReason(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)

class Patient(db.Model):
    __table_args__ = (
        db.UniqueConstraint('rut', 'clinic_id', name='uq_patient_rut_clinic'),
    )

    id = db.Column(db.Integer, primary_key=True)
    rut = db.Column(db.String(12), nullable=False, index=True)
    primer_nombre = db.Column(db.String(100), nullable=False)
    segundo_nombre = db.Column(db.String(100), nullable=True)
    apellido_paterno = db.Column(db.String(100), nullable=False)
    apellido_materno = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)
    episode_id = db.Column(db.String(50), nullable=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    
    tickets = db.relationship('Ticket', backref='patient', lazy=True)

    @property
    def full_name(self):
        parts = [self.primer_nombre, self.segundo_nombre, self.apellido_paterno, self.apellido_materno]
        return ' '.join(part for part in parts if part)

    @property
    def primer_nombre_prop(self):
        return self.primer_nombre

    @property
    def segundo_nombre_prop(self):
        return self.segundo_nombre

    @property
    def apellido_paterno_prop(self):
        return self.apellido_paterno

    @property
    def apellido_materno_prop(self):
        return self.apellido_materno

class Ticket(db.Model):
    id = db.Column(db.String(20), primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    surgery_id = db.Column(db.Integer, db.ForeignKey('surgery.id'), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)
    # Issue #54: discharge_slot_id eliminado - bloques se calculan dinámicamente
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    
    pavilion_end_time = db.Column(db.DateTime, nullable=False)
    medical_discharge_date = db.Column(db.Date, nullable=False)
    system_calculated_fpa = db.Column(db.DateTime, nullable=True)
    initial_fpa = db.Column(db.DateTime, nullable=False)
    current_fpa = db.Column(db.DateTime, nullable=False)
    overnight_stays = db.Column(db.Integer, nullable=False)
    original_overnight_stays = db.Column(db.Integer, nullable=True)
    original_fpa_date = db.Column(db.Date, nullable=True)
    bed_number = db.Column(db.String(10), nullable=True)
    location = db.Column(db.String(50), nullable=True)
    
    status = db.Column(db.String(20), nullable=False, default='Vigente')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(80), nullable=False)
    
    annulled_at = db.Column(db.DateTime, nullable=True)
    annulled_reason = db.Column(db.String(500), nullable=True)
    annulled_by = db.Column(db.String(80), nullable=True)

    # --- Initial Discrepancy Fields ---
    initial_reason = db.Column(db.String(500), nullable=True)
    initial_justification = db.Column(db.Text, nullable=True)

    # --- Snapshot Fields ---
    surgery_name_snapshot = db.Column(db.String(200), nullable=True)
    surgery_base_hours_snapshot = db.Column(db.Integer, nullable=True)
    
    surgery = db.relationship('Surgery', backref='tickets')
    modifications = db.relationship('FpaModification', backref='ticket', lazy=True, cascade='all, delete-orphan')
    

    
    def calculate_fpa(self, pavilion_end_time, surgery):
        """
        DEPRECATED: Use FPACalculator.calculate() from services instead.

        This method is kept for backward compatibility with existing code.
        """
        from services.fpa_calculator import FPACalculator
        return FPACalculator.calculate(pavilion_end_time, surgery)
    
    def compute_state(self):
        """
        Centralized ticket state computation. Single source of truth for
        is_scheduled, time_remaining, urgency_level, and admission_time.

        Populates transient attributes on the ticket instance:
            - admission_time (datetime)
            - is_scheduled (bool)
            - time_remaining (dict or None)
            - urgency_level (str: 'scheduled', 'expired', 'critical', 'warning', 'normal', 'unknown')
        """
        from services.fpa_calculator import FPACalculator
        from utils.datetime_utils import calculate_time_remaining, utcnow

        if not self.current_fpa:
            self.admission_time = None
            self.is_scheduled = False
            self.time_remaining = None
            self.urgency_level = 'unknown'
            return self

        now = utcnow()
        admission_time = FPACalculator.calculate_admission_time(self.pavilion_end_time)
        self.admission_time = admission_time
        self.is_scheduled = now < admission_time
        self.time_remaining = None if self.is_scheduled else calculate_time_remaining(self.current_fpa)

        if self.is_scheduled:
            self.urgency_level = 'scheduled'
        elif self.time_remaining and self.time_remaining['expired']:
            self.urgency_level = 'expired'
        elif self.time_remaining:
            total_hours = self.time_remaining['days'] * 24 + self.time_remaining['hours']
            if total_hours <= 1:
                self.urgency_level = 'critical'
            elif total_hours <= 6:
                self.urgency_level = 'warning'
            else:
                self.urgency_level = 'normal'
        else:
            self.urgency_level = 'unknown'

        return self

    def can_be_modified(self):
        return self.status == 'Vigente'
    
    def get_modification_count(self):
        return len(self.modifications)
    
    @property
    def calculated_discharge_time_block(self):
        """
        Calcula dinámicamente el bloque de 2 horas basándose en current_fpa.
        IMPORTANTE: El FPA es el extremo DERECHO (fin) del bloque.

        CORRECCIÓN Issue #53: Redondeo a hora entera MÁS CERCANA
        - 0-29 minutos → Redondear ABAJO a la hora actual
        - 30-59 minutos → Redondear ARRIBA a la siguiente hora
        - Esa hora es el extremo DERECHO del rango de 2 horas

        Ejemplos:
        - 14:15 → Redondear a 14:00 → Bloque 12:00-14:00
        - 14:30 → Redondear a 15:00 → Bloque 13:00-15:00
        - 14:45 → Redondear a 15:00 → Bloque 13:00-15:00
        - 13:00 → Ya es entero → Bloque 11:00-13:00
        - 22:00 → Bloque 20:00-22:00
        - 23:40 → Redondear a 00:00 → Bloque 22:00-00:00

        Retorna el nombre del bloque (ej: "12:00 - 14:00").
        """
        if not self.current_fpa:
            return "Sin horario"

        # Obtener la hora y minutos del FPA
        fpa_hour = self.current_fpa.hour
        fpa_minute = self.current_fpa.minute

        # CORRECCIÓN: Redondear a la hora MÁS CERCANA
        if fpa_minute >= 30:
            fpa_hour += 1  # Redondear ARRIBA si >= 30 minutos
        # Si < 30 minutos, se queda en la hora actual (redondear ABAJO)

        # Manejar el caso de 24:00 (medianoche del día siguiente)
        if fpa_hour >= 24:
            fpa_hour = 0

        # El FPA redondeado es el extremo DERECHO del bloque
        block_end_hour = fpa_hour
        block_start_hour = (block_end_hour - 2) % 24

        # Formatear como "HH:MM - HH:MM"
        return f"{block_start_hour:02d}:00 - {block_end_hour:02d}:00"


class FpaModification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), db.ForeignKey('ticket.id'), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=False)
    
    previous_fpa = db.Column(db.DateTime, nullable=False)
    new_fpa = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    justification = db.Column(db.Text, nullable=True)
    
    modified_at = db.Column(db.DateTime, default=datetime.utcnow)
    modified_by = db.Column(db.String(80), nullable=False)



class LoginAudit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True)  # Nullable for superusers
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)

    user = db.relationship('User', backref='login_audits')


class ActionAudit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True)  # Nullable for superusers
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.Text, nullable=False)
    target_id = db.Column(db.String(80), nullable=True)
    target_type = db.Column(db.String(80), nullable=True)

    user = db.relationship('User', backref='action_audits')


class UrgencyThreshold(db.Model):
    """
    Configuración de umbrales de urgencia para los colores de las tarjetas de tickets.
    Los superusuarios y administradores pueden configurar estos valores.
    """
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinic.id'), nullable=True)  # Nullable for global config

    # Umbrales en horas
    # Verde (normal): > green_threshold_hours
    # Amarillo (warning): entre yellow_threshold_hours y green_threshold_hours
    # Rojo (critical): < yellow_threshold_hours
    green_threshold_hours = db.Column(db.Integer, default=8, nullable=False)  # Más de 8 horas = verde
    yellow_threshold_hours = db.Column(db.Integer, default=4, nullable=False)  # Entre 4-8 horas = amarillo
    red_threshold_hours = db.Column(db.Integer, default=2, nullable=False)  # Menos de 2 horas = rojo

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(80), nullable=True)

    @staticmethod
    def get_thresholds_for_clinic(clinic_id=None):
        """
        Obtiene los umbrales configurados para una clínica.
        Si no hay configuración específica, usa la global.
        Si no hay configuración global, usa valores por defecto.
        """
        if clinic_id:
            threshold = UrgencyThreshold.query.filter_by(clinic_id=clinic_id).first()
            if threshold:
                return threshold

        # Buscar configuración global
        global_threshold = UrgencyThreshold.query.filter_by(clinic_id=None).first()
        if global_threshold:
            return global_threshold

        # Crear y retornar valores por defecto
        default_threshold = UrgencyThreshold(
            clinic_id=None,
            green_threshold_hours=8,
            yellow_threshold_hours=4,
            red_threshold_hours=2
        )
        return default_threshold
