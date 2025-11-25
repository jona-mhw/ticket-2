from app import create_app
from models import db, Clinic, Superuser, User
from utils.string_utils import generate_prefix

app = create_app()
with app.app_context():
    print(f'\n✅ Base de datos inicializada con SEED MINIMAL LOCAL')
    print(f'\n📊 Conteo:')
    print(f'  - Clínicas: {Clinic.query.count()}')
    print(f'  - Superusers: {Superuser.query.count()}')
    print(f'  - Usuarios Demo: {User.query.count()}')
    
    print(f'\n🏥 Clínicas creadas:')
    for c in Clinic.query.all():
        print(f'  - {c.name}')
    
    print(f'\n👤 Superusers:')
    for s in Superuser.query.all():
        print(f'  - {s.email}')
    
    print(f'\n👥 Usuarios Demo (password: password123):')
    print('='*60)
    for clinic in Clinic.query.all()[:3]:  # Primeras 3 clínicas
        prefix = generate_prefix(clinic.name)
        print(f'\n{clinic.name}:')
        for role in ['admin', 'clinical', 'visualizador']:
            username = f'{role}_{prefix}'
            user = User.query.filter_by(username=username).first()
            if user:
                print(f'  ✓ {username} (role: {user.role})')
    
    if Clinic.query.count() > 3:
        print(f'\n... y {(Clinic.query.count() - 3) * 3} usuarios más')
    
    print('\n' + '='*60)
    print(f'Total usuarios creados: {User.query.count()}')
