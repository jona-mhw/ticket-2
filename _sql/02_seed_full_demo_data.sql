-- ============================================================================
-- Script: 02_seed_full_demo_data.sql
-- Descripción: Agrega datos de demostración completos (usuarios, especialidades,
--              cirugías, doctores, pacientes, tickets)
-- Fecha: 2025-11-10
-- Autor: Claude Code
-- ============================================================================

-- IMPORTANTE: Este script agrega datos de DEMO/PRUEBA
-- Ejecutar después de 01_cleanup_keep_essentials.sql

BEGIN;

-- ============================================================================
-- 1. CREAR USUARIOS POR CLÍNICA
-- ============================================================================

-- Usuario global admin (superusuario sin clínica)
INSERT INTO public.user (username, email, role, password, clinic_id, is_active) VALUES
('global_admin', 'global_admin@tickethome.com', 'admin', 'scrypt:32768:8:1$MHiZQE7ldJl5Nm9e$c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8', NULL, true)
ON CONFLICT (email) DO NOTHING;

-- Usuarios para cada clínica (admin, clinical, visualizador)
DO $$
DECLARE
    clinic_record RECORD;
    clinic_prefix VARCHAR(10);
BEGIN
    FOR clinic_record IN SELECT id, name FROM public.clinic ORDER BY id
    LOOP
        -- Generar prefijo de clínica (primeras letras)
        IF clinic_record.name LIKE '%Iquique%' THEN clinic_prefix := 'IQQ';
        ELSIF clinic_record.name LIKE '%Elqui%' THEN clinic_prefix := 'ELQ';
        ELSIF clinic_record.name LIKE '%Valparaíso%' THEN clinic_prefix := 'VAL';
        ELSIF clinic_record.name LIKE '%Providencia%' THEN clinic_prefix := 'PRO';
        ELSIF clinic_record.name LIKE '%Santiago%' THEN clinic_prefix := 'STG';
        ELSIF clinic_record.name LIKE '%Vitacura%' THEN clinic_prefix := 'VIT';
        ELSIF clinic_record.name LIKE '%Rancagua%' THEN clinic_prefix := 'RAN';
        ELSIF clinic_record.name LIKE '%Temuco%' THEN clinic_prefix := 'TEM';
        ELSIF clinic_record.name LIKE '%Magallanes%' THEN clinic_prefix := 'MAG';
        ELSE clinic_prefix := 'UNK';
        END IF;

        -- Admin
        INSERT INTO public.user (username, email, role, password, clinic_id, is_active) VALUES
        ('admin_' || clinic_prefix, 'admin_' || clinic_prefix || '@tickethome.com', 'admin', 'scrypt:32768:8:1$MHiZQE7ldJl5Nm9e$c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8', clinic_record.id, true)
        ON CONFLICT (email) DO NOTHING;

        -- Clinical
        INSERT INTO public.user (username, email, role, password, clinic_id, is_active) VALUES
        ('clinical_' || clinic_prefix, 'clinical_' || clinic_prefix || '@tickethome.com', 'clinical', 'scrypt:32768:8:1$MHiZQE7ldJl5Nm9e$c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8', clinic_record.id, true)
        ON CONFLICT (email) DO NOTHING;

        -- Visualizador
        INSERT INTO public.user (username, email, role, password, clinic_id, is_active) VALUES
        ('visualizador_' || clinic_prefix, 'visualizador_' || clinic_prefix || '@tickethome.com', 'visualizador', 'scrypt:32768:8:1$MHiZQE7ldJl5Nm9e$c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8e5c8a3d8f8a0d3c5a3e5f8', clinic_record.id, true)
        ON CONFLICT (email) DO NOTHING;
    END LOOP;
END $$;

-- ============================================================================
-- 2. ESPECIALIDADES
-- ============================================================================

DO $$
DECLARE
    clinic_record RECORD;
    clinic_prefix VARCHAR(10);
