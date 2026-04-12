/* ============================================
   SIGE - Sistema Integral de Gestión Escolar
   Main JavaScript
   ============================================ */

$(document).ready(function() {

    // ============================================
    // Sidebar Toggle - Fixed & Responsive
    // ============================================
    const $sidebar = $('#sidebar');
    const $overlay = $('#sidebarOverlay');
    const isMobile = () => window.innerWidth < 992;

    // Toggle sidebar visibility
    $('#sidebarCollapse').on('click', function() {
        if (isMobile()) {
            // Mobile: show/hide as overlay
            $sidebar.toggleClass('show');
            $overlay.toggleClass('show');
            $('body').toggleClass('sidebar-open');
        } else {
            // Desktop: slide in/out
            $sidebar.toggleClass('hide');
            $('#content').toggleClass('expanded');
        }
    });

    // Close sidebar on mobile (X button)
    $('#sidebarCloseBtn').on('click', function() {
        closeSidebar();
    });

    // Close sidebar when clicking overlay
    $overlay.on('click', function() {
        closeSidebar();
    });

    // Close sidebar function
    function closeSidebar() {
        $sidebar.removeClass('show');
        $overlay.removeClass('show');
        $('body').removeClass('sidebar-open');
    }

    // Close sidebar on ESC key
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' && $sidebar.hasClass('show')) {
            closeSidebar();
        }
    });

    // Close sidebar when clicking a submenu link (mobile only)
    $sidebar.on('click', 'ul.submenu li a', function() {
        if (isMobile()) {
            // Small delay to allow link navigation
            setTimeout(closeSidebar, 150);
        }
    });

    // Handle window resize
    let resizeTimer;
    $(window).on('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (!isMobile()) {
                // Reset mobile classes when switching to desktop
                $sidebar.removeClass('show');
                $overlay.removeClass('show');
                $('body').removeClass('sidebar-open');
            } else {
                // Reset desktop classes when switching to mobile
                $sidebar.removeClass('hide');
                $('#content').removeClass('expanded');
            }
        }, 250);
    });

    // ============================================
    // Submenu Toggle - Enhanced
    // ============================================
    $('.submenu-toggle').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const $parent = $(this).closest('li.has-submenu');
        const $submenu = $parent.find('.submenu');
        const isExpanded = $(this).attr('aria-expanded') === 'true';

        // Toggle current submenu
        $(this).attr('aria-expanded', !isExpanded);
        $parent.toggleClass('open');

        // Bootstrap collapse
        if (isExpanded) {
            $submenu.collapse('hide');
        } else {
            $submenu.collapse('show');
        }
    });

    // ============================================
    // Initialize DataTables
    // ============================================
    $('.datatable').each(function() {
        // Skip if already initialized
        if ($.fn.DataTable.isDataTable(this)) {
            return;
        }

        $(this).DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json',
                search: "Buscar:",
                lengthMenu: "Mostrar _MENU_ registros",
                info: "Mostrando _START_ - _END_ de _TOTAL_ registros",
                infoEmpty: "No hay registros disponibles",
                infoFiltered: "(filtrado de _MAX_ registros totales)",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: "Siguiente",
                    previous: "Anterior"
                }
            },
            pageLength: 20,
            responsive: true,
            order: [[0, 'desc']]
        });
    });

    // ============================================
    // Auto-hide alerts after 5 seconds
    // ============================================
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // ============================================
    // Initialize Tooltips
    // ============================================
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ============================================
    // Initialize Popovers
    // ============================================
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // ============================================
    // Close dropdowns on mobile after selection
    // ============================================
    $('.dropdown-menu a').on('click', function() {
        if (isMobile()) {
            const dropdown = bootstrap.Dropdown.getInstance(this.closest('.dropdown'));
            if (dropdown) dropdown.hide();
        }
    });

});

// ============================================
// SweetAlert2 Helper Functions
// ============================================

function confirmDelete(message, callback) {
    Swal.fire({
        title: '¿Está seguro?',
        text: message || 'Esta acción no se puede deshacer.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e74c3c',
        cancelButtonColor: '#95a5a6',
        confirmButtonText: 'Sí, continuar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            if (callback) callback();
        }
    });
}

