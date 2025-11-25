import click
import json
from flask.cli import with_appcontext
from sqlalchemy import text
from flask_migrate import upgrade as alembic_upgrade
from models import (
    db, User, Clinic, Surgery, Specialty, Doctor,
    # Issue #54: DischargeTimeSlot eliminado - se usa TimeBlockHelper
    StandardizedReason, Patient, Ticket, Superuser,
    ROLE_ADMIN, ROLE_CLINICAL, ROLE_VISUALIZADOR,
    TICKET_STATUS_VIGENTE, TICKET_STATUS_ANULADO,
    REASON_CATEGORY_INITIAL, REASON_CATEGORY_MODIFICATION, REASON_CATEGORY_ANNULMENT
)
from datetime import datetime, timedelta
import random
import os
from flask import current_app
from routes.utils import generate_prefix

# --- Nombres Realistas para Demo ---
NOMBRES_DEMO = {
    'admin': [
        'Juan Carlos Pérez González', 'María Fernanda Rojas Silva', 'Carlos Alberto Mendoza Torres',
        'Patricia Andrea González Muñoz', 'Roberto Ignacio Valenzuela Castro', 'Carmen Gloria Espinoza Ramos',
        'Francisco Javier Morales Herrera', 'Claudia Marcela Soto Campos', 'Luis Fernando Bravo Ortiz'
    ],
    'clinical': [
        'Francisca Alejandra Muñoz Vargas', 'Andrés Felipe Castro Loyola', 'Valentina Paz Reyes Cortés',
        'Diego Sebastián Tapia Figueroa', 'Constanza Isabel Contreras Núñez', 'Matías Eduardo Henríquez Parra',
        'Sofía Gabriela Navarro Flores', 'Nicolás Antonio Vergara Rubio', 'Daniela Carolina Sepúlveda Araya'
    ],
    'visualizador': [
        'Beatriz Elena Campos Díaz', 'Fernando José Ortiz Medina', 'Carolina Andrea Bustos Saavedra',
        'Rodrigo Alejandro Gutiérrez Vega', 'Lorena Maritza Pizarro Molina', 'Pablo Ignacio Ríos Fuentes',
        'Andrea Cristina Lagos Ramírez', 'Jorge Eduardo Sandoval Peña', 'Mónica Isabel Carrasco Jara'
    ],
    'paciente': [
        # Nombres masculinos
        ('Pedro Antonio', 'Martínez Flores'), ('José Luis', 'Silva Contreras'), ('Ricardo Andrés', 'Vargas Muñoz'),
        ('Héctor Manuel', 'Rojas Campos'), ('Sergio Patricio', 'Torres Soto'), ('Raúl Enrique', 'Vera Castro'),
        ('Alberto Gabriel', 'Núñez Pérez'), ('Tomás Eduardo', 'Méndez Loyola'), ('Mauricio Hernán', 'Ponce Araya'),
        ('Felipe Cristóbal', 'Gallardo Herrera'), ('Gonzalo Ignacio', 'Cabrera Tapia'), ('Marcelo Esteban', 'Figueroa Ramos'),
        # Nombres femeninos
        ('Rosa María', 'Cortés Morales'), ('Elena Victoria', 'Guzmán Silva'), ('Isabel Cristina', 'Castillo Vega'),
        ('Sandra Alejandra', 'Bravo Muñoz'), ('Gloria Patricia', 'Santana Flores'), ('Teresa Angélica', 'Fuentes Díaz'),
        ('Cecilia Beatriz', 'Ávila Torres'), ('Marcela Soledad', 'Escobar Rojas'), ('Verónica Paola', 'Cárdenas Pérez'),
        ('Silvana Loreto', 'Moreno Contreras'), ('Javiera Monserrat', 'Araya González'), ('Pamela Andrea', 'Navarro Castro')
    ]
}

# --- Seeding Helper Functions ---

