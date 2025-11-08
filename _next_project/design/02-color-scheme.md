# 2. Paleta de Colores

Una paleta de colores consistente es fundamental para la identidad visual de la aplicación. La siguiente paleta está basada en una estética profesional y moderna, utilizando tonos neutros para la base y colores de acento para las acciones y estados.

## Colores Principales

-   **Fondo (`Background`)**:
    -   Principal: `#f8fafc` (Un gris muy claro, casi blanco)
    -   Secundario / Tarjetas: `white` (`#ffffff`)
-   **Texto (`Text`)**:
    -   Principal: `#374151` (Gris oscuro)
    -   Secundario: `#6b7280` (Gris medio)
    -   Tenue: `#9ca3af` (Gris claro)
-   **Bordes (`Borders`)**:
    -   `#e5e7eb` (Gris claro para divisiones sutiles)

## Colores de Acento y Estado

Estos colores se utilizan para llamar la atención sobre elementos interactivos y para comunicar estados.

-   **Primario / Acento (`Primary`)**:
    -   `#3b82f6` (Azul) - Usado para botones principales, enlaces y elementos activos.
-   **Éxito (`Success`)**:
    -   Fondo: `#dcfce7` (Verde muy claro)
    -   Texto: `#166534` (Verde oscuro)
    -   Usado para badges de estado "Vigente" y mensajes de éxito.
-   **Peligro / Error (`Danger`)**:
    -   Fondo: `#fecaca` (Rojo muy claro)
    -   Texto: `#991b1b` (Rojo oscuro)
    -   Usado para badges de estado "Anulado", errores y acciones destructivas.
-   **Advertencia (`Warning`)**:
    -   Fondo: `#fef3c7` (Amarillo muy claro)
    -   Texto: `#92400e` (Ámbar oscuro)
    -   Usado para estados de advertencia o timers que se acercan a su límite.
-   **Neutral / Informativo**:
    -   Fondo: `#e5e7eb` (Gris claro)
    -   Texto: `#4b5563` (Gris oscuro)
    -   Usado para badges de estado "Programado" o informativo.

## Ejemplo de Implementación en CSS

```css
/* Paleta de colores como variables CSS para fácil reutilización */
:root {
    --color-bg-primary: #f8fafc;
    --color-bg-card: #ffffff;
    --color-text-primary: #374151;
    --color-text-secondary: #6b7280;
    --color-border: #e5e7eb;

    --color-accent: #3b82f6;

    --color-success-bg: #dcfce7;
    --color-success-text: #166534;

    --color-danger-bg: #fecaca;
    --color-danger-text: #991b1b;

    --color-warning-bg: #fef3c7;
    --color-warning-text: #92400e;
}

body {
    background-color: var(--color-bg-primary);
    color: var(--color-text-primary);
}

.button-primary {
    background-color: var(--color-accent);
    color: white;
}

.status-badge-success {
    background-color: var(--color-success-bg);
    color: var(--color-success-text);
}
```

---

**Próximo paso:** [3. Assets Estáticos y CSS](./03-static-assets.md)
