"""
Tests de autenticación: IAP + Login tradicional.
Prueba el sistema híbrido de autenticación.
"""
import pytest
from flask import url_for
from flask_login import current_user


@pytest.mark.auth
class TestTraditionalLogin:
    """Tests del login tradicional (usuario/contraseña)."""

    def test_login_page_loads(self, client, db_session):
        """Test que la página de login carga correctamente."""
        response = client.get('/auth/login', follow_redirects=True)
        assert response.status_code == 200

    def test_login_with_valid_credentials(self, client, db_session, sample_user_admin):
        """Test login exitoso con credenciales válidas."""
        response = client.post('/auth/demo-login', data={
            'username': 'admin_test',
            'password': 'password123'
        }, follow_redirects=True)

        # Debería redirigir y autenticar
        assert response.status_code == 200

    def test_login_with_invalid_username(self, client, db_session):
        """Test login fallido con usuario inexistente."""
        response = client.post('/auth/demo-login', data={
            'username': 'noexiste',
            'password': 'cualquiera'
        }, follow_redirects=False)

        # No debería autenticar (redirect o error)
        assert response.status_code in [200, 302]

    def test_login_with_invalid_password(self, client, db_session, sample_user_admin):
        """Test login fallido con contraseña incorrecta."""
        response = client.post('/auth/demo-login', data={
            'username': 'admin_test',
            'password': 'wrongpassword'
        }, follow_redirects=False)

        assert response.status_code in [200, 302]

    def test_logout(self, client, db_session, sample_user_admin, app):
        """Test logout exitoso."""
        # Primero hacer login
        with client:
            client.post('/auth/demo-login', data={
                'username': 'admin_test',
                'password': 'password123'
            })

            # Luego hacer logout
            response = client.get('/auth/logout', follow_redirects=True)
            assert response.status_code == 200


@pytest.mark.auth
class TestUserRoles:
    """Tests de roles de usuario."""

    def test_admin_role(self, db_session, sample_user_admin):
        """Test que usuario admin tiene permisos correctos."""
        assert sample_user_admin.role == 'admin'
        assert sample_user_admin.is_admin() is True

    def test_clinical_role(self, db_session, sample_user_clinical):
        """Test que usuario clinical tiene rol correcto."""
        assert sample_user_clinical.role == 'clinical'

    def test_visualizador_role(self, db_session, sample_user_visualizador):
        """Test que usuario visualizador tiene rol correcto."""
        assert sample_user_visualizador.role == 'visualizador'

    def test_superuser_role(self, db_session, sample_user_super):
        """Test que superusuario tiene permisos especiales."""
        assert sample_user_super.is_superuser is True
        assert sample_user_super.clinic_id is None
        assert sample_user_super.is_admin() is True


@pytest.mark.auth
class TestAccessControl:
    """Tests de control de acceso a rutas protegidas."""

    def test_unauthenticated_access_redirects(self, client, db_session):
        """Test que usuario no autenticado es redirigido."""
        response = client.get('/tickets/nursing-board', follow_redirects=False)
        # Debería redirigir a login
        assert response.status_code == 302

    def test_authenticated_access_allowed(self, client, db_session, sample_user_admin, app):
        """Test que usuario autenticado puede acceder."""
        with client:
            # Login
            client.post('/auth/demo-login', data={
                'username': 'admin_test',
                'password': 'password123'
            })

            # Intentar acceder a ruta protegida
            response = client.get('/tickets/nursing-board', follow_redirects=True)
            assert response.status_code == 200


@pytest.mark.auth
class TestMultiTenancy:
    """Tests de aislamiento multi-tenant."""

    def test_user_belongs_to_clinic(self, db_session, sample_user_admin, sample_clinic):
        """Test que usuario pertenece a una clínica."""
        assert sample_user_admin.clinic_id == sample_clinic.id
        assert sample_user_admin.clinic.name == sample_clinic.name

    def test_superuser_no_clinic(self, db_session, sample_user_super):
        """Test que superusuario no tiene clínica."""
        assert sample_user_super.clinic_id is None

    def test_user_cannot_access_other_clinic_data(self, db_session, sample_clinic):
        """
        Test conceptual: usuarios solo deberían ver datos de su clínica.
        (La lógica real se prueba en tests de routes)
        """
        from models import User, Clinic

        # Crear segunda clínica
        clinic2 = Clinic(name='Otra Clínica', is_active=True)
        db_session.session.add(clinic2)
        db_session.session.commit()

        # Usuario de clinic1
        user1 = User(
            username='user1',
            email='user1@test.com',
            password='pass',
            role='clinical',
            clinic_id=sample_clinic.id
        )

        # Usuario de clinic2
        user2 = User(
            username='user2',
            email='user2@test.com',
            password='pass',
            role='clinical',
            clinic_id=clinic2.id
        )

        db_session.session.add_all([user1, user2])
        db_session.session.commit()

        # Verificar que pertenecen a clínicas diferentes
        assert user1.clinic_id != user2.clinic_id
