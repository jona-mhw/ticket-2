-- ============================================================================
-- Script: 01_cleanup_keep_essentials.sql
-- Descripción: Elimina todos los datos excepto clínicas, rangos horarios y superusuarios
-- Fecha: 2025-11-10
-- Autor: Claude Code
-- ============================================================================

-- IMPORTANTE: Este script elimina TODOS los datos de demo/producción
-- manteniendo solo la estructura base (clínicas, rangos horarios, superusuarios)

BEGIN;

-- 1. Eliminar tickets y datos relacionados (en orden por dependencias)
DELETE FROM public.fpa_modification WHERE TRUE;
DELETE FROM public.ticket WHERE TRUE;
DELETE FROM public.patient WHERE TRUE;

-- 2. Eliminar datos maestros
DELETE FROM public.standardized_reason WHERE TRUE;
DELETE FROM public.doctor WHERE TRUE;
DELETE FROM public.surgery WHERE TRUE;
DELETE FROM public.specialty WHERE TRUE;

-- 3. Eliminar usuarios (excepto los que se crearán automáticamente desde superuser)
DELETE FROM public.user WHERE TRUE;

-- 4. Eliminar auditoría
DELETE FROM public.action_audit WHERE TRUE;
DELETE FROM public.login_audit WHERE TRUE;

-- ============================================================================
-- DATOS QUE SE MANTIENEN:
-- ============================================================================
-- ✓ public.clinic (9 clínicas RedSalud)
-- ✓ public.discharge_time_slot (rangos horarios de 2 horas para cada clínica)
-- ✓ public.superuser (emails autorizados para acceso IAP)
-- ✓ public.alembic_version (control de migraciones)

COMMIT;

-- ============================================================================
-- Verificación de datos restantes
-- ============================================================================

SELECT 'Clínicas:' as tipo, COUNT(*) as total FROM public.clinic
UNION ALL
SELECT 'Rangos horarios:', COUNT(*) FROM public.discharge_time_slot
UNION ALL
SELECT 'Superusuarios:', COUNT(*) FROM public.superuser
UNION ALL
SELECT 'Usuarios:', COUNT(*) FROM public.user
UNION ALL
SELECT 'Pacientes:', COUNT(*) FROM public.patient
UNION ALL
SELECT 'Tickets:', COUNT(*) FROM public.ticket
UNION ALL
SELECT 'Especialidades:', COUNT(*) FROM public.specialty
UNION ALL
SELECT 'Cirugías:', COUNT(*) FROM public.surgery;

-- ============================================================================
-- Resultado esperado:
-- ============================================================================
-- Clínicas: 9
-- Rangos horarios: 108 (9 clínicas × 12 rangos de 2 horas)
-- Superusuarios: 2
-- Usuarios: 0
-- Pacientes: 0
-- Tickets: 0
-- Especialidades: 0
-- Cirugías: 0
-- ============================================================================
