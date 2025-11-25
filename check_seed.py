from app import create_app
from models import db, Clinic, Superuser, User

app = create_app()
with app.app_context():
    print('\n' + '='*70)
    print('✅ SEED MINIMAL LOCAL - ESTADO DE LA BASE DE DATOS')
    print('='*70)
    
    print(f'\n📊 Totales:')
    print(f'  • Clínicas: {Clinic.query.count()}')
    print(f'  • Superusers: {Superuser.query.count()}')
    print(f'  • Usuarios Demo: {User.query.count()}')
    
    # Global Admin
    print(f'\n👑 Global Admin:')
    global_admin = User.query.filter_by(username='global_admin').first()
    if global_admin:
        print(f'  ✓ username: {global_admin.username}')
        print(f'  ✓ email: {global_admin.email}')
        print(f'  ✓ role: {global_admin.role}')
        print(f'  ✓ clinic_id: {global_admin.clinic_id} (None = acceso a todas las clínicas)')
    else:
        print('  ✗ NO ENCONTRADO')
    
    # Usuarios por clínica
    print(f'\n👥 Usuarios Demo por Clínica (password: password123):')
    print('─'*70)
    
    clinics = Clinic.query.all()
    for i, clinic in enumerate(clinics[:3], 1):
        print(f'\n{i}. {clinic.name}:')
        users = User.query.filter_by(clinic_id=clinic.id).all()
        for user in users:
            print(f'   • {user.username:<20} (role: {user.role})')
    
    if len(clinics) > 3:
        remaining_clinics = len(clinics) - 3
        remaining_users = User.query.filter(User.clinic_id.isnot(None)).count() - (3 * 3)
        print(f'\n... y {remaining_clinics} clínicas más con {remaining_users} usuarios adicionales')
    
    print('\n' + '='*70)
    print(f'TOTAL USUARIOS: {User.query.count()} (1 global_admin + {User.query.count()-1} usuarios de clínicas)')
    print('='*70 + '\n')
