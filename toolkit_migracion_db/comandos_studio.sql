/* 
  ============================================================================
  COMANDOS PARA CLOUD SQL STUDIO (PROD)
  ============================================================================
  Usa estos comandos si la importacion falla por conflictos de tablas
  o si necesitas resetear permisos tras un DROP SCHEMA.
  ============================================================================
*/

-- 1. LIMPIEZA TOTAL (Opcional, usar solo si hay errores de esquema previos)
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;

-- 2. RESTAURACION DE PERMISOS (Ejecutar SIEMPRE despues de una importacion exitosa)
-- Reemplaza "tickethome-app" si el usuario cambia en el futuro.

-- Dar permiso sobre el esquema
GRANT ALL ON SCHEMA public TO "tickethome-app";
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- Asegurar que el dueño sea postgres
ALTER SCHEMA public OWNER TO postgres;

-- Dar permisos sobre tablas y secuencias creadas por el dump
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "tickethome-app";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "tickethome-app";

-- Configurar permisos para tablas que se creen en el futuro
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "tickethome-app";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "tickethome-app";

-- 3. VERIFICACION DE CONEXIONES (Si no puedes borrar la BD)
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'tickethome'
  AND pid <> pg_backend_pid();
