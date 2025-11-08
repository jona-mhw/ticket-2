document.addEventListener('DOMContentLoaded', function () {
    // Initialize enhanced table features
    initializeEnhancedTicketsTable();

    // Format RUT input
    const rutInput = document.getElementById('rut');
    if (rutInput) {
        rutInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/[^0-9kK.-]/g, '');
            value = value.replace(/\./g, '').replace(/-/g, '');

            if (value.length > 1) {
                let body = value.slice(0, -1);
                let dv = value.slice(-1).toUpperCase();
                body = new Intl.NumberFormat('es-CL').format(body);
                e.target.value = `${body}-${dv}`;
            } else {
                e.target.value = value;
            }
        });
    }
});

// Enhanced Tickets Table Initialization
function initializeEnhancedTicketsTable() {
    const table = document.getElementById('tickets-table');
    if (!table) return;

    // Initialize collapsible column controls
    initializeCollapsibleColumnControls();

    // Initialize column visibility controls
    initializeColumnVisibilityControls();

    // Initialize enhanced sorting
    initializeEnhancedSorting();

    // Initialize countdown timers
    initializeCountdownTimers();

    // Initialize sticky columns
    initializeStickyColumns();

    // Initialize control buttons
    initializeControlButtons();
}

// Collapsible Column Controls
function initializeCollapsibleColumnControls() {
    const toggleBtn = document.getElementById('toggle-column-controls');
    const panel = document.getElementById('column-controls-panel');
    const chevronIcon = document.getElementById('chevron-icon');

    if (!toggleBtn || !panel || !chevronIcon) return;

    // Load saved state
    const savedState = localStorage.getItem('tickets_column_controls_collapsed');
    const isCollapsed = savedState === 'true';

    // Set initial state
    if (isCollapsed) {
        panel.classList.add('collapsed');
        chevronIcon.classList.add('rotated');
    } else {
        panel.classList.add('expanded');
    }

    // Toggle function
    function togglePanel() {
        const isCurrentlyCollapsed = panel.classList.contains('collapsed');

        if (isCurrentlyCollapsed) {
            // Expand
            panel.classList.remove('collapsed');
            panel.classList.add('expanded');
            chevronIcon.classList.add('rotated');
            localStorage.setItem('tickets_column_controls_collapsed', 'false');
        } else {
            // Collapse
            panel.classList.remove('expanded');
            panel.classList.add('collapsed');
            chevronIcon.classList.remove('rotated');
            localStorage.setItem('tickets_column_controls_collapsed', 'true');
        }
    }

    // Add event listener
    toggleBtn.addEventListener('click', togglePanel);
}

// Column Visibility Controls
function initializeColumnVisibilityControls() {
    const table = document.getElementById('tickets-table');
    const columnToggles = document.getElementById('column-toggles');

    if (!table || !columnToggles) return;

    const headers = table.querySelectorAll('thead th[data-column]');
    const columnData = [];

    // Extract column information
    headers.forEach((header, index) => {
        const columnName = header.dataset.column;
        const priority = parseInt(header.dataset.priority) || 999;

        columnData.push({
            name: columnName,
            displayName: getColumnDisplayName(columnName),
            index: index,
            priority: priority,
            visible: true
        });
    });

    // Sort by priority
    columnData.sort((a, b) => a.priority - b.priority);

    // Create toggle controls
    columnData.forEach(col => {
        const label = document.createElement('label');
        label.className = 'flex items-center px-3 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer transition-colors';
        label.title = `Mostrar/ocultar columna ${col.displayName}`;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'mr-2 text-primary focus:ring-primary';
        checkbox.checked = true;
        checkbox.dataset.columnIndex = col.index;
        checkbox.dataset.columnName = col.name;

        checkbox.addEventListener('change', function(e) {
            toggleColumnVisibility(col.index, e.target.checked);
        });

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(col.displayName));
        columnToggles.appendChild(label);
    });

    // Load saved visibility preferences
    loadColumnVisibilityPreferences();
}

// Enhanced Sorting
function initializeEnhancedSorting() {
    const table = document.getElementById('tickets-table');
    if (!table) return;

    const headers = table.querySelectorAll('thead th[data-column]');

    headers.forEach(header => {
        const columnName = header.dataset.column;
        if (!columnName || ['actions', 'status_countdown'].includes(columnName)) return;

        header.style.cursor = 'pointer';
        header.classList.add('sortable-header');

        // Add sort indicators
        const sortIndicator = header.querySelector('.sort-indicator');
        if (sortIndicator) {
            sortIndicator.style.cursor = 'pointer';
        }

        header.addEventListener('click', function() {
            handleSort(columnName);
        });
    });
}