def seed_db():
    """Orchestrates the database seeding process in a single transaction."""
    
    # 1. Seed Clinics
    if Clinic.query.first():
        print("Database already seeded. Skipping.")
        return

    print("Populating with all clinics...")
    clinic_names = [
        "Clínica RedSalud Iquique", "Clínica RedSalud Elqui", "Clínica RedSalud Valparaíso",
        "Clínica RedSalud Providencia", "Clínica RedSalud Santiago", "Clínica RedSalud Vitacura",
        "Clínica RedSalud Rancagua", "Clínica RedSalud Mayor Temuco", "Clínica RedSalud Magallanes"
    ]
    clinics_to_add = [Clinic(name=name) for name in clinic_names]
    db.session.add_all(clinics_to_add)
    db.session.flush()  # Flush to get clinic IDs
    print(f"{len(clinics_to_add)} clinics populated.")

    all_clinics = Clinic.query.all()

    # --- Lists to hold all new objects ---
    users_to_add = []
    specialties_to_add = []
    surgeries_to_add = []
    doctors_to_add = []
    slots_to_add = []
    reasons_to_add = []
    patients_to_add = []
    tickets_to_add = []

    patient_rut_counter = 1

    # Create a global admin user (superuser) ONCE, before the clinic loop
    global_admin_username = 'global_admin'
    global_admin_email = 'global_admin@tickethome.com'
    if not User.query.filter_by(username=global_admin_username).first():
        users_to_add.append(User(
            username=global_admin_username, email=global_admin_email,
            role=ROLE_ADMIN, password='password123', clinic_id=None # clinic_id is None for superuser
        ))

    # Add global_admin email to Superuser table if not exists
    if not Superuser.query.filter_by(email=global_admin_email).first():
        superuser_entry = Superuser(email=global_admin_email)
        db.session.add(superuser_entry)
        db.session.flush()
        print(f"Added {global_admin_email} to Superuser table")

    for clinic_idx, clinic in enumerate(all_clinics):
        prefix = generate_prefix(clinic.name)
        print(f"Preparing data for {clinic.name} ({prefix})...")

        # 2. Seed Users (con nombres realistas)
        for role in [ROLE_ADMIN, ROLE_CLINICAL, ROLE_VISUALIZADOR]:
            username = f'{role}_{prefix}'
            if not User.query.filter_by(username=username).first():
                # Asignar nombre realista basado en el índice de la clínica
                nombre_real = NOMBRES_DEMO[role][clinic_idx % len(NOMBRES_DEMO[role])]
                # Nota: Los nombres realistas están disponibles en NOMBRES_DEMO si se agrega campo full_name al modelo User
                users_to_add.append(User(
                    username=username,
                    email=f'{username}@tickethome.com',
                    role=role,
                    password='password123',
                    clinic_id=clinic.id
                ))
        
        # 3. Seed Master Data
        # Specialties
        specialties_data = ['Cirugía General', 'Ginecología', 'Traumatología', 'Cirugía Pediátrica']
        clinic_specialties = [Specialty(name=f"{s_name} ({prefix})", clinic_id=clinic.id) for s_name in specialties_data]
        specialties_to_add.extend(clinic_specialties)
        db.session.add_all(clinic_specialties)
        db.session.flush() # Flush to get specialty IDs

        # Surgeries
        surgeries_data = [
            {'name': 'Apendicectomía Laparoscópica', 'specialty_name': 'Cirugía General', 'base_stay_hours': 24, 'is_ambulatory': False},
            {'name': 'Colecistectomía Laparoscópica', 'specialty_name': 'Cirugía General', 'base_stay_hours': 48, 'is_ambulatory': True, 'ambulatory_cutoff_hour': 14},
            {'name': 'Histerectomía Abdominal', 'specialty_name': 'Ginecología', 'base_stay_hours': 72, 'is_ambulatory': False},
            {'name': 'Artroscopia de Rodilla', 'specialty_name': 'Traumatología', 'base_stay_hours': 8, 'is_ambulatory': True, 'ambulatory_cutoff_hour': 16},
        ]
        clinic_surgeries = []
        for s_data in surgeries_data:
            specialty = next((s for s in clinic_specialties if s.name.startswith(s_data['specialty_name'])), None)
            if specialty:
                clinic_surgeries.append(Surgery(
                    name=f"{s_data['name']} ({prefix})", specialty_id=specialty.id,
                    base_stay_hours=s_data['base_stay_hours'], is_ambulatory=s_data['is_ambulatory'],
                    ambulatory_cutoff_hour=s_data.get('ambulatory_cutoff_hour'), clinic_id=clinic.id
                ))
        surgeries_to_add.extend(clinic_surgeries)
        # Flush surgeries immediately so they get IDs for ticket creation
        db.session.add_all(clinic_surgeries)
        db.session.flush()

        # Doctors
        doctors_data = [
            {'name': 'Dr. Carlos Mendoza', 'specialty': 'Cirugía General', 'license': '12345'},
            {'name': 'Dra. Ana María Pérez', 'specialty': 'Ginecología', 'license': '54321'},
        ]
        clinic_doctors = [Doctor(
            name=f"{d['name']} ({prefix})", specialty=d['specialty'],
            rut=f"{d['license']}-{prefix}", clinic_id=clinic.id
        ) for d in doctors_data]
        doctors_to_add.extend(clinic_doctors)
        # Flush doctors immediately so they get IDs for ticket creation
        db.session.add_all(clinic_doctors)
        db.session.flush()

        # Issue #54: DischargeTimeSlot eliminado - los bloques horarios se generan dinámicamente
        # Los bloques son FIJOS (24 bloques de 2h) y no requieren almacenamiento en BD

        # Standardized Reasons (only if they don't exist for the clinic)
        if not StandardizedReason.query.filter_by(clinic_id=clinic.id).first():
            reasons_data = [
                # Razones de Discrepancia Inicial (Al crear ticket)
                {'reason': 'Criterio médico especializado requiere mayor tiempo de observación', 'category': REASON_CATEGORY_INITIAL},
                {'reason': 'Complejidad del procedimiento requiere hospitalización extendida', 'category': REASON_CATEGORY_INITIAL},
                {'reason': 'Comorbilidades del paciente requieren cuidado prolongado', 'category': REASON_CATEGORY_INITIAL},
                {'reason': 'Protocolo clínico específico de la especialidad', 'category': REASON_CATEGORY_INITIAL},
                {'reason': 'Evaluación pre-alta requiere tiempo adicional', 'category': REASON_CATEGORY_INITIAL},
                # Razones de Modificación (Aplazamiento de FPA)
                {'reason': 'Complicación post-operatoria', 'category': REASON_CATEGORY_MODIFICATION},
                {'reason': 'Condición del paciente requiere más observación', 'category': REASON_CATEGORY_MODIFICATION},
                {'reason': 'Interconsulta médica pendiente', 'category': REASON_CATEGORY_MODIFICATION},
                {'reason': 'Espera de resultados de exámenes', 'category': REASON_CATEGORY_MODIFICATION},
                {'reason': 'Necesidad de cuidados intensivos adicionales', 'category': REASON_CATEGORY_MODIFICATION},
                {'reason': 'Ajuste por indicación médica especializada', 'category': REASON_CATEGORY_MODIFICATION},
                {'reason': 'Control de dolor inadecuado', 'category': REASON_CATEGORY_MODIFICATION},
                # Razones de Anulación
                {'reason': 'Error en el ingreso de datos', 'category': REASON_CATEGORY_ANNULMENT},
                {'reason': 'Paciente dado de alta antes de lo previsto', 'category': REASON_CATEGORY_ANNULMENT},
                {'reason': 'Traslado a otra institución', 'category': REASON_CATEGORY_ANNULMENT},
                {'reason': 'Cancelación de procedimiento', 'category': REASON_CATEGORY_ANNULMENT},
            ]
            reasons_to_add.extend([StandardizedReason(reason=r['reason'], category=r['category'], clinic_id=clinic.id) for r in reasons_data])

        # 4. Seed Patients (con nombres realistas)
        clinic_patients = []
        for i in range(5): # Create 5 patients per clinic
            rut = f'{patient_rut_counter:08d}-K'
            # Seleccionar nombre de paciente de la lista
            nombre_idx = (clinic_idx * 5 + i) % len(NOMBRES_DEMO['paciente'])
            primer_nombre, apellido_paterno = NOMBRES_DEMO['paciente'][nombre_idx]

            clinic_patients.append(Patient(
                rut=rut,
                primer_nombre=primer_nombre,
                apellido_paterno=apellido_paterno,
                age=random.randint(20, 80),
                sex=random.choice(['Male', 'Female']),
                clinic_id=clinic.id
            ))
            patient_rut_counter += 1
        patients_to_add.extend(clinic_patients)
        db.session.add_all(clinic_patients)
        db.session.flush() # Flush to get patient IDs

        # 5. Seed Tickets
        if not all([clinic_patients, clinic_surgeries, clinic_doctors]):
            continue

        for i in range(15): # Create 15 tickets per clinic
            now = datetime.now()

            # Seleccionar cirugía y paciente aleatorios
            selected_surgery = random.choice(clinic_surgeries)
            selected_patient = random.choice(clinic_patients)
            selected_doctor = random.choice(clinic_doctors)

            # Generar pavilion_end_time aleatorio en el pasado reciente (últimos 30 días)
            pavilion_end_time = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

            # Calcular FPA correctamente usando el método del modelo
            system_calculated_fpa, overnight_stays = Ticket().calculate_fpa(pavilion_end_time, selected_surgery)

            # Calcular medical_discharge_date (entre 1 y 5 días después del pavilion_end_time)
            medical_discharge_date = (pavilion_end_time + timedelta(days=random.randint(1, 5))).date()

            # Generar bed_number y location aleatorios (Issue #49)
            bed_number = f"{random.randint(101, 450)}" if random.random() > 0.2 else None  # 80% de tickets tienen cama
            locations = ['Piso 2', 'Piso 3', 'UCI', 'Recuperación', 'Ala Norte', 'Ala Sur', 'Sector A', 'Sector B']
            location = random.choice(locations) if bed_number and random.random() > 0.3 else None  # 70% de tickets con cama tienen ubicación

            ticket = Ticket(
                id=f'TH-{prefix.upper()}-{now.year}-{i+1:03d}',
                patient_id=selected_patient.id,
                surgery_id=selected_surgery.id,
                doctor_id=selected_doctor.id,
                pavilion_end_time=pavilion_end_time,
                medical_discharge_date=medical_discharge_date,
                system_calculated_fpa=system_calculated_fpa,
                initial_fpa=system_calculated_fpa,
                current_fpa=system_calculated_fpa,
                overnight_stays=overnight_stays,
                surgery_name_snapshot=selected_surgery.name,
                surgery_base_hours_snapshot=selected_surgery.base_stay_hours,
                bed_number=bed_number,
                location=location,
                created_by=f'{ROLE_ADMIN}_{prefix}',
                clinic_id=clinic.id,
                status=TICKET_STATUS_VIGENTE
            )
            tickets_to_add.append(ticket)

    # --- Final Bulk Insert and Commit ---
    try:
        print("Adding all objects to session...")
        if users_to_add: db.session.add_all(users_to_add)
        if specialties_to_add: db.session.add_all(specialties_to_add)
        # surgeries already added and flushed per clinic
        # doctors already added and flushed per clinic
        # slots already added and flushed per clinic
        if reasons_to_add: db.session.add_all(reasons_to_add)
        # patients already added and flushed per clinic
        if tickets_to_add: db.session.add_all(tickets_to_add)
        
        print("Committing transaction...")
        db.session.commit()
        print("Database seeding complete.")
    except Exception as e:
        print(f"An error occurred during seeding: {e}")
        db.session.rollback()

