/* ============================================
   SIGE - Form Validation System
   Real-time validation with helpful messages
   ============================================ */

$(document).ready(function() {
    
    // ============================================
    // Validation Rules
    // ============================================
    
    const validationRules = {
        // Name fields
        'name': {
            required: true,
            minLength: 3,
            message: 'El nombre debe tener al menos 3 caracteres'
        },
        
        // Email
        'email': {
            required: true,
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            message: 'Ingresa un correo electrónico válido (ejemplo: usuario@dominio.com)'
        },
        
        // Phone
        'phone': {
            pattern: /^[\d\s\-\(\)\+]{7,15}$/,
            message: 'Ingresa un número de teléfono válido (7-15 dígitos)',
            optional: true
        },
        
        // Document number
        'document_number': {
            required: true,
            pattern: /^[\d]{5,15}$/,
            message: 'El documento debe contener entre 5 y 15 dígitos numéricos'
        },
        
        // NIT
        'nit': {
            pattern: /^[\d\-\.\,]{5,20}$/,
            message: 'Formato válido: 900.123.456-7 o 12345678',
            optional: true
        },
        
        // Address
        'address': {
            optional: true,
            message: 'Ejemplo: Calle 123 # 45-67, Barrio Centro'
        },
        
        // Year
        'academic_year': {
            required: true,
            pattern: /^20\d{2}$/,
            message: 'Formato válido: 2025, 2026, etc.'
        },
        
        // Password
        'password': {
            required: true,
            minLength: 6,
            message: 'La contraseña debe tener al menos 6 caracteres'
        }
    };
    
    // ============================================
    // Validation Functions
    // ============================================
    
    function validateField(field) {
        const $field = $(field);
        const fieldName = $field.attr('name') || $field.attr('id');
        const value = $field.val().trim();
        const rules = validationRules[fieldName];
        
        if (!rules) return true;
        
        // Clear previous state
        $field.removeClass('is-valid is-invalid');
        $field.siblings('.validation-message').remove();
        $field.siblings('.field-hint').show();
        
        // Check if required
        if (!rules.optional && !value) {
            showFieldError($field, 'Este campo es obligatorio');
            return false;
        }
        
        // Skip validation if optional and empty
        if (rules.optional && !value) return true;
        
        // Check min length
        if (rules.minLength && value.length < rules.minLength) {
            showFieldError($field, rules.message);
            return false;
        }
        
        // Check pattern
        if (rules.pattern && !rules.pattern.test(value)) {
            showFieldError($field, rules.message);
            return false;
        }
        
        // Field is valid
        showFieldSuccess($field);
        return true;
    }
    
    function showFieldError($field, message) {
        $field.addClass('is-invalid');
        $field.siblings('.field-hint').hide();
        
        if (!$field.siblings('.validation-message').length) {
            $field.after(`<div class="validation-message text-danger mt-1 small"><i class="bi bi-exclamation-circle me-1"></i>${message}</div>`);
        }
    }
    
    function showFieldSuccess($field) {
        $field.addClass('is-valid');
    }
    
    function clearFieldValidation($field) {
        $field.removeClass('is-invalid is-valid');
        $field.siblings('.validation-message').remove();
        $field.siblings('.field-hint').show();
    }
    
    // ============================================
    // Event Handlers
    // ============================================
    
    // Validate on blur
    $('input, select, textarea').on('blur', function() {
        if ($(this).hasClass('no-validation')) return;
        validateField(this);
    });
    
    // Validate on input (for real-time feedback)
    $('input, textarea').on('input', function() {
        if ($(this).hasClass('no-validation')) return;
        const $field = $(this);
        
        // Only validate if field already has validation state
        if ($field.hasClass('is-invalid') || $field.hasClass('is-valid')) {
            validateField(this);
        }
    });
    
    // Clear validation on focus
    $('input, select, textarea').on('focus', function() {
        clearFieldValidation($(this));
    });
    
    // ============================================
    // Form Submit Handler
    // ============================================
    
    $('form').on('submit', function(e) {
        let isValid = true;
        let firstInvalidField = null;
        
        // Validate all required fields
        $(this).find('input, select, textarea').each(function() {
            if ($(this).hasClass('no-validation')) return;
            if ($(this).attr('type') === 'hidden') return;
            if ($(this).attr('type') === 'file') return;
            if ($(this).attr('type') === 'checkbox') return;
            if ($(this).attr('type') === 'submit') return;
            
            if (!validateField(this)) {
                isValid = false;
                if (!firstInvalidField) {
                    firstInvalidField = $(this);
                }
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            
            // Scroll to first invalid field
            if (firstInvalidField) {
                $('html, body').animate({
                    scrollTop: firstInvalidField.offset().top - 100
                }, 500);
                firstInvalidField.focus();
            }
            
            // Show alert
            showValidationAlert();
        }
    });
    
    // ============================================
    // Server-side Error Display
    // ============================================
    
    // This function can be called from templates to show server errors
    window.showServerFieldError = function(fieldName, message) {
        const $field = $(`[name="${fieldName}"]`);
        if ($field.length) {
            showFieldError($field, message);
            $field.focus();
        }
    };
    
    // ============================================
    // Helper Functions
    // ============================================
    
    function showValidationAlert() {
        // Remove existing alert
        $('.validation-alert').remove();
        
        const alert = `
            <div class="validation-alert">
                <div class="alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3 shadow-lg" 
                     role="alert" style="z-index: 9999; min-width: 400px;">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    <strong>¡Atención!</strong> Por favor corrige los campos marcados en rojo.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            </div>
        `;
        
        $('body').append(alert);
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            $('.validation-alert').fadeOut();
        }, 5000);
    }
    
    // ============================================
    // Add Helper Text to Fields
    // ============================================
    
    // Add helpful hints to common fields
    const fieldHints = {
        'email': '💡 Ejemplo: usuario@colegio.edu.co',
        'phone': '💡 Formatos: 3001234567, (601) 234 5678',
        'address': '💡 Ejemplo: Calle 123 # 45-67, Barrio',
        'nit': '💡 Ejemplo: 900.123.456-7',
        'document_number': '💡 Solo números, sin puntos ni comas',
        'academic_year': '💡 Año lectivo actual o próximo'
    };
    
    Object.keys(fieldHints).forEach(function(fieldName) {
        const $field = $(`[name="${fieldName}"]`);
        if ($field.length && !$field.siblings('.field-hint').length) {
            $field.after(`<div class="field-hint text-muted small mt-1"><small>${fieldHints[fieldName]}</small></div>`);
        }
    });
    
});
