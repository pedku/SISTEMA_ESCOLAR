# 🏛️ Arquitectura Multi-Institucional

## Resumen

El sistema escolar ahora soporta múltiples instituciones educativas de manera aislada y escalable. Un usuario root puede crear y gestionar varias instituciones, y cada institución tiene sus datos completamente aislados.

## Diseño de Base de Datos

### Tablas con `institution_id`:

| Tabla | Columna | Nullable | Descripción |
|-------|---------|----------|-------------|
| `users` | `institution_id` | ✅ (solo root) | Vincula usuario a institución |
| `subjects` | `institution_id` | ❌ | Asignaturas por institución |
| `achievements` | `institution_id` | ✅ (globales si NULL) | Logros por institución o globales |
| `campuses` | `institution_id` | ❌ | Sedes de institución |
| `academic_periods` | `institution_id` | ❌ | Periodos académicos |
| `grade_criteria` | `institution_id` | ❌ | Criterios de evaluación |
| `academic_students` | `institution_id` | ❌ | Estudiantes matriculados |

### Relaciones Indirectas (scoped vía joins):

- `grades` → scoped vía `campus_id` → `Campus.institution_id`
- `subject_grades` → scoped vía `grade_id` → `Grade.campus_id` → `Campus.institution_id`
- `grade_records`, `final_grades`, `attendance` → scoped vía `student_id` → `AcademicStudent.institution_id`

## Jerarquía de Usuarios

### Root (Super-Administrador)
- `institution_id = NULL` → Puede ver TODAS las instituciones
- Puede crear/editar/eliminar instituciones
- Puede cambiar entre instituciones con `/institution/switch`
- Datos scoped a institución activa (si hay una seleccionada)

### Admin / Coordinator / Teacher
- `institution_id = REQUIRED` → Solo ven SU institución
- No pueden acceder a datos de otras instituciones
- CRUD scoped a su institución

### Student / Parent
- `institution_id = REQUIRED` (vía `AcademicStudent`)
- Solo ven datos de su institución

## Sistema de Contexto Institucional

### Funciones Principales

```python
from utils.institution_resolver import (
    get_current_institution,      # Obtiene institución actual
    filter_by_institution,        # Filtra query por institución
    get_institution_grades,       # Helper para grades
    get_institution_subjects,     # Helper para subjects
    get_institution_students,     # Helper para students
    set_active_institution,       # Cambiar institución (root)
    can_access_institution        # Verificar acceso
)
```

### Uso en Rutas

```python
@route('/some-endpoint')
@login_required
def my_endpoint():
    institution = get_current_institution()
    
    if institution:
        # Non-root o root con institución activa
        students = AcademicStudent.query.filter_by(
            institution_id=institution.id
        ).all()
    else:
        # Root sin institución activa (ve todo)
        students = AcademicStudent.query.all()
    
    return render_template('...', students=students, institution=institution)
```

## Aislamiento de Datos

### Reglas de Filtrado:

1. **Grades**: `JOIN Campus ON grades.campus_id = campuses.id WHERE campuses.institution_id = X`
2. **Subjects**: `WHERE subjects.institution_id = X`
3. **Students**: `WHERE academic_students.institution_id = X`
4. **Teachers**: `JOIN SubjectGrade JOIN Grade JOIN Campus WHERE campuses.institution_id = X`
5. **Attendance**: Scoped vía student o subject-grade
6. **Grades Records**: Scoped vía student o subject-grade

## Migración

### Para BD existente:
```bash
python migrate_multi_institution.py
```

Esto:
1. Agrega `institution_id` a tablas existentes
2. Asigna datos huérfanos a la primera institución
3. Preserva root users con `institution_id = NULL`

### Para BD nueva:
```bash
python init_db.py
```

## Institution Switching (Root Only)

### Endpoint:
```
POST /institution/switch
Form data: institution_id=<id> o vacío (para ver todas)
```

### UI:
```
GET /institution/institutions/select
```

Muestra lista de instituciones con opción de seleccionar.

## Pruebas

### Crear múltiples instituciones:
1. Login como root
2. Ir a `/institution/new`
3. Crear institución "Colegio A"
4. Crear institución "Colegio B"
5. Ir a `/institution/institutions/select`
6. Seleccionar "Colegio A"
7. Crear grados, asignaturas, estudiantes (solo se ven en Colegio A)
8. Cambiar a "Colegio B"
9. Verificar que NO se ven los datos de Colegio A

### Verificar aislamiento:
1. Crear usuario admin con `institution_id = Colegio A`
2. Login como ese admin
3. Verificar que solo ve datos de Colegio A

## Próximos Pasos

- [ ] Agregar `institution_id` a templates (forms de creación)
- [ ] UI para mostrar institución actual en navbar
- [ ] Auditoría de queries para asegurar aislamiento completo
- [ ] Tests automatizados de aislamiento multi-institucional

## Notas Importantes

⚠️ **Los usuarios root pueden acceder a todas las instituciones** a menos que tengan una institución activa seleccionada.

⚠️ **Los datos existentes antes de la migración** se asignan a la primera institución encontrada.

⚠️ **Las asignaturas ahora son por institución**: El mismo código puede existir en múltiples instituciones.

⚠️ **Los logros pueden ser globales o por institución**: `institution_id = NULL` significa logro global.
