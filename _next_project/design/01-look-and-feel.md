# 1. Look and Feel

La experiencia de usuario (UX) y la interfaz de usuario (UI) deben ser limpias, profesionales y funcionales. El objetivo es crear una aplicación intuitiva que requiera una mínima formación para el usuario.

## Principios de Diseño

-   **Claridad sobre todo**: La información más importante debe ser fácilmente accesible. Las acciones primarias deben ser obvias.
-   **Consistencia**: Los elementos de la interfaz (botones, formularios, tablas) deben verse y comportarse de la misma manera en toda la aplicación.
-   **Feedback al Usuario**: La aplicación debe proporcionar feedback inmediato para las acciones del usuario (ej. mensajes de éxito/error, indicadores de carga).
-   **Diseño Responsive**: La aplicación debe ser usable tanto en pantallas de escritorio como en dispositivos móviles, adaptando su layout según sea necesario.

## Estructura de la Página (`base.html`)

Se recomienda una estructura de página consistente utilizando la herencia de plantillas de Jinja2.

-   **Header**:
    -   Logo de la empresa a la izquierda.
    -   Menú de navegación principal.
    -   Información del usuario y botón de logout a la derecha.
-   **Main Content**:
    -   Un área principal donde se renderiza el contenido de cada página.
    -   Debe incluir un espacio para mostrar mensajes flash (alertas de éxito, error, etc.).
-   **Footer**:
    -   Información secundaria como el nombre de la aplicación, la versión y enlaces de ayuda.

## Componentes Clave de la UI

-   **Formularios**:
    -   Labels claros y concisos.
    -   Inputs con placeholders descriptivos.
    -   Validación tanto en el frontend (JavaScript) como en el backend.
    -   Botones de acción primarios (ej. "Guardar") y secundarios (ej. "Cancelar") claramente diferenciados.

-   **Tablas de Datos**:
    -   Cabeceras fijas (`sticky headers`) para que los títulos de las columnas siempre sean visibles al hacer scroll.
    -   Opciones para ordenar y filtrar los datos.
    -   Paginación para manejar grandes volúmenes de datos.
    -   Acciones por fila (editar, eliminar) agrupadas y accesibles.

-   **Badges y Alertas**:
    -   Uso de colores para indicar estados (ej. "Vigente" en verde, "Anulado" en rojo).
    -   Mensajes flash en la parte superior de la página para notificar al usuario sobre el resultado de sus acciones.

-   **Botones**:
    -   Botón primario con un color de acento fuerte.
    -   Botones secundarios con un estilo más sutil.
    -   Iconos en los botones para mejorar la comprensión.

---

**Próximo paso:** [2. Paleta de Colores](./02-color-scheme.md)