def _sync_superusers():
    """Syncs superuser emails from environment variable to the database."""
    import os

    superuser_emails_str = os.environ.get('SUPERUSER_EMAILS', '')

    if not superuser_emails_str:
        print("No SUPERUSER_EMAILS environment variable found. Skipping superuser sync.")
        return

    # Parse emails separated by semicolon
    superuser_emails = [email.strip() for email in superuser_emails_str.split(';') if email.strip()]

    if not superuser_emails:
        print("SUPERUSER_EMAILS is empty. Skipping superuser sync.")
        return

    print(f"Syncing {len(superuser_emails)} superuser email(s)...")

    # Get existing superusers from DB
    existing_superusers = {su.email: su for su in Superuser.query.all()}

    # Add new superusers
    for email in superuser_emails:
        if email not in existing_superusers:
            new_superuser = Superuser(email=email)
            db.session.add(new_superuser)
            print(f"  + Added superuser: {email}")
        else:
            print(f"  ~ Already exists: {email}")

    # Remove superusers not in the list (cleanup)
    for email, su in existing_superusers.items():
        if email not in superuser_emails:
            db.session.delete(su)
            print(f"  - Removed superuser: {email}")

    db.session.commit()
    print("Superuser sync complete.")

def _create_minimal_seed():
    """Creates only clinics and discharge time slots."""
    # Check if clinics already exist
    if Clinic.query.first():
        print("Clinics already exist. Skipping.")
        return

    # Create clinics
    clinic_names = [
        "Clínica RedSalud Iquique", "Clínica RedSalud Elqui", "Clínica RedSalud Valparaíso",
        "Clínica RedSalud Providencia", "Clínica RedSalud Santiago", "Clínica RedSalud Vitacura",
        "Clínica RedSalud Rancagua", "Clínica RedSalud Mayor Temuco", "Clínica RedSalud Magallanes"
    ]
    clinics_to_add = [Clinic(name=name) for name in clinic_names]
    db.session.add_all(clinics_to_add)
    db.session.commit()
    print(f"{len(clinics_to_add)} clinics created.")

