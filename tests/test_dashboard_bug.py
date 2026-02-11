import pytest
from models import Surgery, Clinic, Specialty

def test_dashboard_surgery_filter_bug(client, app, db_session, sample_user_super):
    """
    Test para verificar que el dropdown de cirugías se filtra correctamente por clínica
    cuando un superusuario selecciona una clínica específica.
    Bug reportado: El dropdown mostraba todas las cirugías sin importar la clínica seleccionada.
    """
    # ... (setup code remains same, implied context) ...
    # 1. Setup: Crear clínicas y cirugías
    clinic_a = Clinic(name='Clinica A', is_active=True)
    clinic_b = Clinic(name='Clinica B', is_active=True)
    db_session.session.add_all([clinic_a, clinic_b])
    db_session.session.commit()
    
    # Necesitamos especialidades para crear cirugías
    spec_a = Specialty(name='Esp A', clinic_id=clinic_a.id)
    spec_b = Specialty(name='Esp B', clinic_id=clinic_b.id)
    db_session.session.add_all([spec_a, spec_b])
    db_session.session.commit()
    
    surg_a = Surgery(name='Cirugia A', base_stay_hours=1, specialty_id=spec_a.id, clinic_id=clinic_a.id, is_active=True)
    surg_b = Surgery(name='Cirugia B', base_stay_hours=1, specialty_id=spec_b.id, clinic_id=clinic_b.id, is_active=True)
    db_session.session.add_all([surg_a, surg_b])
    db_session.session.commit()
    
    # 2. Login como superusuario
    # Usamos el contexto de la aplicación para loguear al usuario
    with client:
        with app.test_request_context():
            from flask_login import login_user
            login_user(sample_user_super)
        
        # 3. Request al dashboard filtrando por Clinica A
        # El endpoint es /dashboard/ (definido en routes/dashboard.py como @dashboard_bp.route('/'))
        # Pero el blueprint se registra probablemente con prefijo /dashboard. Verificaré esto.
        # Asumiendo prefix /dashboard por ahora.
        response = client.get(f'/dashboard/?clinic_id={clinic_a.id}')
        
        # Si devuelve 302 puede ser redirect por login fallido o url incorrecta.
        # Si devuelve 404 es url incorrecta.
        assert response.status_code == 200
        
        # 4. Verificar el contenido
        content = response.data.decode('utf-8')
        
        # Cirugía A debe estar en las opciones
        assert 'Cirugia A' in content, "La cirugía de la clínica seleccionada debería aparecer"
        
        # Cirugía B NO debe estar (este era el bug)
        assert 'Cirugia B' not in content, "Las cirugías de otras clínicas NO deberían aparecer"
