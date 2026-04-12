# Sistema de Formularios con Persistencia de Datos

## ✅ Implementado

### Formularios con `form_data` y `errors`:

#### 1. **Gestión de Usuarios** ✅
- `routes/users.py` - `user_create()`, `user_edit()`
- Templates: `users/create.html`, `users/edit.html`
- Mantiene datos tras errores de validación

#### 2. **Gestión de Sedes** ✅  
- `routes/institution.py` - `campus_new()`, `campus_edit()`
- Template: `institution/campus_form.html`
- Validación de código único y sede principal

#### 3. **Gestión de Grados** ✅
- `routes/institution.py` - `grade_new()`, `grade_edit()`
- Template: `institution/grade_form.html`
- Validación de nombre y sede obligatorios

#### 4. **Gestión de Asignaturas** ✅ (NUEVO)
- `routes/institution.py` - `subject_new()`, `subject_edit()`
- Template: `institution/subject_form.html`
- Validación de nombre obligatorio

#### 5. **Gestión de Periodos** ✅ (NUEVO)
- `routes/institution.py` - `period_new()`, `period_edit()`
- Template: `institution/period_form.html` (PENDIENTE actualizar)
- Validación de fechas y nombres

## 📋 Pendiente

### Formularios que necesitan actualización:

#### 6. **Gestión de Criterios**
- `routes/institution.py` - `criteria_new()`, `criteria_edit()`
- Template: `institution/criteria_form.html`

#### 7. **Gestión de Instituciones**
- `routes/institution.py` - `institution_new()`, `institution_edit()`, `config()`
- Templates: `institution/institution_form.html`

#### 8. **Gestión de Estudiantes**
- `routes/students.py` - `new()`, `edit()`
- Templates: `students/student_form.html`

#### 9. **Gestión de Observaciones**
- `routes/observations.py` - `observations_new()`, `observations_edit()`
- Templates: `observations/create.html`, `observations/edit.html`

## 🎯 Patrón de Implementación

### Backend (Python):
```python
if request.method == 'POST':
    # 1. Extraer datos
    name = request.form.get('name', '').strip()
    
    # 2. Validar
    errors = {}
    if not name:
        errors['name'] = 'El nombre es obligatorio'
    
    # 3. Si hay errores, retornar con form_data y errors
    if errors:
        flash('⚠️ Por favor corrige los errores', 'error')
        return render_template('form.html',
                             form_data={'name': name, ...},
                             errors=errors)
    
    # 4. Crear/Actualizar
    try:
        db.session.commit()
        flash('✅ Creado exitosamente', 'success')
        return redirect(...)
    except Exception as e:
        db.session.rollback()
        return render_template('form.html',
                             form_data={...},
                             errors={'general': str(e)})
```

### Frontend (HTML):
```html
<input type="text" name="name" 
       value="{{ form_data.name if form_data else (object.name if object else '') }}" 
       class="form-control {% if errors and errors.name %}is-invalid{% endif %}">

{% if errors and errors.name %}
<div class="invalid-feedback">{{ errors.name }}</div>
{% endif %}
```

## 📝 Notas

- **JavaScript** (`form-validation.js`) ya valida en tiempo real
- **Bootstrap 5** muestra errores con clases `is-invalid` e `invalid-feedback`
- **Servidor** retorna `form_data` para repoblar campos
- **Flash messages** alertan sobre errores generales
