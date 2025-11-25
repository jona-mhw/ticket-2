from app import create_app
from models import db, Clinic, Specialty, Surgery, Doctor, StandardizedReason, User

app = create_app()
with app.app_context():
    print('\n' + '='*70)
    print('📊 ESTADO ACTUAL DE LA BASE DE DATOS LOCAL')
    print('='*70)
    
    print(f'\n🏥 Clínicas: {Clinic.query.count()}')
    print(f'👥 Usuarios: {User.query.count()}')
    print(f'⚕️  Especialidades: {Specialty.query.count()}')
    print(f'🏥 Cirugías: {Surgery.query.count()}')
    print(f'👨‍⚕️ Doctores: {Doctor.query.count()}')
    print(f'📋 Razones Estandarizadas: {StandardizedReason.query.count()}')
    
    # Mostrar detalles de especialidades y cirugías
    if Specialty.query.count() > 0:
        print(f'\n📋 Especialidades creadas:')
        for spec in Specialty.query.all():
            clinic_name = spec.clinic.name if spec.clinic else "Sin clínica"
            print(f'  • ID: {spec.id} | {spec.name} | Clínica: {clinic_name}')
    
    if Surgery.query.count() > 0:
        print(f'\n🏥 Cirugías creadas:')
        for surg in Surgery.query.all():
            clinic_name = surg.clinic.name if surg.clinic else "Sin clínica"
            spec_name = surg.specialty.name if surg.specialty else "Sin especialidad"
            print(f'  • ID: {surg.id} | {surg.name} ({surg.base_stay_hours}h)')
            print(f'    Especialidad: {spec_name} | Clínica: {clinic_name}')
    
    if Doctor.query.count() > 0:
        print(f'\n👨‍⚕️ Doctores creados:')
        for doc in Doctor.query.all()[:5]:  # Primeros 5
            clinic_name = doc.clinic.name if doc.clinic else "Sin clínica"
            print(f'  • {doc.name} | {doc.specialty} | Clínica: {clinic_name}')
        if Doctor.query.count() > 5:
            print(f'  ... y {Doctor.query.count() - 5} más')
    
    print('\n' + '='*70)