BEGIN
    FOR clinic_record IN SELECT id, name FROM public.clinic ORDER BY id
    LOOP
        -- Generar prefijo
        IF clinic_record.name LIKE '%Iquique%' THEN clinic_prefix := 'IQQ';
        ELSIF clinic_record.name LIKE '%Elqui%' THEN clinic_prefix := 'ELQ';
        ELSIF clinic_record.name LIKE '%Valparaíso%' THEN clinic_prefix := 'VAL';
        ELSIF clinic_record.name LIKE '%Providencia%' THEN clinic_prefix := 'PRO';
        ELSIF clinic_record.name LIKE '%Santiago%' THEN clinic_prefix := 'STG';
        ELSIF clinic_record.name LIKE '%Vitacura%' THEN clinic_prefix := 'VIT';
        ELSIF clinic_record.name LIKE '%Rancagua%' THEN clinic_prefix := 'RAN';
        ELSIF clinic_record.name LIKE '%Temuco%' THEN clinic_prefix := 'TEM';
        ELSIF clinic_record.name LIKE '%Magallanes%' THEN clinic_prefix := 'MAG';
        ELSE clinic_prefix := 'UNK';
        END IF;

        INSERT INTO public.specialty (name, clinic_id) VALUES
        ('Cirugía General (' || clinic_prefix || ')', clinic_record.id),
        ('Ginecología (' || clinic_prefix || ')', clinic_record.id),
        ('Traumatología (' || clinic_prefix || ')', clinic_record.id),
        ('Cirugía Pediátrica (' || clinic_prefix || ')', clinic_record.id);
    END LOOP;
END $$;

-- ============================================================================
-- 3. CIRUGÍAS
-- ============================================================================

DO $$
DECLARE
    clinic_record RECORD;
    clinic_prefix VARCHAR(10);
    specialty_cg_id INTEGER;
    specialty_gin_id INTEGER;
    specialty_trauma_id INTEGER;
BEGIN
    FOR clinic_record IN SELECT id, name FROM public.clinic ORDER BY id
    LOOP
        -- Generar prefijo
        IF clinic_record.name LIKE '%Iquique%' THEN clinic_prefix := 'IQQ';
        ELSIF clinic_record.name LIKE '%Elqui%' THEN clinic_prefix := 'ELQ';
        ELSIF clinic_record.name LIKE '%Valparaíso%' THEN clinic_prefix := 'VAL';
        ELSIF clinic_record.name LIKE '%Providencia%' THEN clinic_prefix := 'PRO';
        ELSIF clinic_record.name LIKE '%Santiago%' THEN clinic_prefix := 'STG';
        ELSIF clinic_record.name LIKE '%Vitacura%' THEN clinic_prefix := 'VIT';
        ELSIF clinic_record.name LIKE '%Rancagua%' THEN clinic_prefix := 'RAN';
        ELSIF clinic_record.name LIKE '%Temuco%' THEN clinic_prefix := 'TEM';
        ELSIF clinic_record.name LIKE '%Magallanes%' THEN clinic_prefix := 'MAG';
        ELSE clinic_prefix := 'UNK';
        END IF;

        -- Obtener IDs de especialidades
        SELECT id INTO specialty_cg_id FROM public.specialty WHERE name = 'Cirugía General (' || clinic_prefix || ')' AND clinic_id = clinic_record.id;
        SELECT id INTO specialty_gin_id FROM public.specialty WHERE name = 'Ginecología (' || clinic_prefix || ')' AND clinic_id = clinic_record.id;
        SELECT id INTO specialty_trauma_id FROM public.specialty WHERE name = 'Traumatología (' || clinic_prefix || ')' AND clinic_id = clinic_record.id;

        -- Cirugías
        INSERT INTO public.surgery (name, specialty_id, base_stay_hours, is_ambulatory, ambulatory_cutoff_hour, clinic_id) VALUES
        ('Apendicectomía Laparoscópica (' || clinic_prefix || ')', specialty_cg_id, 24, false, NULL, clinic_record.id),
        ('Colecistectomía Laparoscópica (' || clinic_prefix || ')', specialty_cg_id, 48, true, 14, clinic_record.id),
        ('Histerectomía Abdominal (' || clinic_prefix || ')', specialty_gin_id, 72, false, NULL, clinic_record.id),
        ('Artroscopia de Rodilla (' || clinic_prefix || ')', specialty_trauma_id, 8, true, 16, clinic_record.id);
    END LOOP;
