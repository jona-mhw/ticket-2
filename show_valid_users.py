from app import create_app
from models import db, User, Clinic

app = create_app()
with app.app_context():
    print('\n' + '='*70)
    print('SOLUCION: Usuarios recomendados para crear tickets')
    print('='*70)
    
    # Mostrar usuarios con clinic_id válido
    users_with_clinic = User.query.filter(User.clinic_id.isnot(None)).all()
    
    print(f'\n✅ Usuarios CON clínica asignada ({len(users_with_clinic)} total):')
    print('='*70)
    
    # Agrupar por clínica
    clinics = {}
    for user in users_with_clinic:
        if user.clinic_id not in clinics:
            clinics[user.clinic_id] = []
        clinics[user.clinic_id].append(user)
    
    # Mostrar primeras 3 clínicas
    for clinic_id in list(clinics.keys())[:3]:
        clinic = Clinic.query.get(clinic_id)
        print(f'\n🏥 {clinic.name}:')
        for user in clinics[clinic_id]:
            password_hint = 'password123'
            print(f'   • Username: {user.username:<25} Role: {user.role:<15} Password: {password_hint}')
    
    if len(clinics) > 3:
        print(f'\n... y {len(clinics) - 3} clínicas más con usuarios')
    
    # Mostrar usuarios SIN clínica (no recomendados para crear tickets)
    users_without_clinic = User.query.filter(User.clinic_id.is_(None)).all()
    if users_without_clinic:
        print(f'\n\n❌ Usuarios SIN clín ica asignada (NO usar para crear tickets):')
        print('='*70)
        for user in users_without_clinic:
            print(f'   • {user.username} (is_superuser: probablemente True)')
    
    print('\n' + '='*70)
    print('RECOMENDACION: Cierra sesión y vuelve a entrar con uno de los')
    print('usuarios CON clínica asignada listados arriba.')
    print('='*70 + '\n')