# --- Click Commands ---

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database with migrations, clinics, and discharge time slots only."""
    click.echo('Applying all database migrations...')
    alembic_upgrade()
    click.echo('Database tables created via migrations.')

    # Sync superusers first
    click.echo('Syncing superusers from SUPERUSER_EMAILS...')
    _sync_superusers()

    # Only create clinics and discharge time slots
    click.echo('Creating clinics and discharge time slots...')
    _create_minimal_seed()

    click.echo("Database initialized with clinics and discharge time slots only.")

@click.command('reset-db')
@with_appcontext
def reset_db_command():
    """Drops all tables, re-creates schema, applies migrations, syncs superusers, and seeds data."""
    with db.engine.connect() as con:
        with con.begin(): # Use a transaction
            click.echo('Wiping database schema (DROP SCHEMA public CASCADE)...')
            con.execute(text('DROP SCHEMA public CASCADE;'))
            con.execute(text('CREATE SCHEMA public;'))

    click.echo('Database schema wiped and recreated.')

    # Run all migrations to create the schema correctly
    click.echo('Applying all database migrations...')
    alembic_upgrade()
    click.echo('Database tables created via migrations.')

    # Sync superusers from environment variable
    click.echo('Syncing superusers from environment...')
    _sync_superusers()

    # Seed database with demo data
    click.echo('Seeding database with demo data...')
    seed_db()

    click.echo('Database has been reset, superusers synced, and demo data seeded.')

@click.command('update-users')
@with_appcontext
def update_users_command():
    """Updates users with correct clinic structure for authentication."""
    click.echo('Updating users with correct clinic structure...')
    
    # Get all clinics
    clinics = Clinic.query.all()
    if not clinics:
        click.echo('No clinics found. Please run init-db first.')
        return
    
    users_created = 0
    users_updated = 0
    
    # Create or update users for each clinic
    for clinic in clinics:
        prefix = generate_prefix(clinic.name)
        click.echo(f'Processing users for {clinic.name} ({prefix})...')
        
        # Check/Create admin user
        admin_username = f'admin_{prefix}'
        admin_user = User.query.filter_by(username=admin_username).first()
        if not admin_user:
            admin_user = User(
                username=admin_username,
                email=f'{admin_username}@tickethome.com',
                role=ROLE_ADMIN,
                password='password123',
                clinic_id=clinic.id
            )
            db.session.add(admin_user)
            users_created += 1
            click.echo(f'  + Created: {admin_username}')
        else:
            admin_user.clinic_id = clinic.id
            admin_user.role = ROLE_ADMIN
            users_updated += 1
            click.echo(f'  ~ Updated: {admin_username}')
        
        # Check/Create clinical user
        clinical_username = f'clinical_{prefix}'
        clinical_user = User.query.filter_by(username=clinical_username).first()
        if not clinical_user:
            clinical_user = User(
                username=clinical_username,
                email=f'{clinical_username}@tickethome.com',
                role=ROLE_CLINICAL,
                password='password123',
                clinic_id=clinic.id
            )
            db.session.add(clinical_user)
            users_created += 1
            click.echo(f'  + Created: {clinical_username}')
        else:
            clinical_user.clinic_id = clinic.id
            clinical_user.role = ROLE_CLINICAL
            users_updated += 1
            click.echo(f'  ~ Updated: {clinical_username}')
        
        # Check/Create visualizador user
        visualizador_username = f'visualizador_{prefix}'
        visualizador_user = User.query.filter_by(username=visualizador_username).first()
        if not visualizador_user:
            visualizador_user = User(
                username=visualizador_username,
                email=f'{visualizador_username}@tickethome.com',
                role=ROLE_VISUALIZADOR,
                password='password123',
                clinic_id=clinic.id
            )
            db.session.add(visualizador_user)
            users_created += 1
            click.echo(f'  + Created: {visualizador_username}')
        else:
            visualizador_user.clinic_id = clinic.id
            visualizador_user.role = ROLE_VISUALIZADOR
            users_updated += 1
            click.echo(f'  ~ Updated: {visualizador_username}')
    
    db.session.commit()
    total_users = User.query.count()
    click.echo(f'User update complete. Created: {users_created}, Updated: {users_updated}, Total users: {total_users}')

@click.command('db-nuke')
@with_appcontext
def db_nuke_command():
    """Drops the public schema to wipe the database clean."""
    with db.engine.connect() as con:
        with con.begin(): # Use a transaction
            click.echo('Wiping database schema (DROP SCHEMA public CASCADE)...')
            con.execute(text('DROP SCHEMA public CASCADE;'))
            con.execute(text('CREATE SCHEMA public;'))
    click.echo('Database schema wiped and recreated.')

@click.command('run-upgrade')
@with_appcontext
def run_upgrade_command():
    """Runs the database migrations."""
    click.echo('Starting database upgrade...')
    alembic_upgrade()
    click.echo('Database upgrade complete.')

@click.command('verify-superuser')
@with_appcontext
def verify_superuser_command():
    """Checks the superuser table and lists authorized emails."""
    try:
        from models import Superuser
        superusers = Superuser.query.all()
        if not superusers:
            click.echo("SUCCESS: The 'superuser' table exists, but it is empty.")
        else:
            click.echo("SUCCESS: The 'superuser' table exists and contains the following emails:")
            for su in superusers:
                click.echo(f"- {su.email}")
    except ImportError:
        click.echo("ERROR: Could not import the Superuser model. This should not happen.")
    except Exception as e:
        if "no such table" in str(e) or "does not exist" in str(e):
             click.echo("ERROR: The 'superuser' table does not exist in the database.")
             click.echo("Please run 'flask db upgrade' to create it.")
        else:
            click.echo(f"An unexpected error occurred: {e}")

@click.command('sync-superusers')
@with_appcontext
def sync_superusers_command():
    """Syncs superuser emails from environment variable to the database."""
    _sync_superusers()

@click.command('export-local-db')
@click.option('--output', default='local_db_export.sql', help='Output SQL filename')
@click.option('--upload-to-gcs', is_flag=True, help='Upload to Google Cloud Storage after export')
@click.option('--bucket', default='ticket-home-db-exports', help='GCS bucket name for upload')
@with_appcontext
def export_local_db_command(output, upload_to_gcs, bucket):
    """Exports the local PostgreSQL database to a SQL file and optionally uploads to GCS."""
    import subprocess

    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        click.echo("ERROR: DATABASE_URL environment variable not set")
        return

    # Parse database URL to extract connection parameters
    # Format: postgresql://user:password@host:port/dbname
    try:
        from urllib.parse import urlparse
        parsed = urlparse(database_url)

        db_user = parsed.username
        db_password = parsed.password
        db_host = parsed.hostname
        db_port = parsed.port or 5432
        db_name = parsed.path.lstrip('/')

        click.echo(f"Exporting database: {db_name} from {db_host}...")

        # Set PGPASSWORD environment variable for pg_dump
        env = os.environ.copy()
        if db_password:
            env['PGPASSWORD'] = db_password

        # Build pg_dump command
        pg_dump_cmd = [
            'pg_dump',
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-d', db_name,
            '--clean',  # Include DROP statements
            '--if-exists',  # Use IF EXISTS in DROP statements
            '--no-owner',  # Don't output ownership commands
            '--no-acl',  # Don't output ACL (grant/revoke) commands
            '-f', output
        ]

        # Execute pg_dump
        result = subprocess.run(pg_dump_cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            click.echo(f"ERROR during pg_dump: {result.stderr}")
            return

        click.echo(f"✓ Database exported successfully to: {output}")

        # Get file size
        import os as os_module
        file_size = os_module.path.getsize(output)
        click.echo(f"  File size: {file_size / 1024:.2f} KB")

        # Upload to GCS if requested
        if upload_to_gcs:
            click.echo(f"\nUploading to GCS bucket: gs://{bucket}/...")

            gsutil_cmd = [
                'gsutil',
                'cp',
                output,
                f'gs://{bucket}/{output}'
            ]

            result = subprocess.run(gsutil_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                click.echo(f"ERROR during gsutil upload: {result.stderr}")
                click.echo("\nYou can upload manually with:")
                click.echo(f"  gsutil cp {output} gs://{bucket}/{output}")
                return

            click.echo(f"✓ File uploaded to: gs://{bucket}/{output}")
            click.echo("\n=== Next Steps ===")
            click.echo("Use this file in deployment by setting environment variable:")
            click.echo(f"  IMPORT_SQL_FROM_GCS=gs://{bucket}/{output}")
            click.echo("\nSee script: 4-deploy-con-reset-desde-db-local-v3.txt")
        else:
            click.echo("\n=== Next Steps ===")
            click.echo("To upload to GCS manually:")
            click.echo(f"  gsutil cp {output} gs://{bucket}/{output}")
            click.echo("\nOr re-run with --upload-to-gcs flag:")
            click.echo(f"  flask export-local-db --upload-to-gcs --bucket {bucket}")

    except Exception as e:
        click.echo(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

@click.command('init-db-qa-minimal')
@with_appcontext
def init_db_qa_minimal_command():
    """Initialize database with minimal QA data: only clinics and superusers."""
    click.echo('Applying database migrations...')
    alembic_upgrade()

    click.echo('Creating clinics...')
    # Check if clinics already exist
    if Clinic.query.first():
        click.echo('Clinics already exist. Skipping clinic creation.')
    else:
        clinic_names = [
            "Clínica RedSalud Iquique", "Clínica RedSalud Elqui", "Clínica RedSalud Valparaíso",
            "Clínica RedSalud Providencia", "Clínica RedSalud Santiago", "Clínica RedSalud Vitacura",
            "Clínica RedSalud Rancagua", "Clínica RedSalud Mayor Temuco", "Clínica RedSalud Magallanes"
        ]
        clinics_to_add = [Clinic(name=name) for name in clinic_names]
        db.session.add_all(clinics_to_add)
        db.session.commit()
        click.echo(f'{len(clinics_to_add)} clinics created.')

    click.echo('Syncing superusers from SUPERUSER_EMAILS...')
    _sync_superusers()

    # Create essential system data for each clinic
    click.echo('Creating essential system data (DischargeTimeSlots)...')
    click.echo('Essential system data created successfully.')

    click.echo('QA minimal database initialization complete.')
    click.echo('Database contains:')
    click.echo(f'  - {Clinic.query.count()} clinics')
    click.echo(f'  - {Superuser.query.count()} superusers')
    click.echo('  - No other data (users, specialties, surgeries, standardized reasons, etc. must be created manually)')

@click.command('reset-db-qa-minimal')
@with_appcontext
def reset_db_qa_minimal_command():
    """Resets the database and initializes with minimal QA data."""
    with db.engine.connect() as con:
        with con.begin():
            click.echo('Dropping schema public CASCADE...')
            con.execute(text('DROP SCHEMA public CASCADE;'))
            click.echo('Recreating schema public...')
            con.execute(text('CREATE SCHEMA public;'))

    click.echo('Applying database migrations...')
    alembic_upgrade()

    click.echo('Syncing superusers from SUPERUSER_EMAILS...')
    _sync_superusers()

    click.echo('Creating clinics...')
    clinic_names = [
        "Clínica RedSalud Iquique", "Clínica RedSalud Elqui", "Clínica RedSalud Valparaíso",
        "Clínica RedSalud Providencia", "Clínica RedSalud Santiago", "Clínica RedSalud Vitacura",
        "Clínica RedSalud Rancagua", "Clínica RedSalud Mayor Temuco", "Clínica RedSalud Magallanes"
    ]
    clinics_to_add = [Clinic(name=name) for name in clinic_names]
    db.session.add_all(clinics_to_add)
    db.session.commit()
    click.echo(f'{len(clinics_to_add)} clinics created.')

    click.echo('Essential system data created successfully.')

    click.echo('Database has been reset with minimal QA data.')
    click.echo('Database contains:')
    click.echo(f'  - {Clinic.query.count()} clinics')
    click.echo(f'  - {Superuser.query.count()} superusers')
    click.echo('  - No other data (users, specialties, surgeries, standardized reasons, etc. must be created manually)')

@click.command('reset-db-local-minimal')
@with_appcontext
def reset_db_local_minimal_command():
    """Resets the database and initializes with minimal LOCAL data (clinics, superusers, and demo users)."""
    with db.engine.connect() as con:
        with con.begin():
            click.echo('Dropping schema public CASCADE...')
            con.execute(text('DROP SCHEMA public CASCADE;'))
            click.echo('Recreating schema public...')
            con.execute(text('CREATE SCHEMA public;'))

    click.echo('Applying database migrations...')
    alembic_upgrade()

    click.echo('Syncing superusers from SUPERUSER_EMAILS...')
    _sync_superusers()

    click.echo('Creating clinics...')
    clinic_names = [
        "Clínica RedSalud Iquique", "Clínica RedSalud Elqui", "Clínica RedSalud Valparaíso",
        "Clínica RedSalud Providencia", "Clínica RedSalud Santiago", "Clínica RedSalud Vitacura",
        "Clínica RedSalud Rancagua", "Clínica RedSalud Mayor Temuco", "Clínica RedSalud Magallanes"
    ]
    clinics_to_add = [Clinic(name=name) for name in clinic_names]
    db.session.add_all(clinics_to_add)
    db.session.commit()
    click.echo(f'{len(clinics_to_add)} clinics created.')

    # Get all clinics for user creation
    all_clinics = Clinic.query.all()

    # Create global admin user (superuser without clinic assignment)
    click.echo('Creating global admin user...')
    global_admin_username = 'global_admin'
    global_admin_email = 'global_admin@tickethome.com'
    
    global_admin = User(
        username=global_admin_username,
        email=global_admin_email,
        role=ROLE_ADMIN,
        password='password123',
        clinic_id=None  # No clinic assignment - can access all clinics
    )
    db.session.add(global_admin)
    
    # Add global_admin to Superuser table if not exists
    if not Superuser.query.filter_by(email=global_admin_email).first():
        superuser_entry = Superuser(email=global_admin_email)
        db.session.add(superuser_entry)
    
    db.session.commit()
    click.echo(f'Global admin user created: {global_admin_username}')

    click.echo('Creating demo users for each clinic...')
    users_created = 0
    for clinic in all_clinics:
        prefix = generate_prefix(clinic.name)
        
        # Create users for each role
        for role in [ROLE_ADMIN, ROLE_CLINICAL, ROLE_VISUALIZADOR]:
            username = f'{role}_{prefix}'
            user = User(
                username=username,
                email=f'{username}@tickethome.com',
                role=role,
                password='password123',
                clinic_id=clinic.id
            )
            db.session.add(user)
            users_created += 1
    
    db.session.commit()
    click.echo(f'{users_created} demo users created.')

    click.echo('\n' + '='*60)
    click.echo('Database has been reset with LOCAL MINIMAL data.')
    click.echo('='*60)
    click.echo('\nDatabase contains:')
    click.echo(f'  ✓ {Clinic.query.count()} clinics')
    click.echo(f'  ✓ {Superuser.query.count()} superusers')
    click.echo(f'  ✓ {User.query.count()} demo users')
    click.echo('\n  Demo user credentials (password: password123):')
    click.echo('  ─────────────────────────────────────────────')
    click.echo('  Global Admin (all clinics):')
    click.echo('    • global_admin')
    click.echo('')
    for clinic in all_clinics[:3]:  # Show first 3 clinics as examples
        prefix = generate_prefix(clinic.name)
        click.echo(f'  {clinic.name}:')
        click.echo(f'    • admin_{prefix}')
        click.echo(f'    • clinical_{prefix}')
        click.echo(f'    • visualizador_{prefix}')
    if len(all_clinics) > 3:
        click.echo(f'  ... y {len(all_clinics) - 3} clínicas más')
    click.echo('\n  ⚠ No other data created (specialties, surgeries, patients, tickets)')
    click.echo('='*60)

def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(reset_db_command)
    app.cli.add_command(update_users_command)
    app.cli.add_command(db_nuke_command)
    app.cli.add_command(run_upgrade_command)
    app.cli.add_command(verify_superuser_command)
    app.cli.add_command(sync_superusers_command)
    app.cli.add_command(export_local_db_command)
    app.cli.add_command(init_db_qa_minimal_command)
    app.cli.add_command(reset_db_qa_minimal_command)
    app.cli.add_command(reset_db_local_minimal_command)