END $$;

-- ============================================================================
-- 4. DOCTORES
-- ============================================================================

DO $$
DECLARE
    clinic_record RECORD;
    clinic_prefix VARCHAR(10);
BEGIN
    FOR clinic_record IN SELECT id, name FROM public.clinic ORDER BY id
    LOOP
        -- Generar prefijo
        IF clinic_record.name LIKE '%Iquique%' THEN clinic_prefix := 'IQQ';
        ELSIF clinic_record.name LIKE '%Elqui%' THEN clinic_prefix := 'ELQ';
        ELSIF clinic_record.name LIKE '%Valparaíso%' THEN clinic_prefix := 'VAL';
        ELSIF clinic_record.name LIKE '%Providencia%' THEN clinic_prefix := 'PRO';
        ELSIF clinic_record.name LIKE '%Santiago%' THEN clinic_prefix := 'STG';
        ELSIF clinic_record.name LIKE '%Vitacura%' THEN clinic_prefix := 'VIT';
        ELSIF clinic_record.name LIKE '%Rancagua%' THEN clinic_prefix := 'RAN';
        ELSIF clinic_record.name LIKE '%Temuco%' THEN clinic_prefix := 'TEM';
        ELSIF clinic_record.name LIKE '%Magallanes%' THEN clinic_prefix := 'MAG';
        ELSE clinic_prefix := 'UNK';
        END IF;

        INSERT INTO public.doctor (name, specialty, rut, clinic_id) VALUES
        ('Dr. Carlos Mendoza (' || clinic_prefix || ')', 'Cirugía General', '12345-' || clinic_prefix, clinic_record.id),
        ('Dra. Ana María Pérez (' || clinic_prefix || ')', 'Ginecología', '54321-' || clinic_prefix, clinic_record.id);
    END LOOP;
END $$;

-- ============================================================================
-- 5. RAZONES ESTANDARIZADAS
-- ============================================================================

DO $$
DECLARE
    clinic_record RECORD;
BEGIN
    FOR clinic_record IN SELECT id FROM public.clinic ORDER BY id
    LOOP
        -- Razones de Discrepancia Inicial
        INSERT INTO public.standardized_reason (reason, category, clinic_id) VALUES
        ('Criterio médico especializado requiere mayor tiempo de observación', 'initial', clinic_record.id),
        ('Complejidad del procedimiento requiere hospitalización extendida', 'initial', clinic_record.id),
        ('Comorbilidades del paciente requieren cuidado prolongado', 'initial', clinic_record.id),
        ('Protocolo clínico específico de la especialidad', 'initial', clinic_record.id),
        ('Evaluación pre-alta requiere tiempo adicional', 'initial', clinic_record.id);

        -- Razones de Modificación
        INSERT INTO public.standardized_reason (reason, category, clinic_id) VALUES
        ('Complicación post-operatoria', 'modification', clinic_record.id),
        ('Condición del paciente requiere más observación', 'modification', clinic_record.id),
        ('Interconsulta médica pendiente', 'modification', clinic_record.id),
        ('Espera de resultados de exámenes', 'modification', clinic_record.id),
        ('Necesidad de cuidados intensivos adicionales', 'modification', clinic_record.id),
        ('Ajuste por indicación médica especializada', 'modification', clinic_record.id),
        ('Control de dolor inadecuado', 'modification', clinic_record.id);

        -- Razones de Anulación
        INSERT INTO public.standardized_reason (reason, category, clinic_id) VALUES
        ('Error en el ingreso de datos', 'annulment', clinic_record.id),
        ('Paciente dado de alta antes de lo previsto', 'annulment', clinic_record.id),
        ('Traslado a otra institución', 'annulment', clinic_record.id),
        ('Cancelación de procedimiento', 'annulment', clinic_record.id);
    END LOOP;