// Countdown Timers
function initializeCountdownTimers() {
    const timers = document.querySelectorAll('.countdown-timer');

    function updateTimers() {
        timers.forEach(timer => {
            const fpaString = timer.dataset.fpa;
            if (!fpaString) return;

            const fpaDate = new Date(fpaString);
            const now = new Date();
            const timeDiff = fpaDate - now;

            if (timeDiff <= 0) {
                timer.textContent = 'VENCIDO';
                timer.className = 'countdown-display countdown-critical';
                return;
            }

            const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);

            let display = '';
            let cssClass = 'countdown-display ';

            if (days > 0) {
                display = `${days}d ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                cssClass += 'countdown-normal';
            } else if (hours > 6) {
                display = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                cssClass += 'countdown-normal';
            } else if (hours > 1) {
                display = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                cssClass += 'countdown-warning';
            } else {
                display = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                cssClass += 'countdown-critical';
            }

            timer.textContent = display;
            timer.className = cssClass;
        });
    }

    if (timers.length > 0) {
        updateTimers(); // Initial call
        setInterval(updateTimers, 1000); // Update every second for real-time countdown
    }
}

// Sticky Columns
function initializeStickyColumns() {
    const table = document.getElementById('tickets-table');
    if (!table) return;

    function adjustStickyColumns() {
        const stickyCols = table.querySelectorAll('.sticky-col');
        let currentOffset = 0;

        stickyCols.forEach(col => {
            if (col.style.display !== 'none') {
                col.style.left = `${currentOffset}px`;
                currentOffset += col.offsetWidth;
            }
        });
    }

    // Initial adjustment
    setTimeout(adjustStickyColumns, 100);

    // Re-adjust on window resize
    window.addEventListener('resize', adjustStickyColumns);

    // Re-adjust when columns are shown/hidden
    const observer = new MutationObserver(adjustStickyColumns);
    observer.observe(table, { attributes: true, subtree: true });
}

// Control Buttons
function initializeControlButtons() {
    const showAllBtn = document.getElementById('show-all-columns');
    const resetBtn = document.getElementById('reset-columns');

    if (showAllBtn) {
        showAllBtn.addEventListener('click', function() {
            showAllColumns();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            resetColumnVisibility();
        });
    }
}

// Helper Functions
function getColumnDisplayName(columnName) {
    const displayNames = {
        'actions': 'Acciones',
        'status_countdown': 'Estado / Tiempo',
        'fpa': 'FPA Actual',
        'ticket_id': 'ID Ticket',
        'rut': 'RUT Paciente',
        'first_name': 'Primer Nombre',
        'second_name': 'Segundo Nombre',
        'last_name_father': 'Apellido Paterno',
        'last_name_mother': 'Apellido Materno',
        'room': 'Cama',
        'medical_discharge': 'Alta Médica',
        'doctor': 'Médico Tratante',
        'surgery': 'Cirugía',
        'created_at': 'Fecha Creación'
    };

    return displayNames[columnName] || columnName;
}

function toggleColumnVisibility(columnIndex, visible) {
    const table = document.getElementById('tickets-table');
    if (!table) return;

    // Find all cells in this column (header and body)
    const selector = `th:nth-child(${columnIndex + 1}), td:nth-child(${columnIndex + 1})`;
    const cells = table.querySelectorAll(selector);

    cells.forEach(cell => {
        cell.style.display = visible ? '' : 'none';
    });

    // Save preference
    saveColumnVisibilityPreferences();

    // Re-adjust sticky columns after a brief delay
    setTimeout(() => {
        adjustStickyColumns();
    }, 100);
}

function showAllColumns() {
    const checkboxes = document.querySelectorAll('#column-toggles input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        if (!checkbox.checked) {
            checkbox.checked = true;
            toggleColumnVisibility(parseInt(checkbox.dataset.columnIndex), true);
        }
    });
}

function resetColumnVisibility() {
    // Reset to default visibility (hide less important columns)
    const defaultHiddenColumns = ['second_name', 'last_name_mother'];

    const checkboxes = document.querySelectorAll('#column-toggles input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        const columnName = checkbox.dataset.columnName;
        const shouldHide = defaultHiddenColumns.includes(columnName);

        if (shouldHide !== checkbox.checked) {
            checkbox.checked = !shouldHide;
            toggleColumnVisibility(parseInt(checkbox.dataset.columnIndex), !shouldHide);
        }
    });

    // Clear localStorage to reset preferences
    localStorage.removeItem('tickets_columns_visible');
}

function handleSort(columnName) {
    const currentUrl = new URL(window.location.href);
    const currentSort = currentUrl.searchParams.get('sort_by');
    const currentOrder = currentUrl.searchParams.get('sort_dir') || 'asc';

    let newOrder = 'asc';
    if (currentSort === columnName && currentOrder === 'asc') {
        newOrder = 'desc';
    }

    currentUrl.searchParams.set('sort_by', columnName);
    currentUrl.searchParams.set('sort_dir', newOrder);
    window.location.href = currentUrl.toString();
}

function saveColumnVisibilityPreferences() {
    const checkboxes = document.querySelectorAll('#column-toggles input[type="checkbox"]');
    const visibility = {};

    checkboxes.forEach(checkbox => {
        const columnIndex = parseInt(checkbox.dataset.columnIndex);
        visibility[columnIndex] = checkbox.checked;
    });

    localStorage.setItem('tickets_columns_visible', JSON.stringify(visibility));
}

function loadColumnVisibilityPreferences() {
    const saved = localStorage.getItem('tickets_columns_visible');
    if (!saved) return;

    try {
        const visibility = JSON.parse(saved);
        const checkboxes = document.querySelectorAll('#column-toggles input[type="checkbox"]');

        checkboxes.forEach(checkbox => {
            const columnIndex = parseInt(checkbox.dataset.columnIndex);
            if (visibility[columnIndex] !== undefined) {
                checkbox.checked = visibility[columnIndex];
                toggleColumnVisibility(columnIndex, visibility[columnIndex]);
            }
        });
    } catch (e) {
        console.warn('Error loading column visibility preferences:', e);
    }
}

function adjustStickyColumns() {
    const table = document.getElementById('tickets-table');
    if (!table) return;

    const stickyCols = table.querySelectorAll('.sticky-col:visible');
    let currentOffset = 0;

    stickyCols.forEach(col => {
        col.style.left = `${currentOffset}px`;
        currentOffset += col.offsetWidth;
    });
}
