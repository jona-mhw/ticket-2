"""
Tests de validación de logs de auditoría por perfil de usuario.

Valida que:
- Superusuarios ven todos los logs de todas las clínicas
- Administradores solo ven logs de su clínica (multi-tenancy)
- Isolation entre clínicas está garantizada
- Los logs se crean con clinic_id correcto
"""
import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash

from models import (
    db, User, Clinic, LoginAudit, ActionAudit,
    ROLE_ADMIN, ROLE_CLINICAL, ROLE_VISUALIZADOR
)


@pytest.fixture
def clinic_providencia(db_session):
    """Crea clínica Providencia."""
    clinic = Clinic(name='Providencia', is_active=True)
    db_session.session.add(clinic)
    db_session.session.commit()
    return clinic


@pytest.fixture
def clinic_vitacura(db_session):
    """Crea clínica Vitacura."""
    clinic = Clinic(name='Vitacura', is_active=True)
    db_session.session.add(clinic)
    db_session.session.commit()
    return clinic


@pytest.fixture
def admin_providencia(db_session, clinic_providencia):
    """Admin de clínica Providencia."""
    user = User(
        username='admin_prov',
        email='admin@providencia.cl',
        password=generate_password_hash('password123'),
        role=ROLE_ADMIN,
        clinic_id=clinic_providencia.id,
        is_active=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def admin_vitacura(db_session, clinic_vitacura):
    """Admin de clínica Vitacura."""
    user = User(
        username='admin_vita',
        email='admin@vitacura.cl',
        password=generate_password_hash('password123'),
        role=ROLE_ADMIN,
        clinic_id=clinic_vitacura.id,
        is_active=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def clinical_vitacura(db_session, clinic_vitacura):
    """Usuario clinical de clínica Vitacura."""
    user = User(
        username='clinical_vita',
        email='clinical@vitacura.cl',
        password=generate_password_hash('password123'),
        role=ROLE_CLINICAL,
        clinic_id=clinic_vitacura.id,
        is_active=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture
def superuser(db_session):
    """Superusuario sin clinic_id."""
    user = User(
        username='superuser',
        email='super@test.com',
        password=generate_password_hash('password123'),
        role=ROLE_ADMIN,
        clinic_id=None,  # Superuser no tiene clínica
        is_active=True
    )
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.mark.auth
class TestLoginAuditMultiTenancy:
    """Tests de multi-tenancy en LoginAudit."""

    def test_superuser_sees_all_login_logs(self, db_session, superuser,
                                           admin_providencia, admin_vitacura):
        """
        Superusuario debe ver TODOS los logs de TODAS las clínicas.
        """
        # Crear logs de diferentes clínicas
        log_prov = LoginAudit(
            user_id=admin_providencia.id,
            username=admin_providencia.username,
            clinic_id=admin_providencia.clinic_id,
            ip_address='192.168.1.10'
        )
        log_vita = LoginAudit(
            user_id=admin_vitacura.id,
            username=admin_vitacura.username,
            clinic_id=admin_vitacura.clinic_id,
            ip_address='192.168.1.20'
        )
        log_super = LoginAudit(
            user_id=superuser.id,
            username=superuser.username,
            clinic_id=None,  # Superuser tiene clinic_id NULL
            ip_address='192.168.1.30'
        )

        db_session.session.add_all([log_prov, log_vita, log_super])
        db_session.session.commit()

        # Superusuario consulta TODOS los logs (sin filtro)
        all_logs = LoginAudit.query.all()

        # DEBE ver los 3 logs
        assert len(all_logs) == 3
        usernames = [log.username for log in all_logs]
        assert 'admin_prov' in usernames
        assert 'admin_vita' in usernames
        assert 'superuser' in usernames

        # Verificar que clinic_id está presente en los logs
        clinic_ids = [log.clinic_id for log in all_logs]
        assert admin_providencia.clinic_id in clinic_ids
        assert admin_vitacura.clinic_id in clinic_ids
        assert None in clinic_ids  # Superuser tiene NULL

    def test_admin_only_sees_own_clinic_login_logs(self, db_session,
                                                    admin_providencia, admin_vitacura):
        """
        Admin solo debe ver logs de SU clínica (isolation).
        """
        # Crear logs de diferentes clínicas
        log_prov = LoginAudit(
            user_id=admin_providencia.id,
            username=admin_providencia.username,
            clinic_id=admin_providencia.clinic_id
        )
        log_vita = LoginAudit(
            user_id=admin_vitacura.id,
            username=admin_vitacura.username,
            clinic_id=admin_vitacura.clinic_id
        )

        db_session.session.add_all([log_prov, log_vita])
        db_session.session.commit()

        # Admin de Providencia filtra por su clínica
        prov_logs = LoginAudit.query.filter_by(
            clinic_id=admin_providencia.clinic_id
        ).all()

        # DEBE ver solo 1 log (el suyo)
        assert len(prov_logs) == 1
        assert prov_logs[0].username == 'admin_prov'
        assert prov_logs[0].clinic_id == admin_providencia.clinic_id

        # Admin de Vitacura filtra por su clínica
        vita_logs = LoginAudit.query.filter_by(
            clinic_id=admin_vitacura.clinic_id
        ).all()

        # DEBE ver solo 1 log (el suyo)
        assert len(vita_logs) == 1
        assert vita_logs[0].username == 'admin_vita'
        assert vita_logs[0].clinic_id == admin_vitacura.clinic_id

    def test_admin_cannot_see_other_clinic_logs(self, db_session,
                                                 admin_providencia, admin_vitacura):
        """
        Admin NO debe ver logs de otras clínicas (validación de isolation).
        """
        # Crear 5 logs de Providencia y 3 de Vitacura
        for i in range(5):
            log = LoginAudit(
                user_id=admin_providencia.id,
                username=f'user_prov_{i}',
                clinic_id=admin_providencia.clinic_id
            )
            db_session.session.add(log)

        for i in range(3):
            log = LoginAudit(
                user_id=admin_vitacura.id,
                username=f'user_vita_{i}',
                clinic_id=admin_vitacura.clinic_id
            )
            db_session.session.add(log)

        db_session.session.commit()

        # Admin de Providencia consulta con filtro
        prov_logs = LoginAudit.query.filter_by(
            clinic_id=admin_providencia.clinic_id
        ).all()

        # DEBE ver exactamente 5 logs
        assert len(prov_logs) == 5

        # NINGUNO debe ser de Vitacura
        for log in prov_logs:
            assert log.clinic_id == admin_providencia.clinic_id
            assert 'vita' not in log.username

    def test_login_log_created_with_correct_clinic_id(self, db_session,
                                                       admin_providencia):
        """
        Verificar que los logs se crean con clinic_id correcto.
        """
        # Crear log de login
        log = LoginAudit(
            user_id=admin_providencia.id,
            username=admin_providencia.username,
            clinic_id=admin_providencia.clinic_id,
            ip_address='192.168.1.100',
            timestamp=datetime.utcnow()
        )
        db_session.session.add(log)
        db_session.session.commit()

        # Verificar que se guardó correctamente
        saved_log = LoginAudit.query.filter_by(
            user_id=admin_providencia.id
        ).first()

        assert saved_log is not None
        assert saved_log.clinic_id == admin_providencia.clinic_id
        assert saved_log.username == admin_providencia.username
        assert saved_log.ip_address == '192.168.1.100'


@pytest.mark.auth
class TestActionAuditMultiTenancy:
    """Tests de multi-tenancy en ActionAudit."""

    def test_superuser_sees_all_action_logs(self, db_session, superuser,
                                            admin_providencia, admin_vitacura):
        """
        Superusuario debe ver TODAS las acciones de TODAS las clínicas.
        """
        # Crear acciones de diferentes clínicas
        action_prov = ActionAudit(
            user_id=admin_providencia.id,
            username=admin_providencia.username,
            clinic_id=admin_providencia.clinic_id,
            action='create_ticket',
            target_id='TH-PROV-001',
            target_type='Ticket'
        )
        action_vita = ActionAudit(
            user_id=admin_vitacura.id,
            username=admin_vitacura.username,
            clinic_id=admin_vitacura.clinic_id,
            action='modify_fpa',
            target_id='TH-VITA-001',
            target_type='Ticket'
        )

        db_session.session.add_all([action_prov, action_vita])
        db_session.session.commit()

        # Superusuario consulta TODAS las acciones
        all_actions = ActionAudit.query.all()

        # DEBE ver las 2 acciones
        assert len(all_actions) == 2
        actions = [a.action for a in all_actions]
        assert 'create_ticket' in actions
        assert 'modify_fpa' in actions

        # Verificar clinic_id
        clinic_ids = [a.clinic_id for a in all_actions]
        assert admin_providencia.clinic_id in clinic_ids
        assert admin_vitacura.clinic_id in clinic_ids

    def test_admin_only_sees_own_clinic_actions(self, db_session,
                                                 admin_providencia, admin_vitacura):
        """
        Admin solo debe ver acciones de SU clínica.
        """
        # Crear acciones de diferentes clínicas
        action_prov = ActionAudit(
            user_id=admin_providencia.id,
            username=admin_providencia.username,
            clinic_id=admin_providencia.clinic_id,
            action='create_ticket',
            target_id='TH-PROV-001'
        )
        action_vita = ActionAudit(
            user_id=admin_vitacura.id,
            username=admin_vitacura.username,
            clinic_id=admin_vitacura.clinic_id,
            action='delete_ticket',
            target_id='TH-VITA-001'
        )

        db_session.session.add_all([action_prov, action_vita])
        db_session.session.commit()

        # Admin de Providencia filtra por su clínica
        prov_actions = ActionAudit.query.filter_by(
            clinic_id=admin_providencia.clinic_id
        ).all()

        # DEBE ver solo 1 acción (la suya)
        assert len(prov_actions) == 1
        assert prov_actions[0].action == 'create_ticket'
        assert prov_actions[0].target_id == 'TH-PROV-001'

    def test_clinical_user_isolation(self, db_session, clinical_vitacura,
                                     admin_providencia):
        """
        Usuario clinical solo ve acciones de su clínica (mismo que admin).
        """
        # Crear acciones de diferentes clínicas
        action_clinical = ActionAudit(
            user_id=clinical_vitacura.id,
            username=clinical_vitacura.username,
            clinic_id=clinical_vitacura.clinic_id,
            action='view_ticket',
            target_id='TH-VITA-002'
        )
        action_admin_prov = ActionAudit(
            user_id=admin_providencia.id,
            username=admin_providencia.username,
            clinic_id=admin_providencia.clinic_id,
            action='create_ticket',
            target_id='TH-PROV-003'
        )

        db_session.session.add_all([action_clinical, action_admin_prov])
        db_session.session.commit()

        # Clinical de Vitacura filtra por su clínica
        vita_actions = ActionAudit.query.filter_by(
            clinic_id=clinical_vitacura.clinic_id
        ).all()

        # DEBE ver solo 1 acción (la suya)
        assert len(vita_actions) == 1
        assert vita_actions[0].username == 'clinical_vita'
        assert vita_actions[0].clinic_id == clinical_vitacura.clinic_id

    def test_action_log_created_with_correct_clinic_id(self, db_session,
                                                        admin_vitacura):
        """
        Verificar que acciones se crean con clinic_id correcto.
        """
        # Crear acción
        action = ActionAudit(
            user_id=admin_vitacura.id,
            username=admin_vitacura.username,
            clinic_id=admin_vitacura.clinic_id,
            action='modify_fpa',
            target_id='TH-VITA-100',
            target_type='Ticket',
            timestamp=datetime.utcnow()
        )
        db_session.session.add(action)
        db_session.session.commit()

        # Verificar que se guardó correctamente
        saved_action = ActionAudit.query.filter_by(
            target_id='TH-VITA-100'
        ).first()

        assert saved_action is not None
        assert saved_action.clinic_id == admin_vitacura.clinic_id
        assert saved_action.username == admin_vitacura.username
        assert saved_action.action == 'modify_fpa'


@pytest.mark.auth
class TestAuditLogEdgeCases:
    """Tests de casos edge en auditoría."""

    def test_superuser_has_null_clinic_id_in_logs(self, db_session, superuser):
        """
        Logs de superusuario deben tener clinic_id = NULL.
        """
        # Crear log de superusuario
        log = LoginAudit(
            user_id=superuser.id,
            username=superuser.username,
            clinic_id=None  # Explícitamente NULL
        )
        db_session.session.add(log)
        db_session.session.commit()

        # Verificar
        saved_log = LoginAudit.query.filter_by(user_id=superuser.id).first()
        assert saved_log.clinic_id is None

    def test_filter_by_clinic_excludes_null_clinic_id(self, db_session,
                                                       superuser, admin_providencia):
        """
        Filtrar por clinic_id debe excluir logs con clinic_id NULL.
        """
        # Crear logs
        log_super = LoginAudit(
            user_id=superuser.id,
            username=superuser.username,
            clinic_id=None
        )
        log_admin = LoginAudit(
            user_id=admin_providencia.id,
            username=admin_providencia.username,
            clinic_id=admin_providencia.clinic_id
        )

        db_session.session.add_all([log_super, log_admin])
        db_session.session.commit()

        # Filtrar por clínica específica
        clinic_logs = LoginAudit.query.filter_by(
            clinic_id=admin_providencia.clinic_id
        ).all()

        # DEBE ver solo 1 log (el del admin)
        assert len(clinic_logs) == 1
        assert clinic_logs[0].username == admin_providencia.username

    def test_multiple_clinics_isolation(self, db_session, clinic_providencia,
                                       clinic_vitacura):
        """
        Validar isolation entre múltiples clínicas.
        """
        # Crear 3 clínicas con usuarios
        clinic_elqui = Clinic(name='Elqui', is_active=True)
        db_session.session.add(clinic_elqui)
        db_session.session.commit()

        users = []
        for i, clinic in enumerate([clinic_providencia, clinic_vitacura, clinic_elqui]):
            user = User(
                username=f'user_{clinic.name.lower()}',
                email=f'user@{clinic.name.lower()}.cl',
                password=generate_password_hash('password123'),
                role=ROLE_ADMIN,
                clinic_id=clinic.id,
                is_active=True
            )
            db_session.session.add(user)
            users.append((user, clinic))

        db_session.session.commit()

        # Crear logs para cada usuario
        for user, clinic in users:
            log = LoginAudit(
                user_id=user.id,
                username=user.username,
                clinic_id=clinic.id
            )
            db_session.session.add(log)

        db_session.session.commit()

        # Validar que cada clínica solo ve sus logs
        for user, clinic in users:
            clinic_logs = LoginAudit.query.filter_by(clinic_id=clinic.id).all()

            # Debe ver exactamente 1 log
            assert len(clinic_logs) == 1
            assert clinic_logs[0].clinic_id == clinic.id
            assert clinic_logs[0].username == user.username