END $$;

-- ============================================================================
-- 6. PACIENTES (5 por clínica)
-- ============================================================================

DO $$
DECLARE
    clinic_record RECORD;
    i INTEGER;
    rut_counter INTEGER := 1;
    nombres_masculinos TEXT[] := ARRAY[
        'Pedro Antonio', 'José Luis', 'Ricardo Andrés', 'Héctor Manuel', 'Sergio Patricio'
    ];
    apellidos TEXT[] := ARRAY[
        'Martínez Flores', 'Silva Contreras', 'Vargas Muñoz', 'Rojas Campos', 'Torres Soto'
    ];
BEGIN
    FOR clinic_record IN SELECT id FROM public.clinic ORDER BY id
    LOOP
        FOR i IN 1..5 LOOP
            INSERT INTO public.patient (rut, primer_nombre, apellido_paterno, age, sex, clinic_id) VALUES
            (LPAD(rut_counter::TEXT, 8, '0') || '-K',
             SPLIT_PART(nombres_masculinos[((rut_counter - 1) % 5) + 1], ' ', 1),
             SPLIT_PART(apellidos[((rut_counter - 1) % 5) + 1], ' ', 1),
             20 + ((rut_counter * 7) % 60),
             CASE WHEN rut_counter % 2 = 0 THEN 'Male' ELSE 'Female' END,
             clinic_record.id);

            rut_counter := rut_counter + 1;
        END LOOP;
    END LOOP;
END $$;

-- ============================================================================
-- 7. TICKETS (15 por clínica)
-- ============================================================================

DO $$
DECLARE
    clinic_record RECORD;
    clinic_prefix VARCHAR(10);
    i INTEGER;
    patient_ids INTEGER[];
    surgery_ids INTEGER[];
    doctor_ids INTEGER[];
    slot_ids INTEGER[];
    selected_patient_id INTEGER;
    selected_surgery_id INTEGER;
    selected_doctor_id INTEGER;
    selected_slot_id INTEGER;
    surgery_base_hours INTEGER;
    pavilion_end TIMESTAMP;
    calculated_fpa TIMESTAMP;
    medical_discharge DATE;
    overnight_stays INTEGER;
    ticket_id VARCHAR(50);
    surgery_name VARCHAR(255);