function confirmAction(title, message, callback) {
    Swal.fire({
        title: title || '¿Confirmar acción?',
        text: message || '¿Desea continuar?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3498db',
        cancelButtonColor: '#95a5a6',
        confirmButtonText: 'Sí',
        cancelButtonText: 'No',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            if (callback) callback();
        }
    });
}

function showSuccess(message, title) {
    Swal.fire({
        icon: 'success',
        title: title || '¡Éxito!',
        text: message,
        timer: 3000,
        showConfirmButton: false
    });
}

function showError(message, title) {
    Swal.fire({
        icon: 'error',
        title: title || 'Error',
        text: message
    });
}

function showWarning(message, title) {
    Swal.fire({
        icon: 'warning',
        title: title || 'Advertencia',
        text: message
    });
}

function showInfo(message, title) {
    Swal.fire({
        icon: 'info',
        title: title || 'Información',
        text: message
    });
}

// ============================================
// Grade Formatting Functions
// ============================================

function formatGrade(grade) {
    if (grade === null || grade === undefined) return 'N/A';
    
    const numGrade = parseFloat(grade);
    if (isNaN(numGrade)) return 'N/A';
    
    let className = 'grade-bajo';
    if (numGrade >= 4.6) className = 'grade-superior';
    else if (numGrade >= 4.0) className = 'grade-alto';
    else if (numGrade >= 3.0) className = 'grade-basico';
    
    return `<span class="${className}">${numGrade.toFixed(1)}</span>`;
}

function getGradeStatus(grade) {
    if (grade === null || grade === undefined) return '<span class="status-no-evaluado">No evaluado</span>';
    
    const numGrade = parseFloat(grade);
    if (numGrade >= 3.0) {
        return '<span class="status-ganada"><i class="bi bi-check-circle"></i> Ganada</span>';
    } else {
        return '<span class="status-perdida"><i class="bi bi-x-circle"></i> Perdida</span>';
    }
}

function getPerformanceLevel(grade) {
    if (grade === null || grade === undefined) return 'N/A';
    
    const numGrade = parseFloat(grade);
    if (numGrade >= 4.6) return 'Superior';
    if (numGrade >= 4.0) return 'Alto';
    if (numGrade >= 3.0) return 'Básico';
    return 'Bajo';
}

function calculateAverage(grades) {
    if (!grades || grades.length === 0) return 0;
    const validGrades = grades.filter(g => g !== null && g !== undefined && !isNaN(parseFloat(g)));
    if (validGrades.length === 0) return 0;
    const sum = validGrades.reduce((a, b) => a + parseFloat(b), 0);
    return (sum / validGrades.length).toFixed(1);
}

// ============================================
// Export Functions
// ============================================

function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length - 1; j++) {
            row.push('"' + cols[j].innerText.replace(/"/g, '""') + '"');
        }
        
        csv.push(row.join(','));
    }
    
    downloadCSV(csv.join('\n'), filename);
}

function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// ============================================
// Print Function
// ============================================

function printPage() {
    window.print();
}

// ============================================
// Form Validation
// ============================================

function validateGradeForm(form) {
    const inputs = form.querySelectorAll('input[type="number"]');
    let isValid = true;
    
    inputs.forEach(input => {
        const value = parseFloat(input.value);
        if (isNaN(value) || value < 1.0 || value > 5.0) {
            isValid = false;
            input.classList.add('is-invalid');
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// ============================================
// Loading Overlay
// ============================================

function showLoading(message) {
    const overlay = $('<div class="loading-overlay">' +
        '<div class="text-center">' +
        '<div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;"></div>' +
        '<p class="mt-3">' + (message || 'Cargando...') + '</p>' +
        '</div></div>');
    $('body').append(overlay);
}

function hideLoading() {
    $('.loading-overlay').remove();
}

// ============================================
// Auto-calculate Final Grade
// ============================================

function calculateFinalGrade(criteriaSelector) {
    const criteria = document.querySelectorAll(criteriaSelector || '.grade-criterion');
    let finalGrade = 0;
    let totalWeight = 0;
    
    criteria.forEach(criterion => {
        const weight = parseFloat(criterion.dataset.weight);
        const grade = parseFloat(criterion.value);
        
        if (!isNaN(grade) && !isNaN(weight)) {
            finalGrade += grade * (weight / 100);
            totalWeight += weight;
        }
    });
    
    if (totalWeight > 0) {
        return (finalGrade / totalWeight * 100).toFixed(1);
    }
    
    return null;
}
