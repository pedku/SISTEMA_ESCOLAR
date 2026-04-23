# 📚 SIGE - Documentación Técnica Completa

## Sistema Integral de Gestión Escolar

> **Versión**: 1.5 - Soporte Multi-jornada y Analíticas | **Rama**: main | **Última actualización**: 2026-04-23
> **Stack**: Python 3 + Flask + Bootstrap 5 + Chart.js + DataTables + SQLite
> **Total errores corregidos**: 50+ | **Testing**: Pirámide de 4 fases validada + Pytest

---

## 📋 Tabla de Contenidos

1. [Arquitectura](#arquitectura)
2. [Modelos de Base de Datos](#modelos-de-base-de-datos)
3. [Blueprints y Rutas](#blueprints-y-rutas)
4. [Sistema de Roles](#sistema-de-roles)
5. [Sistema de Calificación](#sistema-de-calificación)
6. [Utilidades Core](#utilidades-core)
7. [Patrones de Diseño](#patrones-de-diseño)
8. [Guía de Desarrollo](#guía-de-desarrollo)
9. [Próximos Pasos](#próximos-pasos)

---

## Arquitectura

```
sistema_escolar/
├── app.py                          # Application factory
├── config.py                       # Configuración multi-entorno
├── extensions.py                   # Extensiones Flask centralizadas
├── init_db.py                      # Inicialización BD + seed data
│
├── models/                         # 10 archivos, ~25 tablas
│   ├── user.py                     # User (auth + 7 roles)
│   ├── institution.py              # Institution, Campus
│   ├── academic.py                 # Grade, Subject, SubjectGrade, AcademicStudent, ParentStudent
│   ├── grading.py                  # AcademicPeriod, GradeCriteria, GradeRecord, FinalGrade, AnnualGrade
│   ├── attendance.py               # Attendance
│   ├── observation.py              # Observation
│   ├── report.py                   # ReportCard, ReportCardObservation
│   ├── achievement.py              # Achievement, StudentAchievement
│   ├── alert.py                    # Alert
│   └── scheduling.py               # Classroom, StudentEnrollment, TeacherSubjectAssignment, Schedule, ScheduleBlock
│
├── routes/                         # 15 blueprints
│   ├── auth.py                     # Login, logout, profile, password
│   ├── dashboard.py                # 7 dashboards por rol
│   ├── institution.py              # CRUD institución, sedes, grados, asignaturas, periodos, criterios
│   ├── students.py                 # CRUD estudiantes + Excel upload
│   ├── users.py                    # CRUD usuarios + permisos de roles
│   ├── grades.py                   # Sistema de notas (lock, finales, anuales)
│   ├── report_cards.py             # Boletines PDF + gestión
│   ├── attendance.py               # Asistencia diaria
│   ├── observations.py             # Observaciones comportamiento
│   ├── metrics.py                  # Métricas profesor + institucionales
│   ├── alerts.py                   # Sistema alertas tempranas
│   ├── achievements.py             # Logros/gamificación
│   ├── parent.py                   # Portal de acudientes
│   ├── qr.py                       # Acceso QR (placeholder)
│   └── scheduling.py               # Matrícula, asignación de profesores, generación de horarios
│
├── services/                       # Capa de servicios (SRP)
│   ├── grade_calculator.py         # Cálculos de notas
│   ├── excel_handler.py            # Manejo de Excel
│   ├── report_card_service.py      # Generación de boletines
│   ├── student_service.py          # CRUD estudiantes
│   ├── metrics_service.py          # Estadísticas institucionales
│   └── teacher_analytics.py        # Analítica avanzada y sugerencias IA
│
├── utils/                          # 12 utilidades
│   ├── decorators.py               # @role_required, @login_required
│   ├── validators.py               # Validación documento, email, notas
│   ├── pdf_generator.py            # Generación PDF (WeasyPrint)
│   ├── charts.py                   # Configuración Chart.js
│   ├── institution_resolver.py     # get_current_institution()
│   ├── username_generator.py       # Usernames incrementales
│   ├── alert_engine.py             # Motor 6 reglas de alerta
│   ├── achievement_engine.py       # Motor auto-award 7 logros
│   └── template_helpers.py         # Helpers Jinja2
│
├── templates/                      # ~98 templates HTML
│   ├── base.html                   # Layout base con sidebar dinámico
│   ├── dashboard/                  # 7 dashboards por rol
│   ├── institution/                # Gestión institucional
│   ├── students/                   # Gestión estudiantes
│   ├── users/                      # Gestión usuarios
│   ├── grades/                     # Sistema de notas
│   ├── report_cards/               # Boletines PDF
│   ├── attendance/                 # Asistencia
│   ├── observations/               # Observaciones
│   ├── metrics/                    # Métricas y analítica
│   ├── alerts/                     # Alertas tempranas
│   ├── achievements/               # Logros/gamificación
│   ├── parent/                     # Portal acudientes
│   ├── qr/                         # Acceso QR
│   └── scheduling/                 # NUEVO: Matrícula y horarios (12 templates)
│       ├── enrollments/            # Listado y formulario de matrículas
│       ├── assignments/            # Listado y formulario de asignaciones
│       ├── subject_grades/         # Listado y formulario de materias por grado
│       ├── classrooms/             # Listado y formulario de salones
│       ├── schedules/              # Listado y generación de horarios
│       └── blocks/                 # Listado y formulario de bloques horarios
│
├── static/
│   ├── css/
│   │   ├── main.css                # Estilos principales
│   │   └── sige-styles.css         # Estilos profesionales (+1500 líneas)
│   └── js/
│       ├── main.js                 # DataTables init, sidebar logic
│       └── form-validation.js      # Validación formularios en tiempo real
│
└── tests/                          # 12 scripts de prueba
```

---

## Modelos de Base de Datos

### Auth y Usuarios
| Modelo | Tabla | Campos Clave |
|--------|-------|-------------|
| **User** | `users` | username, email, password_hash, first_name, last_name, document_number, role, institution_id, is_active, must_change_password |

### Institución
| Modelo | Tabla | Campos Clave |
|--------|-------|-------------|
| **Institution** | `institutions` | name, nit, address, municipality, department, academic_year |
| **Campus** | `campuses` | institution_id, name, code, is_main_campus, active |

### Estructura Académica
| Modelo | Tabla | Campos Clave |
|--------|-------|-------------|
| **Grade** | `grades` | campus_id, director_id, name, academic_year, max_students, shift |
| **Subject** | `subjects` | institution_id, name, code |
| **SubjectGrade** | `subject_grades` | subject_id, grade_id, teacher_id, hours_per_week (default 4) |
| **AcademicStudent** | `academic_students` | user_id (unique), institution_id, campus_id, grade_id, document_number, status |
| **ParentStudent** | `parent_students` | parent_id, student_id, relationship (unique pair) |

### Calificaciones
| Modelo | Tabla | Campos Clave |
|--------|-------|-------------|
| **AcademicPeriod** | `academic_periods` | institution_id, name, short_name, start_date, end_date, is_active, order |
| **GradeCriteria** | `grade_criteria` | institution_id, name, weight (%), description, order |
| **GradeRecord** | `grade_records` | student_id, subject_grade_id, period_id, criterion_id, score (1.0-5.0), locked |
| **FinalGrade** | `final_grades` | student_id, subject_grade_id, period_id, final_score, status (ganada/perdida) |
| **AnnualGrade** | `annual_grades` | student_id, subject_grade_id, annual_score, status (aprobado/reprobado), academic_year |

### Complementarios
| Modelo | Tabla | Campos Clave |
|--------|-------|-------------|
| **Attendance** | `attendance` | student_id, subject_grade_id, date, status (presente/ausente/justificado/excusado) |
| **Observation** | `observations` | student_id, author_id, type (positiva/negativa/seguimiento/convivencia), description, notified |
| **ReportCard** | `report_cards` | student_id, period_id, pdf_path, delivery_status (pendiente/entregado) |
| **ReportCardObservation** | `report_card_observations` | report_card_id, subject_grade_id, observation |
| **Achievement** | `achievements` | name, description, icon, criteria, category |
| **StudentAchievement** | `student_achievements` | student_id, achievement_id, period_id, earned_at |
| **Alert** | `alerts` | student_id, alert_type (6 tipos), severity (alta/media/baja), resolved, notes |

### Programación y Matrícula (NUEVO)
| Modelo | Tabla | Campos Clave |
|--------|-------|-------------|
| **Classroom** | `classrooms` | campus_id, name, code, capacity, classroom_type, floor, building |
| **StudentEnrollment** | `student_enrollments` | student_id, subject_grade_id, academic_year, status, enrollment_date |
| **TeacherSubjectAssignment** | `teacher_subject_assignments` | subject_grade_id, teacher_id, academic_year, status, assignment_date |
| **Schedule** | `schedules` | subject_grade_id, classroom_id, day_of_week, start_time, end_time, academic_year |
| **ScheduleBlock** | `schedule_blocks` | campus_id, name, start_time, end_time, is_break, order_num, shift (Mañana/Tarde/...), academic_year |

---

## Blueprints y Rutas

### 1. Auth (`auth_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/login` | GET/POST | Autenticación |
| `/logout` | GET | Cerrar sesión |
| `/profile` | GET/POST | Ver/editar perfil |
| `/change-password` | POST | Cambiar contraseña |
| `/force-change-password` | GET/POST | Cambio obligatorio primer login |

### 2. Dashboard (`dashboard_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/` | GET | Dashboard según rol (7 variantes) |
| `/dashboard` | GET | Dashboard con métricas rápidas |

### 3. Institución (`institution_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/institution` | GET/POST | Configurar institución |
| `/institution/users/<id>` | GET | Usuarios de la institución |
| `/institution/add-admin/<id>` | GET/POST | Crear usuario en institución |
| `/campuses` | GET | Listar sedes |
| `/campuses/new` | GET/POST | Crear sede |
| `/campuses/<id>/edit` | GET/POST | Editar sede |
| `/campuses/api` | GET/POST | API RESTful sedes |
| `/grades` | GET | Listar grados |
| `/grades/new` | GET/POST | Crear grado |
| `/grades/<id>/edit` | GET/POST | Editar grado |
| `/subjects` | GET/POST | CRUD asignaturas |
| `/periods` | GET/POST | CRUD periodos académicos |
| `/criteria` | GET/POST | CRUD criterios evaluación |

### 4. Estudiantes (`students_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/students/` | GET | Lista con filtros + perfiles incompletos |
| `/students/new` | GET/POST | Crear estudiante completo |
| `/students/new/<user_id>` | GET/POST | Completar perfil académico |
| `/students/<id>` | GET | Perfil académico |
| `/students/<id>/edit` | GET/POST | Editar estudiante |
| `/students/<id>/delete` | POST | Eliminar estudiante |
| `/students/upload` | GET/POST | Carga masiva Excel |

### 5. Usuarios (`users_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/users/users` | GET | Lista de usuarios (filtrada por rol) |
| `/users/new` | GET/POST | Crear usuario |
| `/users/<id>/edit` | GET/POST | Editar usuario |
| `/users/<id>/delete` | POST | Eliminar usuario |

### 6. Notas (`grades_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/grades/input` | GET/POST | Selección grado+materia+periodo |
| `/grades/input/<sg_id>/<period_id>` | GET/POST | Planilla tipo spreadsheet |
| `/grades/upload` | POST | Carga masiva Excel |
| `/grades/student/<student_id>` | GET | Notas del estudiante |
| `/grades/lock` | GET/POST | Panel lock/unlock periodos |
| `/grades/final/<sg_id>/<period_id>` | GET/POST | Notas finales ponderadas |
| `/grades/annual/<sg_id>` | GET | Notas anuales |

### 7. Boletines (`report_cards_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/report-cards/manage` | GET | Panel de gestión |
| `/report-cards/generate/<student_id>/<period_id>` | POST | Generar boletín individual |
| `/report-cards/generate_bulk/<grade_id>/<period_id>` | POST | Generación masiva |
| `/report-cards/<id>` | GET | Ver PDF |
| `/report-cards/<id>/download` | GET | Descargar PDF |
| `/report-cards/history/<student_id>` | GET | Historial boletines |
| `/report-cards/<id>/deliver` | POST | Marcar entregado |
| `/report-cards/api/students/<grade_id>` | GET | API estudiantes por grado |

### 8. Asistencia (`attendance_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/attendance/` | GET/POST | Tomar asistencia |
| `/attendance/student/<id>` | GET | Historial estudiante |
| `/attendance/summary` | GET | Resumen grupal |
| `/attendance/export` | GET | Exportar CSV |

### 9. Observaciones (`observations_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/observations/` | GET/POST | Crear observación |
| `/observations/student/<id>` | GET | Historial estudiante |
| `/observations/student/<id>/quick` | GET/POST | Quick form |
| `/observations/<id>/notify` | POST | Notificar acudiente |
| `/observations/export` | GET | Exportar CSV |

### 10. Métricas (`metrics_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/metrics/teacher` | GET | Dashboard profesor |
| `/metrics/teacher/comparison` | GET | Comparativa anónima |
| `/metrics/teacher/attendance` | GET | Correlación asistencia-rendimiento |
| `/metrics/institution` | GET | Dashboard institucional |
| `/metrics/heatmap` | GET | Mapa de calor Grado×Materia |
| `/metrics/trends` | GET | Tendencias por periodo |
| `/metrics/export` | GET | Exportar Excel (5 hojas) |

### 11. Alertas (`alerts_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/alerts` | GET | Panel principal |
| `/alerts/run` | GET/POST | Ejecutar motor reglas |
| `/alerts/<id>` | GET | Detalle alerta |
| `/alerts/<id>/resolve` | POST | Marcar resuelta |
| `/alerts/export` | GET | Exportar CSV |
| `/alerts/api/count` | GET | Contador para badge sidebar |

### 12. Logros (`achievements_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/achievements` | GET | Catálogo de logros |
| `/achievements/award` | POST | Otorgar manualmente |
| `/achievements/student/<id>` | GET | Timeline logros estudiante |
| `/leaderboard` | GET | Ranking con podio |
| `/achievements/run_engine` | POST | Ejecutar auto-award |

### 13. Portal Padres (`parent_bp`)
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/parent/dashboard` | GET | Dashboard acudiente |
| `/parent/grades/<student_id>` | GET | Notas del acudido |
| `/parent/attendance/<student_id>` | GET | Calendario asistencia |
| `/parent/observations/<student_id>` | GET | Observaciones del acudido |
| `/parent/report_cards/<student_id>` | GET | Boletines del acudido |

### 14. Programación y Matrícula (`scheduling_bp`) - NUEVO
| Ruta | Método | Descripción |
|------|--------|-------------|
| `/scheduling/enrollments` | GET | Lista de matrículas de estudiantes |
| `/scheduling/enrollments/new` | GET/POST | Crear matrícula de estudiante |
| `/scheduling/enrollments/<id>/edit` | GET/POST | Editar matrícula |
| `/scheduling/enrollments/<id>/delete` | POST | Eliminar matrícula |
| `/scheduling/assignments` | GET | Lista de asignaciones de profesores |
| `/scheduling/assignments/new` | GET/POST | Asignar profesor a materia |
| `/scheduling/assignments/<id>/edit` | GET/POST | Editar asignación |
| `/scheduling/assignments/<id>/delete` | POST | Eliminar asignación |
| `/scheduling/subject-grades` | GET | Lista de materias por grado |
| `/scheduling/subject-grades/new` | GET/POST | Asignar materias a grados |
| `/scheduling/subject-grades/<id>/delete` | POST | Eliminar asignación |
| `/scheduling/classrooms` | GET | Lista de salones |
| `/scheduling/classrooms/new` | GET/POST | Crear salón |
| `/scheduling/classrooms/<id>/edit` | GET/POST | Editar salón |
| `/scheduling/classrooms/<id>/delete` | POST | Eliminar salón |
| `/scheduling/schedules` | GET | Ver horarios (filtrado por rol) |
| `/scheduling/schedules/generate` | GET | Vista para generar horarios |
| `/scheduling/schedules/generate/run` | POST | Ejecutar generador automático de horarios |
| `/scheduling/schedules/<id>/delete` | POST | Eliminar horario |
| `/scheduling/blocks` | GET | Lista de bloques de tiempo |
| `/scheduling/blocks/new` | GET/POST | Crear bloque de tiempo |
| `/scheduling/blocks/<id>/edit` | GET/POST | Editar bloque |
| `/scheduling/blocks/<id>/delete` | POST | Eliminar bloque |
| `/scheduling/api/students/by-grade/<grade_id>` | GET | API: Obtener estudiantes por grado |
| `/scheduling/api/subject-grades/by-grade/<grade_id>` | GET | API: Obtener materias por grado |

---

## Sistema de Roles

### Jerarquía
```
root (super-admin)
  └── admin (institución)
        ├── coordinator (académico)
        ├── teacher (grupo/materia)
        ├── student (consulta)
        ├── parent (acudiente)
        └── viewer (solo lectura)
```

### Permisos de Creación
| Rol puede crear | root | admin |
|----------------|------|-------|
| Root | ✅ | ❌ |
| Admin | ✅ | ❌ |
| Coordinador | ✅ | ✅ |
| Profesor | ✅ | ✅ |
| Estudiante | ✅ | ✅ |
| Acudiente | ✅ | ✅ |
| Viewer | ✅ | ✅ |

### Reglas de Aislamiento
- **root**: Ve TODAS las instituciones y datos
- **admin**: Ve SOLO su institución asignada (`user.institution_id`)
- **coordinator/teacher**: Ven datos de SU institución vía `get_current_institution()`
- **student**: Ve SOLO sus propios datos
- **parent**: Ve SOLO estudiantes vinculados vía `ParentStudent`
- **viewer**: Solo lectura, institución asignada

---

## Sistema de Calificación

### Escala: 1.0 - 5.0
| Rango | Desempeño | Estado |
|-------|-----------|--------|
| 4.6 - 5.0 | Superior | ✅ Ganada |
| 4.0 - 4.5 | Alto | ✅ Ganada |
| 3.0 - 3.9 | Básico | ✅ Ganada |
| 1.0 - 2.9 | Bajo | ❌ Perdida |

### Criterios de Evaluación (configurables)
| Criterio | Peso por defecto |
|----------|-----------------|
| Seguimiento | 20% |
| Formativo | 20% |
| Cognitivo | 30% |
| Procedimental | 30% |

### Cálculo Nota Final
```
Nota Final = Σ(criterio_score × criterio_weight / 100)
```

### Cálculo Nota Anual
```
Nota Anual = (P1 + P2 + P3 + P4) / 4
```

---

## Utilidades Core

### `utils/decorators.py`
- `@role_required(*roles)`: Verifica que el usuario tenga uno de los roles
- `@institution_required`: Verifica que el usuario tenga institución asignada

### `utils/institution_resolver.py`
- `get_current_institution()`: Retorna institución según rol y sesión
- `get_institution_students()`: Query de estudiantes filtrada por institución
- `filter_by_institution()`: Filtra cualquier query por institución

### `utils/alert_engine.py`
Motor con 6 reglas automáticas:
| Alerta | Condición | Severidad |
|--------|-----------|-----------|
| Riesgo Académico | FinalGrade < 3.0 | alta |
| Tendencia Negativa | Bajó >0.5 pts entre periodos | media |
| Inasistencia Crítica | >20% ausencias en 30 días | media |
| Grupo en Riesgo | >30% del grupo pierde con mismo profesor | alta |
| Riesgo Deserción | Notas bajas + ausencias altas combinadas | alta |
| Mejora Destacable | Subió >1.0 pts entre periodos | baja |

### `utils/achievement_engine.py`
Motor con 7 reglas de auto-award:
| Logro | Criterio | Icono |
|-------|----------|-------|
| Superador | Subió ≥1.0 pts entre periodos | 📈 |
| Excelencia | Nota ≥4.5 en periodo | ⭐ |
| Asistencia Perfecta | 0 ausencias en periodo | ✅ |
| Todo Terreno | Todas las materias ganadas | 🏅 |
| Resiliente | Recuperó materia perdida | 💪 |
| Constancia | 3 periodos ≥4.0 seguidos | 🔥 |
| Compañero | Recibió observación positiva | 🤝 |

### `utils/username_generator.py`
- `generate_username_from_db(first_name, last_name)`: Primera inicial + apellido + número incremental
- Ejemplo: `pedro castro` → `pcastro1`, `pcastro2`, `pcastro3`...

---

## Patrones de Diseño

### Estándar de Formularios
1. **Validación en tiempo real**: JavaScript valida al salir del campo (on blur)
2. **Mantener datos**: NUNCA borrar datos al retornar con errores
3. **Mensajes por campo**: `is-invalid` + `invalid-feedback` debajo del campo
4. **Alerta general**: Para errores del servidor (`errors.general`)
5. **Backend retorna**: `form_data` dict + `errors` dict al template

### Estándar de CRUD Pages
```
┌── Header: Título + Botones ──────────────────┐
│  📋 Gestión de X        [+ Nuevo] [Volver]   │
├── Stat Cards (3-4) ──────────────────────────┤
│  [Total]  [Activos]  [Inactivos]  [Con X]    │
├── Filtros (si aplica) ───────────────────────┤
│  [Select] [Select] [Search] [Filtrar] [Limpiar]│
├── Tabla (DataTables español) ────────────────┤
│  # | Campo1 | Campo2 | Estado | Acciones      │
│  ─────────────────────────────────────────    │
│  1 | Valor  | Valor  | [Badge]| [👁️] [✏️] [🗑️] │
└───────────────────────────────────────────────┘
```

### Estándar de Seguridad
1. **SIEMPRE** usar `@login_required` en todas las rutas
2. **SIEMPRE** usar `@role_required` para restringir por rol
3. **SIEMPRE** filtrar por `get_current_institution()` para aislar datos
4. **SIEMPRE** verificar permisos antes de editar/eliminar
5. **NUNCA** confiar en IDs del cliente sin verificar ownership

---

## Guía de Desarrollo

### Cómo Agregar una Nueva Ruta
```python
# 1. En routes/mi_modulo.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from extensions import db
from utils.decorators import role_required
from utils.institution_resolver import get_current_institution

mi_bp = Blueprint('mi_modulo', __name__)

@mi_bp.route('/mi-ruta')
@login_required
@role_required('root', 'admin')
def mi_funcion():
    institution = get_current_institution()
    if not institution:
        flash('Seleccione institución primero.', 'warning')
        return redirect(url_for('dashboard.index'))
    
    # Lógica aquí
    return render_template('mi_modulo/vista.html', data=data)
```

### Cómo Registrar un Blueprint
```python
# En app.py
from routes.mi_modulo import mi_bp
app.register_blueprint(mi_bp, url_prefix='/mi-prefix')
```

### Cómo Crear un Template
```html
{% extends "base.html" %}

{% block title %}Mi Título - SIGE{% endblock %}

{% block content %}
<div class="container-fluid px-4">
    <!-- Header -->
    <div class="d-flex justify-content-between align-items-center mb-4 animate-in">
        <div>
            <h1 class="h3 mb-1 fw-bold text-dark"><i class="bi bi-icon me-2"></i>Título</h1>
            <p class="text-muted mb-0">Subtítulo</p>
        </div>
    </div>

    <!-- Content -->
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('#miTabla').DataTable({
        language: { url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json' },
        pageLength: 15,
        order: [[0, 'asc']]
    });
});
</script>
{% endblock %}
```

### Cómo Crear un Test
```python
# test_mi_modulo.py
import sys
sys.path.insert(0, '.')

from app import create_app
from extensions import db

app = create_app()
passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"  [PASS] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}")
        failed += 1

with app.app_context():
    print("=== Mi Módulo Tests ===")
    test("Ruta existe", True)
    # ... más tests

print(f"\nResultados: {passed} passed, {failed} failed, {passed+failed} total")
```

---

## Próximos Pasos

### Pendientes de Baja Prioridad
| # | Tarea | Esfuerzo | Notas |
|---|-------|----------|-------|
| 1 | Sistema QR | Variable | Requiere integración con PROYECTO-LAB |
| 2 | Capa de servicios | Refactor | Extraer lógica de rutas a services/ |
| 3 | Tests con pytest | Variable | Framework de testing con cobertura |
| 4 | Upload foto/logo | 30 min | Implementar stubs con `pass` |
| 5 | Habilitar CSRF globalmente | 1h | Descomentar `csrf.init_app(app)` en app.py |
| 6 | AJAX CSRF en institutions_list.html | 30 min | Agregar header X-CSRFToken en $.ajax |
| 7 | Migraciones Alembic | 4h | Reemplazar scripts one-off por cadena de migraciones |

### Correcciones de Seguridad Aplicadas (Sesión 2026-04-13)
- 44 formularios POST recibieron `{{ csrf_token() }}` (login, password, users, institution, grades, observations, alerts, achievements)
- Rutas QR protegidas con `@login_required` (qr.py)
- Ruta `student_grades` protegida con `@role_required` (grades.py)
- SQL bug en `_get_teacher_subject_grades()` corregido: institution filter con subconsultas circulares reemplazado por JOIN Campus limpio
- SQL bug en `institution_metrics()` corregido: `.join(subquery())` invalido reemplazado por `.join(Campus)` directo
- Variable shadowing en `observations.py` corregido: `student_ids` renombrado a `institution_student_ids` + `stats_scope`
- Dead code en `pdf_generator.py` desactivado: `generate_certificate_pdf()` ahora lanza `NotImplementedError`

### Arquitectura Futura
- **Integración PROYECTO-LAB**: QR como identificación única, validación en tiempo real
- **Capa de servicios**: `services/grade_calculator.py`, `services/excel_handler.py`, etc.
- **Migraciones Alembic**: Reemplazar scripts one-off por cadena de migraciones
- **Tests con pytest**: Framework de testing con cobertura

---

## Notas para Futuras Sesiones

### ⚠️ Reglas OBLIGATORIAS
1. **Bootstrap 5**: NUNCA usar Tailwind CSS. El proyecto usa exclusivamente Bootstrap 5
2. **DataTables en español**: Siempre usar `language: { url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json' }`
3. **Agentes para tareas pesadas**: Un agente por módulo, con prompt detallado
4. **Crear test antes de commitear**: Cada módulo debe tener script de prueba
5. **NO commitear sin verificación**: El usuario debe aprobar antes de `git commit`
6. **Institution resolver**: Siempre usar `get_current_institution()` para filtrar datos
7. **Jerarquía de roles**: Admin NO puede crear/editar/eliminar otros admins
8. **Formularios**: Siempre mantener datos tras errores (`form_data` + `errors`)
9. **Relationships del modelo**: Verificar que existen antes de usar en templates
10. **CSRF**: Todos los forms POST deben tener `{{ csrf_token() }}`. Para AJAX usar header `X-CSRFToken`
11. **Decoradores**: Siempre `@login_required` + `@role_required` en rutas que modifican datos
12. **Testing**: Seguir pirámide en TESTING_STRATEGY.md (Linting → Estático → Runtime → Manual)
13. **Responder en español**: Siempre

### 🎨 Paleta de Colores
| Uso | Color | Clase Bootstrap |
|-----|-------|----------------|
| Primario | #667eea | `text-primary` / `bg-primary` |
| Éxito | #198754 | `text-success` / `bg-success` |
| Advertencia | #ffc107 | `text-warning` / `bg-warning` |
| Peligro | #dc3545 | `text-danger` / `bg-danger` |
| Info | #0dcaf0 | `text-info` / `bg-info` |
| Secundario | #6c757d | `text-muted` / `bg-secondary` |

### 🚫 Errores Comunes a Evitar
| Error | Causa | Solución |
|-------|-------|----------|
| `student.campus` retorna None | Faltaba relationship en modelo | Agregado `campus = db.relationship('Campus')` |
| `student.grade` retorna None | Backref ya existía en Grade | No crear relationship duplicado |
| `BuildError: students.student_profile` | Endpoint no existe | Usar `students.profile` |
| `DetachedInstanceError` | Objeto fuera de session | Usar `db.session.get(Model, id)` |
| Estudiantes no aparecen en lista | `institution_id` mismatch | Asignar `institution_id` al crear User Y AcademicStudent |
| Tailwind sin estilos | Proyecto usa Bootstrap 5 | Convertir clases Tailwind a Bootstrap |

---

**Generado**: 2026-04-12 | **Mantener actualizado en cada sesión**
**Última actualización**: 2026-04-22 (Fase 0 completada: summary, risk_students y parent dashboard implementados)