BEGIN
    FOR clinic_record IN SELECT id, name FROM public.clinic ORDER BY id
    LOOP
        -- Generar prefijo
        IF clinic_record.name LIKE '%Iquique%' THEN clinic_prefix := 'IQQ';
        ELSIF clinic_record.name LIKE '%Elqui%' THEN clinic_prefix := 'ELQ';
        ELSIF clinic_record.name LIKE '%Valparaíso%' THEN clinic_prefix := 'VAL';
        ELSIF clinic_record.name LIKE '%Providencia%' THEN clinic_prefix := 'PRO';
        ELSIF clinic_record.name LIKE '%Santiago%' THEN clinic_prefix := 'STG';
        ELSIF clinic_record.name LIKE '%Vitacura%' THEN clinic_prefix := 'VIT';
        ELSIF clinic_record.name LIKE '%Rancagua%' THEN clinic_prefix := 'RAN';
        ELSIF clinic_record.name LIKE '%Temuco%' THEN clinic_prefix := 'TEM';
        ELSIF clinic_record.name LIKE '%Magallanes%' THEN clinic_prefix := 'MAG';
        ELSE clinic_prefix := 'UNK';
        END IF;

        -- Obtener arrays de IDs
        SELECT ARRAY_AGG(id) INTO patient_ids FROM public.patient WHERE clinic_id = clinic_record.id;
        SELECT ARRAY_AGG(id) INTO surgery_ids FROM public.surgery WHERE clinic_id = clinic_record.id;
        SELECT ARRAY_AGG(id) INTO doctor_ids FROM public.doctor WHERE clinic_id = clinic_record.id;
        SELECT ARRAY_AGG(id) INTO slot_ids FROM public.discharge_time_slot WHERE clinic_id = clinic_record.id;

        -- Crear 15 tickets
        FOR i IN 1..15 LOOP
            -- Seleccionar aleatoriamente
            selected_patient_id := patient_ids[1 + ((i - 1) % ARRAY_LENGTH(patient_ids, 1))];
            selected_surgery_id := surgery_ids[1 + ((i - 1) % ARRAY_LENGTH(surgery_ids, 1))];
            selected_doctor_id := doctor_ids[1 + ((i - 1) % ARRAY_LENGTH(doctor_ids, 1))];
            selected_slot_id := slot_ids[1 + ((i - 1) % ARRAY_LENGTH(slot_ids, 1))];

            -- Obtener base_stay_hours y nombre de cirugía
            SELECT base_stay_hours, name INTO surgery_base_hours, surgery_name
            FROM public.surgery WHERE id = selected_surgery_id;

            -- Calcular pavilion_end_time (últimos 30 días)
            pavilion_end := NOW() - INTERVAL '1 day' * ((i * 2) % 30) - INTERVAL '1 hour' * ((i * 3) % 23);

            -- Calcular FPA
            calculated_fpa := pavilion_end + INTERVAL '1 hour' * surgery_base_hours;

            -- Calcular overnight stays
            overnight_stays := EXTRACT(EPOCH FROM (calculated_fpa - pavilion_end)) / 86400;

            -- Calcular medical_discharge_date
            medical_discharge := (pavilion_end + INTERVAL '1 day' * (1 + (i % 4)))::DATE;

            -- Generar ticket ID
            ticket_id := 'TH-' || clinic_prefix || '-' || EXTRACT(YEAR FROM NOW())::TEXT || '-' || LPAD(i::TEXT, 3, '0');

            -- Insertar ticket
            INSERT INTO public.ticket (
                id, patient_id, surgery_id, doctor_id,
                pavilion_end_time, medical_discharge_date,
                system_calculated_fpa, initial_fpa, current_fpa,
                overnight_stays, discharge_slot_id,
                surgery_name_snapshot, surgery_base_hours_snapshot,
                created_by, clinic_id, status
            ) VALUES (
                ticket_id, selected_patient_id, selected_surgery_id, selected_doctor_id,
                pavilion_end, medical_discharge,
                calculated_fpa, calculated_fpa, calculated_fpa,
                overnight_stays, selected_slot_id,
                surgery_name, surgery_base_hours,
                'admin_' || clinic_prefix, clinic_record.id, 'vigente'
            );
        END LOOP;
    END LOOP;
END $$;

COMMIT;

-- ============================================================================
-- Verificación de datos creados
-- ============================================================================

SELECT 'Usuarios:' as tipo, COUNT(*) as total FROM public.user
UNION ALL
SELECT 'Especialidades:', COUNT(*) FROM public.specialty
UNION ALL
SELECT 'Cirugías:', COUNT(*) FROM public.surgery
UNION ALL
SELECT 'Doctores:', COUNT(*) FROM public.doctor
UNION ALL
SELECT 'Razones estandarizadas:', COUNT(*) FROM public.standardized_reason
UNION ALL
SELECT 'Pacientes:', COUNT(*) FROM public.patient
UNION ALL
SELECT 'Tickets:', COUNT(*) FROM public.ticket;

-- ============================================================================
-- Resultado esperado:
-- ============================================================================
-- Usuarios: 28 (1 global_admin + 9 clínicas × 3 roles)
-- Especialidades: 36 (9 clínicas × 4 especialidades)
-- Cirugías: 36 (9 clínicas × 4 cirugías)
-- Doctores: 18 (9 clínicas × 2 doctores)
-- Razones estandarizadas: 144 (9 clínicas × 16 razones)
-- Pacientes: 45 (9 clínicas × 5 pacientes)
-- Tickets: 135 (9 clínicas × 15 tickets)
-- ============================================================================

-- NOTA: Todos los usuarios tienen contraseña: "password123" (hash scrypt)
