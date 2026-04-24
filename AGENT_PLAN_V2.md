# AGENT PLAN V2 - SIGE Development Roadmap

## Sistema Integral de Gesti\u00f3n Escolar

> **Estado actual**: ~99% implementado | **Stack**: Python 3 + Flask + Bootstrap 5 + Chart.js + DataTables + SQLite
> **Fecha de creaci\u00f3n**: 2026-04-12
> **\u00daltima actualizaci\u00f3n**: 2026-04-24
> **Documento autocontenido**: Sirve como gu\u00eda completa para cualquier agente futuro

---

## Tabla de Contenidos

| Secci\u00f3n | Descripci\u00f3n |
|-----------|-------------|
| [Contexto del Proyecto](#contexto-del-proyecto) | Arquitectura, modelos, blueprints existentes |
| [Reglas Universales](#reglas-universales) | Normas obligatorias para TODOS los agentes |
| [Fase 0](#fase-0---completar-placeholders-inmediato) | Templates placeholder (3 tareas f\u00e1ciles) |
| [Fase 1](#fase-1---calidad-y-robustez-corto-plazo) | Capa de servicios + Tests + Migraciones (COMPLETO) |
| [Fase 2](#fase-2---reingenier\u00eda-acad\u00e9mica-y-anal\u00edtica) | Multi-jornada, Horarios e Inteligencia (COMPLETO) |
| [Fase 3](#fase-3---integraci\u00f3n-qr-mediano-plazo) | Sistema QR completo con PROYECTO-LAB (COMPLETO) |
| [Fase 4](#fase-4---producci\u00f3n-y-escalabilidad) | Deploy, optimizaci\u00f3n, monitoreo |
| [Ap\u00e9ndice](#ap\u00e9ndice---referencia-r\u00e1pida) | Patrones de c\u00f3digo, paleta de colores, errores comunes |

---

## Contexto del Proyecto

### Lo que YA est\u00e1 completo (NO tocar)

| M\u00f3dulo | Progreso | Estado |
|----------|----------|--------|
| Autenticaci\u00f3n | 100% | Login, logout, profile, password, force change |
| Dashboards por rol | 100% | 7 dashboards (root, admin, coordinator, teacher, student, parent, viewer) |
| Gesti\u00f3n institucional | 100% | CRUD instituci\u00f3n, sedes, grados, asignaturas, periodos, criterios |
| Gesti\u00f3n de usuarios | 100% | CRUD + Excel + permisos + usernames incrementales |
| Gesti\u00f3n de estudiantes | 100% | CRUD + Excel + perfiles incompletos visibles |
| Sistema de notas | 100% | Resumen, finales, anuales y anal\u00edtica longitudinal |
| Asistencia | 100% | Registro, historial, resumen grupal, export CSV |
| Observaciones | 100% | CRUD, historial, notificaci\u00f3n, quick form |
| Boletines PDF | 90% | Generaci\u00f3n, PDF, historial. Pendiente WeasyPrint en Windows |
| M\u00e9tricas | 100% | Dashboards, heatmap, risk_students y ANAL\u00cdTICA IA |
| Alertas tempranas | 95% | Motor 6 reglas, panel, resoluci\u00f3n |
| Logros/Gamificaci\u00f3n | 95% | Auto-award 7 logros, cat\u00e1logo, leaderboard |
| Portal acudientes | 100% | Dashboard avanzado, notas, asistencia, observaciones |
| Horarios y Matr\u00edcula| 100% | Generaci\u00f3n inteligente, Multi-jornada, Intensidad horaria |

### Estructura del proyecto (archivos clave)

```
sistema_escolar/
\u251c\u2500\u2500 app.py                          # Application factory
\u251c\u2500\u2500 config.py                       # Configuraci\u00f3n multi-entorno
\u251c\u2500\u2500 extensions.py                   # Extensiones Flask centralizadas
\u251c\u2500\u2500 init_db.py                      # Inicializaci\u00f3n BD + seed data
\u251c\u2500\u2500
\u251c\u2500\u2500 models/                         # 9 archivos, ~20 tablas
\u2502   \u251c\u2500\u2500 user.py                     # User (auth + 7 roles), ParentStudent
\u2502   \u251c\u2500\u2500 institution.py              # Institution, Campus, Grade, Subject
\u2502   \u251c\u2500\u2500 academic.py                 # SubjectGrade, AcademicStudent, ParentStudent
\u2502   \u251c\u2500\u2500 grading.py                  # AcademicPeriod, GradeCriteria, GradeRecord, FinalGrade, AnnualGrade
\u2502   \u251c\u2500\u2500 attendance.py               # Attendance
\u2502   \u251c\u2500\u2500 observation.py              # Observation
\u2502   \u251c\u2500\u2500 report.py                   # ReportCard, ReportCardObservation
\u2502   \u251c\u2500\u2500 achievement.py              # Achievement, StudentAchievement
\u2502   \u2514\u2500\u2500 alert.py                    # Alert
\u2502
\u251c\u2500\u2500 routes/                         # 14 blueprints registrados en app.py
\u2502   \u251c\u2500\u2500 auth.py                     # Login, logout, profile, password
\u2502   \u251c\u2500\u2500 dashboard.py                # 7 dashboards por rol
\u2502   \u251c\u2500\u2500 institution.py              # CRUD institucional completo
\u2502   \u251c\u2500\u2500 students.py                 # CRUD estudiantes + Excel upload
\u2502   \u251c\u2500\u2500 users.py                    # CRUD usuarios + permisos
\u2502   \u251c\u2500\u2500 grades.py                   # Sistema de notas (planilla, lock, finales, anuales)
\u2502   \u251c\u2500\u2500 report_cards.py             # Boletines PDF
\u2502   \u251c\u2500\u2500 attendance.py               # Asistencia diaria
\u2502   \u251c\u2500\u2500 observations.py             # Observaciones comportamiento
\u2502   \u251c\u2500\u2500 metrics.py                  # M\u00e9tricas profesor + institucionales
\u2502   \u251c\u2500\u2500 alerts.py                   # Sistema alertas tempranas
\u2502   \u251c\u2500\u2500 achievements.py             # Logros/gamificaci\u00f3n
\u2502   \u251c\u2500\u2500 parent.py                   # Portal de acudientes
\u2502   \u2514\u2500\u2500 qr.py                       # Acceso QR (placeholder - solo 2 rutas sin decoradores)
\u2502
\u251c\u2500\u2500 utils/                          # 12 utilidades
\u2502   \u251c\u2500\u2500 decorators.py               # @role_required, @login_required, @institution_required
\u2502   \u251c\u2500\u2500 validators.py               # Validaci\u00f3n documento, email, notas
\u2502   \u251c\u2500\u2500 pdf_generator.py            # Generaci\u00f3n PDF (WeasyPrint)
\u2502   \u251c\u2500\u2500 charts.py                   # Configuraci\u00f3n Chart.js
\u2502   \u251c\u2500\u2500 institution_resolver.py     # get_current_institution()
\u2502   \u251c\u2500\u2500 username_generator.py       # Usernames incrementales
\u2502   \u251c\u2500\u2500 alert_engine.py             # Motor 6 reglas de alerta
\u2502   \u251c\u2500\u2500 achievement_engine.py       # Motor auto-award 7 logros
\u2502   \u2514\u2500\u2500 template_helpers.py         # Helpers Jinja2
\u2502
\u251c\u2500\u2500 templates/                      # ~87 templates HTML
\u2502   \u251c\u2500\u2500 base.html                   # Layout base con sidebar din\u00e1mico
\u2502   \u251c\u2500\u2500 grades/summary.html         # PLACEHOLDER - ruta funciona con datos
\u2502   \u251c\u2500\u2500 metrics/risk_students.html  # PLACEHOLDER - ruta existe sin decoradores
\u2502   \u251c\u2500\u2500 qr/my_qr.html              # PLACEHOLDER
\u2502   \u251c\u2500\u2500 qr/validate.html           # PLACEHOLDER
\u2502   \u2514\u2500\u2500 parent/dashboard.html      # Funcional pero minimal
\u2502
\u251c\u2500\u2500 static/
\u2502   \u251c\u2500\u2500 css/main.css
\u2502   \u251c\u2500\u2500 css/sige-styles.css         # +1500 l\u00edneas de estilos profesionales
\u2502   \u251c\u2500\u2500 js/main.js                  # DataTables init, sidebar logic
\u2502   \u2514\u2500\u2500 js/form-validation.js       # Validaci\u00f3n formularios en tiempo real
\u2502
\u2514\u2500\u2500 test_*.py                       # 12 scripts de prueba sueltos (NO pytest)
```

### Jerarqu\u00eda de Roles

```
root (super-admin global)
  \u2514\u2500\u2500 admin (instituci\u00f3n)
        \u251c\u2500\u2500 coordinator (acad\u00e9mico)
        \u251c\u2500\u2500 teacher (grupo/materia asignada)
        \u251c\u2500\u2500 student (consulta propia)
        \u251c\u2500\u2500 parent (acudiente de estudiantes vinculados)
        \u2514\u2500\u2500 viewer (solo lectura)
```

### Escala de Calificaci\u00f3n

| Rango | Desempe\u00f1o | Estado |
|-------|-----------|--------|
| 4.6 - 5.0 | Superior | Ganada |
| 4.0 - 4.5 | Alto | Ganada |
| 3.0 - 3.9 | B\u00e1sico | Ganada |
| 1.0 - 2.9 | Bajo | Perdida |

### Documentos de Referencia Obligatoria

Cualquier agente DEBE leer estos archivos antes de empezar:
1. `DOCUMENTATION.md` - Contexto t\u00e9cnico completo
2. `PROGRESS.md` - Estado actual y \u00faltimos cambios
3. `AGENT_PLAN_V2.md` - Este plan

---

## Reglas Universales

> **Estas reglas aplican a TODOS los agentes de TODAS las fases. Violaciones = rehacer.**

### Reglas de Estilo y Frontend

| # | Regla | Detalle |
|---|-------|---------|
| 1 | **Bootstrap 5 EXCLUSIVO** | NUNCA usar Tailwind CSS. El proyecto usa exclusivamente Bootstrap 5 + `sige-styles.css` |
| 2 | **DataTables en espa\u00f1ol** | Siempre: `language: { url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json' }` |
| 3 | **Paleta de colores** | Primary `#667eea`, Success `#198754`, Warning `#ffc107`, Danger `#dc3545`, Info `#0dcaf0` |
| 4 | **Cards** | `border-radius: 15px`, `shadow-sm`, hover: `translateY(-5px)` |
| 5 | **Animaciones** | `fadeInUp` con delays escalonados `.delay-1`, `.delay-2`, `.delay-3` |
| 6 | **Iconos** | Bootstrap Icons (`bi bi-*`) con `me-1` o `me-2` |
| 7 | **Espaciado** | Generoso: `p-4`, `g-4`, `mb-4` |

### Reglas de Backend

| # | Regla | Detalle |
|---|-------|---------|
| 8 | **Institution resolver** | Siempre usar `get_current_institution()` para filtrar datos por instituci\u00f3n |
| 9 | **Decoradores** | Siempre `@login_required` + `@role_required(*roles)` en todas las rutas protegidas |
| 10 | **Seguridad de datos** | NUNCA confiar en IDs del cliente. Verificar ownership antes de editar/eliminar |
| 11 | **Formularios** | Siempre retornar `form_data` + `errors` al validar. NUNCA borrar datos del usuario |
| 12 | **Flash messages** | Con emojis: \u2705 \u00e9xito, \u26a0\ufe0f advertencia, \u274c error |
| 13 | **PRG Pattern** | Redirect despu\u00e9s de POST |

### Reglas de Trabajo

| # | Regla | Detalle |
|---|-------|---------|
| 14 | **Tests antes de commit** | Cada m\u00f3dulo debe tener script de prueba que verifique funcionalidad |
| 15 | **NO commitear autom\u00e1ticamente** | El usuario debe aprobar antes de `git commit` |
| 16 | **Un agente por m\u00f3dulo** | No mezclar cambios de m\u00faltiples m\u00f3dulos en una sola ejecuci\u00f3n |
| 17 | **Leer documentaci\u00f3n primero** | Antes de tocar c\u00f3digo, leer `DOCUMENTATION.md` y `PROGRESS.md` |

---

## FASE 0 - Completar Placeholders (Inmediato)

**Prioridad**: \ud83d\udd34 ALTA
**Estimaci\u00f3n**: 3 agentes, ~2-3 horas total
**Dependencias**: Ninguna - son tareas independientes
**Complejidad**: Baja - las rutas ya existen y proveen datos

---

### Agente 0.1: Template `grades/summary.html`

**Contexto**: La ruta `/grades/summary/<sg_id>/<period_id>` ya existe en `routes/grades.py` (l\u00ednea 988) y provee todos los datos necesarios. El template actual es un placeholder m\u00ednimo.

**Archivos que el agente DEBE leer**:
- `routes/grades.py` (funci\u00f3n `grade_summary`, l\u00edneas 988-1120) - para entender las variables que se pasan al template
- `templates/grades/final_view.html` - referencia de estilo para vistas de notas
- `templates/grades/annual_view.html` - referencia de estructura de tabla
- `static/css/sige-styles.css` - estilos existentes a reutilizar
- `DOCUMENTATION.md` - sistema de calificaci\u00f3n

**Variables disponibles en el template** (prove\u00eddas por la ruta):
```python
{
    'subject_grade': SubjectGrade,     # Asignatura-Grado
    'grade': Grade,                     # Grado
    'subject': Subject,                 # Materia
    'period': AcademicPeriod,           # Per\u00edodo
    'students': list[AcademicStudent],  # Estudiantes activos del grado
    'student_grades': dict,             # {student_id: FinalGrade}
    'final_grades': list[FinalGrade],   # Todas las notas finales
    'average': float,                   # Promedio general
    'max_score': float,                 # Nota m\u00e1xima
    'min_score': float,                 # Nota m\u00ednima
    'median': float,                    # Mediana
    'std_dev': float,                   # Desviaci\u00f3n est\u00e1ndar
    'passed': int,                      # Count aprobados
    'failed': int,                      # Count reprobados
    'not_evaluated': int,               # Count no evaluados
    'pass_rate': float,                 # Tasa aprobaci\u00f3n (%)
    'fail_rate': float,                 # Tasa reprobaci\u00f3n (%)
    'distribution': dict,               # {'1.0-1.9': n, '2.0-2.9': n, ...}
    'criteria_stats': list,             # [{criterion, average, count}, ...]
    'MIN_GRADE': 1.0,
    'MAX_GRADE': 5.0,
    'PASSING_GRADE': 3.0
}
```

**Especificaciones t\u00e9cnicas**:

1. **Header de p\u00e1gina**: T\u00edtulo con "{Materia} - {Grado} - {Periodo}", bot\u00f3n volver a planilla de notas
2. **Stat Cards** (4 cards en fila):
   - Promedio General (n\u00famero grande con color seg\u00fan rango)
   - Tasa de Aprobaci\u00f3n (barra de progreso circular o lineal)
   - Nota M\u00e1xima / Nota M\u00ednima
   - Estudiantes evaluados vs totales
3. **Tabla resumen Students \u00d7 Criteria**:
   - Filas: cada estudiante (ordenados por apellido)
   - Columnas: cada criterio de evaluaci\u00f3n + Nota Final + Estado
   - Celdas con badges de color seg\u00fan rendimiento
   - Fila de promedios por columna al final
4. **Gr\u00e1fico de distribuci\u00f3n** (Chart.js bar chart):
   - Usar `distribution` dict para mostrar barras por rango
   - Colores: rojo (<2.0), naranja (2.0-2.9), amarillo (3.0-3.9), verde (4.0-4.9), azul (5.0)
5. **Estad\u00edsticas por criterio**:
   - Tabla peque\u00f1a con cada criterio, su promedio y cantidad de estudiantes evaluados
   - Barras de progreso horizontales para visualizaci\u00f3n r\u00e1pida
6. **Empty state**: Si no hay notas, mostrar mensaje con bot\u00f3n para ir a la planilla

**Estructura HTML esperada**:
```html
{% extends "base.html" %}
{% block title %}Resumen - {{ subject.name }} - {{ grade.name }}{% endblock %}

{% block extra_css %}
<style>
    /* Cards con estilo SIGE */
    .stat-card { border: none; border-radius: 15px; }
    .stat-card:hover { transform: translateY(-5px); }
    /* Tabla de resumen */
    .summary-table th { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
    /* Barras de progreso */
    .progress-bar-custom { background: linear-gradient(90deg, #667eea, #764ba2); }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid px-4">
    <!-- Header con breadcrumb y bot\u00f3n volver -->
    <!-- Stat Cards (4 en fila) -->
    <!-- Tabla resumen students \u00d7 criteria -->
    <!-- Gr\u00e1fico de distribuci\u00f3n (Chart.js) -->
    <!-- Estad\u00edsticas por criterio con barras -->
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    $('#summaryTable').DataTable({
        language: { url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json' },
        pageLength: 15,
        order: [[1, 'asc']]
    });
    // Chart.js distribution bar chart
});
</script>
{% endblock %}
```

**Script de prueba**: Crear `test_phase0_summary.py` que:
1. Verifique que el template existe y se renderiza sin errores
2. Verifique que las stat cards muestran los datos correctos
3. Verifique que la tabla tiene filas por estudiante
4. Verifique que el gr\u00e1fico Chart.js se inicializa

**C\u00f3mo verificar**:
```bash
.venv\Scripts\python.exe app.py
# Navegar a /grades/input \u2192 seleccionar grado/materia/periodo \u2192 clic en "Resumen"
# Verificar: stat cards visibles, tabla con datos, gr\u00e1fico renderizado
```

---

### Agente 0.2: Template `metrics/risk_students.html`

**Contexto**: Existe una funci\u00f3n `_get_risk_students()` en `routes/metrics.py` (l\u00ednea 132) con l\u00f3gica completa. La ruta `/metrics/risk-students` existe (l\u00ednea 1356) pero:
- **PROBLEMA**: No tiene decoradores `@login_required` ni `@role_required`
- **PROBLEMA**: No pasa datos al template
- El template es un placeholder m\u00ednimo

**Archivos que el agente DEBE leer**:
- `routes/metrics.py` (funci\u00f3n `_get_risk_students`, l\u00edneas 132-202) - l\u00f3gica de riesgo
- `routes/metrics.py` (funci\u00f3n `teacher_metrics`, l\u00edneas 461-520) - referencia de c\u00f3mo se usa risk_students
- `templates/metrics/teacher.html` - referencia de estilo
- `templates/alerts/list.html` - referencia de tabla con filtros
- `DOCUMENTATION.md` - motor de alertas

**Cambios requeridos en la ruta** (`routes/metrics.py`):

La ruta actual (l\u00ednea 1356-1359) debe modificarse para:
```python
@metrics_bp.route('/risk-students')
@login_required
@role_required('root', 'admin', 'coordinator', 'teacher')
def risk_students():
    """View students at risk with full data."""
    institution = get_current_institution()
    if not institution:
        flash('Seleccione instituci\u00f3n primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    # Usar la funci\u00f3n existente _get_risk_students
    threshold = request.args.get('threshold', 3.0, type=float)
    teacher_id = current_user.id if current_user.has_role('teacher') else None

    risk_list = _get_risk_students(teacher_id, institution, threshold)

    # Estad\u00edsticas
    total_at_risk = len(risk_list)
    high_risk = sum(1 for r in risk_list if r['avg_score'] < 2.0)
    medium_risk = sum(1 for r in risk_list if 2.0 <= r['avg_score'] < 3.0)

    return render_template('metrics/risk_students.html',
                           risk_students=risk_list,
                           total_at_risk=total_at_risk,
                           high_risk=high_risk,
                           medium_risk=medium_risk,
                           threshold=threshold)
```

**Especificaciones t\u00e9cnicas del template**:

1. **Header**: "Estudiantes en Riesgo" con subtitulo explicativo, bot\u00f3n volver
2. **Filtros**:
   - Select de umbral de riesgo (1.0, 1.5, 2.0, 2.5, 3.0) - default 3.0
   - Bot\u00f3n "Aplicar filtro"
3. **Stat Cards** (3 cards):
   - Total estudiantes en riesgo
   - Riesgo Alto (promedio < 2.0) - card rojo
   - Riesgo Medio (promedio 2.0-2.9) - card naranja
4. **Tabla de estudiantes en riesgo** (DataTables):
   - Columnas: #, Estudiante, Grado, Materia, Promedio, Estado, Acciones
   - Promedio con badge de color (rojo <2.0, naranja 2.0-2.9)
   - Acci\u00f3n: enlace al perfil del estudiante
5. **Gr\u00e1fico de distribuci\u00f3n** (Chart.js doughnut):
   - Porcentaje riesgo alto vs medio
6. **Empty state**: Si no hay estudiantes en riesgo, mostrar \u00edcono check verde + mensaje positivo

**Script de prueba**: Crear `test_phase0_risk.py` que:
1. Verifique que la ruta tiene decoradores de autenticaci\u00f3n
2. Verifique que el template renderiza con datos
3. Verifique que los filtros funcionan
4. Verifique que las estad\u00edsticas son correctas

**C\u00f3mo verificar**:
```bash
.venv\Scripts\python.exe app.py
# Como teacher: /metrics/risk-students
# Como admin/coordinator: /metrics/risk-students
# Verificar: tabla con estudiantes, filtros, gr\u00e1fico
```

---

### Agente 0.3: Dashboard de Acudiente Mejorado

**Contexto**: El template `templates/parent/dashboard.html` ya es funcional y tiene buen estilo (fue implementado al 95%). Lo que falta es hacerlo m\u00e1s completo visualmente.

**Archivos que el agente DEBE leer**:
- `templates/parent/dashboard.html` - estado actual (ya tiene buen base)
- `routes/parent.py` - para entender datos disponibles
- `templates/dashboard/student.html` - referencia de dashboard completo
- `templates/dashboard/teacher.html` - referencia de stat cards con gr\u00e1ficos

**Mejoras requeridas**:

1. **Header mejorado**: Bienvenida personalizada con nombre del acudiente
2. **Student selector**: Si el acudiente tiene m\u00faltiples hijos, tabs o cards horizontales para seleccionar
3. **Stat Cards por estudiante** (agregar a los existentes):
   - Promedio general actual (ya existe)
   - Asistencia \u00faltimos 30 d\u00edas (ya existe)
   - **NUEVO**: Observaciones pendientes (count)
   - **NUEVO**: Alertas activas (count con badge)
   - **NUEVO**: Pr\u00f3ximo periodo/evaluaci\u00f3n (si hay datos)
4. **Gr\u00e1fico de tendencia de notas** (Chart.js line chart):
   - Eje X: periodos acad\u00e9micos
   - Eje Y: promedio por periodo
   - L\u00ednea de umbral en 3.0 (roja)
5. **Gr\u00e1fico de asistencia** (Chart.js bar chart):
   - \u00daltimos 30 d\u00edas: presente vs ausente
   - Colores: verde = presente, rojo = ausente
6. **Timeline de actividad reciente**:
   - \u00daltimas 5-10 actividades cronol\u00f3gicas
   - Cada item: icono + fecha + descripci\u00f3n corta
   - Tipos: nueva nota, nueva observaci\u00f3n, alerta, logro, bolet\u00edn
   - Colores por tipo
7. **Secci\u00f3n de acciones r\u00e1pidas**: Botones grandes para ir a notas, asistencia, observaciones, boletines

**Script de prueba**: Crear `test_phase0_parent_dashboard.py` que:
1. Verifique que el dashboard renderiza sin errores
2. Verifique que los stat cards muestran datos
3. Verifique que los gr\u00e1ficos Chart.js se inicializan
4. Verifique que el timeline muestra actividad

**C\u00f3mo verificar**:
```bash
.venv\Scripts\python.exe app.py
# Login como parent \u2192 verificar dashboard completo
```

---

## FASE 1 - Calidad y Robustez (Corto Plazo)

**Prioridad**: \ud83d\udfe0 MEDIA-ALTA
**Estimaci\u00f3n**: 6 agentes, ~8-12 horas total
**Dependencias**: Fase 0 completada
**Complejidad**: Media - requiere refactorizaci\u00f3n cuidadosa

---

### Agente 1.1: Capa de Servicios - `services/grade_calculator.py`

**Contexto**: La l\u00f3gica de c\u00e1lculo de notas est\u00e1 dispersa en `routes/grades.py`, especialmente la funci\u00f3n `_calculate_final_grade()` (l\u00ednea 1126) y c\u00e1lculos inline en m\u00faltiples rutas.

**Archivos que el agente DEBE leer**:
- `routes/grades.py` - toda la l\u00f3gica de c\u00e1lculo a extraer
- `models/grading.py` - modelos GradeRecord, FinalGrade, AnnualGrade, GradeCriteria
- `DOCUMENTATION.md` - sistema de calificaci\u00f3n (f\u00f3rmulas)

**Archivos a crear**:
- `services/__init__.py`
- `services/grade_calculator.py`

**Especificaciones t\u00e9cnicas**:

```python
# services/grade_calculator.py
class GradeCalculator:
    """
    Servicio centralizado para c\u00e1lculos de calificaciones.
    Escala: 1.0 - 5.0, aprobaci\u00f3n: 3.0
    """

    MIN_GRADE = 1.0
    MAX_GRADE = 5.0
    PASSING_GRADE = 3.0

    @staticmethod
    def calculate_final_grade(student_id, sg_id, period_id, criteria):
        """
        Calcula nota final ponderada para un estudiante.
        Formula: sum(score * weight/100) para cada criterio.
        Retorna float o None si datos insuficientes.
        """

    @staticmethod
    def calculate_annual_grade(student_id, sg_id, academic_year):
        """
        Calcula nota anual: promedio de notas finales de los 4 periodos.
        Retorna dict con annual_score, status, period_breakdown.
        """

    @staticmethod
    def get_grade_status(score):
        """Retorna 'ganada' o 'perdida' seg\u00fan score."""

    @staticmethod
    def get_performance_level(score):
        """Retorna: 'Superior', 'Alto', 'B\u00e1sico', 'Bajo'."""

    @staticmethod
    def calculate_statistics(scores):
        """
        Calcula estad\u00edsticas completas de una lista de notas.
        Retorna: average, max, min, median, std_dev, pass_rate, fail_rate.
        """

    @staticmethod
    def get_distribution(scores):
        """
        Distribuci\u00f3n por rangos: 1.0-1.9, 2.0-2.9, 3.0-3.9, 4.0-4.9, 5.0
        """
```

**Refactor requerido**:
1. Extraer `_calculate_final_grade()` de `routes/grades.py` \u2192 `GradeCalculator.calculate_final_grade()`
2. Reemplazar todas las llamadas a la funci\u00f3n old
3. Actualizar imports en `routes/grades.py`
4. Los c\u00e1lculos inline en `grade_summary` y `final_view` deben usar `GradeCalculator.calculate_statistics()`

**Script de prueba**: Crear `tests/test_grade_calculator.py` con:
- Test de c\u00e1lculo con datos v\u00e1lidos
- Test de c\u00e1lculo con datos incompletos
- Test de estad\u00edsticas
- Test de distribuci\u00f3n
- Test de estados y niveles

---

### Agente 1.2: Capa de Servicios - `services/excel_handler.py`

**Contexto**: El manejo de archivos Excel est\u00e1 inline en `routes/students.py` (upload) y `routes/grades.py` (upload masivo).

**Archivos a leer**:
- `routes/students.py` - l\u00f3gica de upload de estudiantes
- `routes/grades.py` - l\u00f3gica de upload masivo de notas
- `routes/users.py` - si hay upload de usuarios

**Archivos a crear**:
- `services/excel_handler.py`

**Especificaciones t\u00e9cnicas**:

```python
# services/excel_handler.py
class ExcelHandler:
    """Servicio centralizado para lectura/validaci\u00f3n de archivos Excel."""

    @staticmethod
    def read_students_upload(file_path):
        """
        Lee archivo Excel de carga de estudiantes.
        Retorna: (students_list, errors_list)
        Valida: documento, nombre, grado, campos obligatorios.
        """

    @staticmethod
    def read_grades_upload(file_path, subject_grade_id, period_id):
        """
        Lee archivo Excel de carga masiva de notas.
        Retorna: (grades_list, errors_list)
        Valula: estudiante existe, nota en rango 1.0-5.0.
        """

    @staticmethod
    def validate_document_number(doc):
        """Valida formato de n\u00famero de documento."""

    @staticmethod
    def export_to_excel(data_dict, filename):
        """
        Exporta diccionario de datos a archivo Excel multi-hoja.
        Usado por metrics/export.
        """
```

**Script de prueba**: Crear `tests/test_excel_handler.py` con:
- Test de lectura de estudiantes v\u00e1lido
- Test de lectura con errores
- Test de lectura de notas
- Test de exportaci\u00f3n

---

### Agente 1.3: Capa de Servicios - `services/report_card_service.py`

**Contexto**: La generaci\u00f3n de boletines est\u00e1 en `routes/report_cards.py`. Extraer a servicio para permitir generaci\u00f3n program\u00e1tica (ej: desde alertas autom\u00e1ticas).

**Archivos a leer**:
- `routes/report_cards.py` - toda la l\u00f3gica de generaci\u00f3n
- `utils/pdf_generator.py` - generador PDF existente
- `models/report.py` - ReportCard, ReportCardObservation

**Archivos a crear**:
- `services/report_card_service.py`

**Especificaciones t\u00e9cnicas**:

```python
# services/report_card_service.py
class ReportCardService:
    """Servicio para generaci\u00f3n y gesti\u00f3n de boletines."""

    def __init__(self, db_session, pdf_generator=None):
        self.db = db_session
        self.pdf = pdf_generator

    def generate_single(self, student_id, period_id):
        """
        Genera bolet\u00edn individual para estudiante/periodo.
        Retorna: ReportCard creado o None si error.
        """

    def generate_bulk(self, grade_id, period_id):
        """
        Genera boletines para todo un grado/periodo.
        Retorna: dict con {created: int, errors: list}.
        """

    def get_student_history(self, student_id):
        """
        Historial completo de boletines del estudiante.
        """

    def mark_delivered(self, report_card_id):
        """Marca bolet\u00edn como entregado."""

    def get_pending_delivery(self, grade_id=None, period_id=None):
        """Lista boletines pendientes de entrega."""
```

**Script de prueba**: Crear `tests/test_report_card_service.py` con:
- Test de generaci\u00f3n individual
- Test de generaci\u00f3n masiva
- Test de historial
- Test de marcado como entregado

---

### Agente 1.4: Capa de Servicios - `services/student_service.py` + `services/metrics_service.py`

**Contexto**: CRUD de estudiantes en `routes/students.py` y c\u00e1lculos de m\u00e9tricas en `routes/metrics.py` deben extraerse.

**Archivos a crear**:
- `services/student_service.py`
- `services/metrics_service.py`

**Especificaciones t\u00e9cnicas - StudentService**:
```python
class StudentService:
    """Servicio para operaciones CRUD de estudiantes."""

    def create_student(self, data_dict):
        """Crea estudiante completo (User + AcademicStudent). Retorna estudiante o errores."""

    def update_student(self, student_id, data_dict):
        """Actualiza estudiante. Retorna estudiante actualizado o errores."""

    def delete_student(self, student_id):
        """Elimina estudiante (soft delete o hard con cascade)."""

    def get_student_profile(self, student_id):
        """Obtiene perfil acad\u00e9mico completo del estudiante."""

    def list_students(self, institution_id, grade_id=None, campus_id=None, status='activo'):
        """Lista estudiantes con filtros."""

    def upload_from_excel(self, file_path, institution_id):
        """Carga masiva desde Excel. Retorna {created: int, errors: list}."""

    def get_incomplete_profiles(self, institution_id):
        """Usuarios role=student sin AcademicStudent."""
```

**Especificaciones t\u00e9cnicas - MetricsService**:
```python
class MetricsService:
    """Servicio para c\u00e1lculos de m\u00e9tricas institucionales."""

    def get_teacher_metrics(self, teacher_id, institution):
        """M\u00e9tricas completas del profesor."""

    def get_institutional_metrics(self, institution):
        """KPIs institucionales completos."""

    def get_heatmap_data(self, institution):
        """Datos para mapa de calor Grado \u00d7 Materia."""

    def get_trends_data(self, institution, periods=None):
        """Tendencias hist\u00f3ricas."""

    def get_risk_students_list(self, institution, teacher_id=None, threshold=3.0):
        """Lista de estudiantes en riesgo."""

    def export_metrics_excel(self, institution):
        """Genera archivo Excel de m\u00e9tricas (5 hojas)."""
```

---

### Agente 1.5: Tests Unitarios con pytest

**Contexto**: Existen 12 scripts de prueba sueltos (`test_*.py` en ra\u00edz). Deben migrarse a estructura pytest profesional.

**Archivos a leer**:
- Todos los `test_*.py` existentes - para entender qu\u00e9 se prueba actualmente
- `app.py` - factory function `create_app()`
- `config.py` - configuraci\u00f3n de testing

**Estructura a crear**:
```
tests/
\u251c\u2500\u2500 __init__.py
\u251c\u2500\u2500 conftest.py             # Fixtures: app, client, db_session
\u251c\u2500\u2500 test_auth.py
\u251c\u2500\u2500 test_students.py
\u251c\u2500\u2500 test_grades.py
\u251c\u2500\u2500 test_attendance.py
\u251c\u2500\u2500 test_observations.py
\u251c\u2500\u2500 test_users.py
\u251c\u2500\u2500 test_institution.py
\u251c\u2500\u2500 test_report_cards.py
\u251c\u2500\u2500 test_metrics.py
\u251c\u2500\u2500 test_alerts.py
\u251c\u2500\u2500 test_achievements.py
\u2514\u2500\u2500 test_parent.py
```

**Especificaciones t\u00e9cnicas**:

1. **`conftest.py`** - Fixtures principales:
```python
import pytest
from app import create_app
from extensions import db

@pytest.fixture
def app():
    app = create_app('testing')  # Config de testing con BD en memoria
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    with app.app_context():
        db.create_all()
        yield db.session
        db.drop_all()

@pytest.fixture
def auth_client(client, db_session):
    """Client autenticado como root."""
    # Crear usuario root y login
    pass

@pytest.fixture
def admin_client(client, db_session):
    """Client autenticado como admin."""
    pass

@pytest.fixture
def teacher_client(client, db_session):
    """Client autenticado como teacher."""
    pass
```

2. **Cobertura objetivo**: 80%+ de las rutas y servicios
3. **Cada archivo de test** debe probar:
   - Rutas GET retornan 200
   - Rutas POST con datos v\u00e1lidos redirigen (302)
   - Rutas POST con datos inv\u00e1lidos retornan errores
   - Autenticaci\u00f3n requerida (401/302 para no auth)
   - Autorizaci\u00f3n por rol (403 para rol incorrecto)
   - Aislamiento de datos por instituci\u00f3n

4. **Ejemplo de estructura de test**:
```python
# tests/test_auth.py
class TestAuth:
    def test_login_page_loads(self, client):
        response = client.get('/login')
        assert response.status_code == 200

    def test_login_success(self, client, db_session):
        response = client.post('/login', data={
            'username': 'root', 'password': 'root123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_login_invalid(self, client):
        response = client.post('/login', data={
            'username': 'invalid', 'password': 'wrong'
        })
        # Verificar que muestra error

    def test_logout(self, auth_client):
        response = auth_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200

    def test_change_password(self, auth_client):
        response = auth_client.post('/change-password', data={
            'current_password': 'root123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_profile_access(self, auth_client):
        response = auth_client.get('/profile')
        assert response.status_code == 200
```

**Requisitos adicionales**:
- Agregar `pytest` y `pytest-cov` a `requirements.txt`
- Crear `pytest.ini` o `setup.cfg` con configuraci\u00f3n
- Configurar `config.py` con entorno `testing` (SQLite en memoria)
- Los tests deben correr con: `pytest tests/ -v --cov=routes --cov=services --cov=utils`

---

### Agente 1.6: Migraciones Alembic

**Contexto**: Existen scripts one-off de migraci\u00f3n (`migrate_*.py`). Deben reemplazarse por cadena de migraciones Alembic profesional.

**Archivos a leer**:
- Todos los `migrate_*.py` existentes - para entender migraciones ya aplicadas
- `models/*.py` - estado actual de todos los modelos
- `init_db.py` - c\u00f3mo se inicializa la BD actualmente

**Estructura a crear**:
```
migrations/                     # Generada por Flask-Migrate (ya instalado)
\u251c\u2500\u2500 versions/
\u2502   \u251c\u2500\u2500 001_initial_schema.py
\u2502   \u251c\u2500\u2500 002_add_multi_institution.py
\u2502   \u251c\u2500\u2500 003_add_is_main_campus.py
\u2502   \u251c\u2500\u2500 004_add_campus_created_at.py
\u2502   \u2514\u2500\u2500 ...
```

**Especificaciones t\u00e9cnicas**:

1. **Inicializar Flask-Migrate** (ya est\u00e1 en requirements.txt):
```python
# app.py - ya deber\u00eda estar configurado
from flask_migrate import Migrate
migrate = Migrate(app, db)
```

2. **Crear migraci\u00f3n inicial desde BD actual**:
```bash
flask db migrate -m "initial schema"
```

3. **Generar migraciones para cada script one-off existente**:
   - `migrate_multi_institution.py` \u2192 migraci\u00f3n Alembic
   - `migrate_add_is_main_campus.py` \u2192 migraci\u00f3n Alembic
   - `migrate_add_campus_created_at.py` \u2192 migraci\u00f3n Alembic

4. **Verificar que `flask db upgrade` funciona desde cero**

5. **Crear script de verificaci\u00f3n**: `test_migrations.py` que:
   - Crea BD vac\u00eda
   - Ejecuta todas las migraciones
   - Verifica que todas las tablas existen
   - Verifica relaciones entre tablas

---

## FASE 2 - Integraci\u00f3n QR (Mediano Plazo)

**Prioridad**: \ud83d\udfe1 MEDIA
**Estimaci\u00f3n**: 3 agentes, ~6-8 horas total
**Dependencias**: Fase 0 completada (los templates placeholder se convierten en funcionales)
**Complejidad**: Media - integraci\u00f3n con PROYECTO-LAB

### Contexto QR

El proyecto tiene un m\u00f3dulo `routes/qr.py` con 2 rutas placeholder sin decoradores de autenticaci\u00f3n. Las librer\u00edas necesarias ya est\u00e1n en `requirements.txt`: `qrcode==8.0` y `Pillow>=11.0.0`.

---

### Agente 2.1: Generaci\u00f3n y Modelo QR

**Archivos a leer**:
- `routes/qr.py` - rutas placeholder actuales
- `templates/qr/my_qr.html` - template placeholder
- `models/user.py` - modelo User al que vincular QR
- `requirements.txt` - confirmar qrcode y Pillow instalados

**Archivos a crear**:
- `models/qr_access.py` - modelo nuevo
- `services/qr_service.py` - servicio de generaci\u00f3n/validaci\u00f3n

**Modelo nuevo** (`models/qr_access.py`):
```python
class QRTokens(db.Model):
    __tablename__ = 'qr_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    qr_image_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    use_count = db.Column(db.Integer, default=0)

    # Relaciones
    user = db.relationship('User', backref=db.backref('qr_tokens', lazy=True))
```

**Especificaciones t\u00e9cnicas**:

1. **Generaci\u00f3n de QR**:
   - Cada usuario puede tener un QR \u00fanico
   - El QR contiene un token UUID4 codificado
   - El QR es descargable como PNG
   - Opci\u00f3n de regenerar QR (invalida anterior)

2. **Template `qr/my_qr.html`**:
   - Mostrar QR del usuario actual
   - Bot\u00f3n "Descargar QR" (PNG)
   - Bot\u00f3n "Regenerar QR" (con confirmaci\u00f3n)
   - Informaci\u00f3n: fecha creaci\u00f3n, veces usado, \u00faltimo uso
   - Instrucciones de uso para el acudiente/estudiante

3. **Ruta `GET /qr/my-qr`** (modificar existente):
   - Agregar `@login_required`
   - Generar QR si no existe
   - Renderizar template con QR

4. **Ruta `POST /qr/regenerate`**:
   - Invalida QR actual
   - Genera nuevo token y QR
   - Redirect a `/qr/my-qr`

5. **Ruta `GET /qr/download/<token>`**:
   - Genera PNG del QR al vuelo
   - Retorna archivo para descarga

**Servicio QR** (`services/qr_service.py`):
```python
class QRService:
    @staticmethod
    def generate_qr_token(user_id):
        """Genera nuevo token QR para usuario."""

    @staticmethod
    def get_user_qr(user_id):
        """Obtiene QR activo del usuario."""

    @staticmethod
    def generate_qr_image(token, filepath):
        """Genera imagen PNG del QR usando qrcode library."""

    @staticmethod
    def regenerate_qr(user_id):
        """Regenera QR invalidando el anterior."""
```

**Script de prueba**: `test_phase2_qr_generation.py`

---

### Agente 2.2: Validaci\u00f3n QR

**Archivos a leer**:
- `routes/qr.py` - ruta `qr_validate` placeholder
- `templates/qr/validate.html` - template placeholder
- `models/qr_access.py` - modelo creado por Agente 2.1

**Especificaciones t\u00e9cnicas**:

1. **Endpoint `POST /qr/validate`**:
   - Recibe token QR (desde escaneo)
   - Valida token contra base de datos
   - Verifica: token existe, est\u00e1 activo, no expir\u00f3
   - Retorna JSON con resultado + info del usuario
   - Actualiza `last_used_at` y `use_count`

```python
@qr_bp.route('/validate', methods=['POST'])
def qr_validate():
    """
    Valida c\u00f3digo QR.
    Input: JSON { "token": "uuid..." }
    Output: JSON { "valid": bool, "user": {...}, "message": str }
    """
```

2. **Template `qr/validate.html`** - Dashboard de validaci\u00f3n:
   - **Dos modos**:
     - **Manual**: Input para pegar token manualmente
     - **Scanner**: Si el navegador soporta, usa c\u00e1mara para escanear (html5-qrcode library)
   - **Resultado**: Card con info del usuario si v\u00e1lido
   - **Historial**: Tabla de \u00faltimas validaciones del d\u00eda
   - **Solo accesible por**: admin, coordinator

3. **Endpoint `GET /qr/validate`** (modificar existente):
   - Agregar `@login_required`
   - `@role_required('admin', 'coordinator')`
   - Renderizar dashboard de validaci\u00f3n con historial

4. **Endpoint `GET /qr/history`**:
   - Historial completo de accesos QR
   - Filtros por fecha, usuario
   - Exportar CSV

**Script de prueba**: `test_phase2_qr_validation.py`

---

### Agente 2.3: Integraci\u00f3n con Horarios y Permisos

**Contexto**: Esta fase conecta el sistema QR con la l\u00f3gica de horarios del PROYECTO-LAB. Como SIGE no tiene m\u00f3dulo de horarios propiamente dicho, esta fase prepara hooks para integraci\u00f3n futura.

**Archivos a leer**:
- `models/academic.py` - AcademicStudent, Grade, SubjectGrade
- `models/attendance.py` - Attendance (para registrar acceso QR como asistencia)

**Especificaciones t\u00e9cnicas**:

1. **Modelo `QRAccessLog`** (agregar a `models/qr_access.py`):
```python
class QRAccessLog(db.Model):
    __tablename__ = 'qr_access_logs'

    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, db.ForeignKey('qr_tokens.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    access_time = db.Column(db.DateTime, default=datetime.utcnow)
    access_type = db.Column(db.String(50))  # 'entrada', 'salida', 'visita'
    location = db.Column(db.String(100))    # campus code
    is_authorized = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
```

2. **Validaci\u00f3n con contexto**:
   - Verificar si el usuario tiene permiso de acceso en ese momento
   - Para estudiantes: verificar horario de clases
   - Para profesores: verificar que est\u00e1 en horario laboral
   - Registrar en log independientemente del resultado

3. **Webhook/API para PROYECTO-LAB**:
   - `POST /api/qr/external-validate` - endpoint para que PROYECTO-LAB valide
   - Autenticaci\u00f3n con API key
   - Retorna datos del usuario + permisos actuales

4. **Dashboard de accesos**:
   - Timeline de accesos del d\u00eda
   - Mapa de calor de accesos por hora
   - Alertas de accesos no autorizados

**Script de prueba**: `test_phase2_qr_integration.py`

---

## FASE 3 - Funcionalidades Avanzadas (Largo Plazo)

**Prioridad**: \ud83d\udfe2 MEDIA-BAJA
**Estimaci\u00f3n**: 6 agentes, ~15-20 horas total
**Dependencias**: Fase 1 completada (capa de servicios + tests)
**Complejidad**: Media-Alta - nuevos modelos y funcionalidades completas

---

### Agente 3.1: Sistema de Comunicaciones Internas

**Contexto**: Sistema de mensajer\u00eda interna entre usuarios del sistema (profesor \u2192 padre, admin \u2192 todos, etc.).

**Archivos a crear**:
- `models/message.py`
- `routes/messages.py`
- `templates/messages/` (inbox, sent, compose, view)
- `services/message_service.py`

**Modelo** (`models/message.py`):
```python
class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL = masivo
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    is_bulk = db.Column(db.Boolean, default=False)
    bulk_target_role = db.Column(db.String(50))  # 'teacher', 'parent', etc.
    bulk_target_grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'))
    attachment_path = db.Column(db.String(255))

    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])
```

**Blueprint** (`routes/messages.py`):
| Ruta | M\u00e9todo | Descripci\u00f3n |
|------|----------|-------------|
| `/messages/` | GET | Bandeja de entrada |
| `/messages/sent` | GET | Mensajes enviados |
| `/messages/compose` | GET/POST | Redactar mensaje |
| `/messages/compose/bulk` | GET/POST | Mensaje masivo |
| `/messages/<id>` | GET | Ver mensaje |
| `/messages/<id>/reply` | GET/POST | Responder |
| `/messages/<id>/delete` | POST | Eliminar |
| `/messages/<id>/mark-read` | POST | Marcar como le\u00eddo |
| `/messages/api/unread-count` | GET | Contador para badge |

**Especificaciones t\u00e9cnicas**:

1. **Bandeja de entrada** (`messages/inbox.html`):
   - DataTables con mensajes recibidos
   - Columnas: Le\u00eddo, Remitente, Asunto, Fecha, Acciones
   - Badge de no le\u00eddos en sidebar
   - Filtros: todos, no le\u00eddos, le\u00eddos

2. **Redactar** (`messages/compose.html`):
   - Select de destinatario (filtrado por rol)
   - Para admin/coordinator: opci\u00f3n "Enviar a todos los X"
   - Subject + Body (textarea grande)
   - Opci\u00f3n de adjuntar archivo

3. **Masivo** (`messages/compose_bulk.html`):
   - Seleccionar target: por rol, por grado, por sede
   - Preview de destinatarios
   - Confirmaci\u00f3n antes de enviar

4. **Notificaciones en UI**:
   - Agregar al `base.html` un badge en el sidebar con count de no le\u00eddos
   - Poll cada 30 segundos a `/messages/api/unread-count`
   - Toast notification cuando llega mensaje nuevo

5. **Vista de mensaje** (`messages/view.html`):
   - Header con remitente, fecha, asunto
   - Body del mensaje
   - Bot\u00f3n responder
   - Si tiene adjunto, bot\u00f3n descargar

**Script de prueba**: `test_phase3_messages.py`

---

### Agente 3.2: Calendario Acad\u00e9mico

**Contexto**: Sistema de eventos y planificaci\u00f3n acad\u00e9mica con vista de calendario.

**Archivos a crear**:
- `models/calendar.py`
- `routes/calendar.py`
- `templates/calendar/` (view, manage)

**Modelo** (`models/calendar.py`):
```python
class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # Para eventos multi-d\u00eda
    event_type = db.Column(db.String(50))  # 'academico', 'administrativo', 'cultural', 'deportivo', 'reunion'
    target_audience = db.Column(db.String(50))  # 'todos', 'estudiantes', 'profesores', 'padres'
    grade_id = db.Column(db.Integer, db.ForeignKey('grades.id'))
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    color = db.Column(db.String(7), default='#667eea')  # Color para calendario
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50))  # 'weekly', 'monthly', 'yearly'

    institution = db.relationship('Institution')
    creator = db.relationship('User')
```

**Blueprint** (`routes/calendar.py`):
| Ruta | M\u00e9todo | Descripci\u00f3n |
|------|----------|-------------|
| `/calendar/` | GET | Vista calendario mensual |
| `/calendar/api/events` | GET | API de eventos para FullCalendar |
| `/calendar/events` | GET | Lista de eventos (admin) |
| `/calendar/events/new` | GET/POST | Crear evento |
| `/calendar/events/<id>/edit` | GET/POST | Editar evento |
| `/calendar/events/<id>/delete` | POST | Eliminar evento |

**Especificaciones t\u00e9cnicas**:

1. **Vista de calendario** (`calendar/view.html`):
   - Usar FullCalendar.js (CDN) o implementaci\u00f3n propia con Bootstrap
   - Vista mensual por defecto
   - Eventos como badges de color en los d\u00edas
   - Click en d\u00eda \u2192 modal con eventos del d\u00eda
   - Click en evento \u2192 modal con detalles
   - Navegaci\u00f3n mes anterior/siguiente
   - Filtros por tipo de evento

2. **Gesti\u00f3n de eventos** (`calendar/manage.html`):
   - CRUD completo con DataTables
   - Filtros por tipo, fecha, p\u00fablico objetivo
   - Color picker para seleccionar color del evento

3. **Sincronizaci\u00f3n con periodos**:
   - Auto-crear eventos de inicio/fin de periodo acad\u00e9mico
   - Alertas de fechas importantes (entrega de notas, boletines)

4. **Acceso por rol**:
   - **Admin/Coordinator**: CRUD completo
   - **Teacher**: Ver calendario + crear eventos de su grado
   - **Student/Parent**: Solo ver calendario de su instituci\u00f3n/grado

**Script de prueba**: `test_phase3_calendar.py`

---

### Agente 3.3: Biblioteca Digital

**Contexto**: Gesti\u00f3n de recursos digitales y libros f\u00edsicos de la instituci\u00f3n.

**Archivos a crear**:
- `models/library.py`
- `routes/library.py`
- `templates/library/` (books, resources, loans)
- `services/library_service.py`

**Modelos** (`models/library.py`):
```python
class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(200))
    isbn = db.Column(db.String(13))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    location = db.Column(db.String(100))  # "Estante A3", etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Loan(db.Model):
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    loan_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, returned, overdue
    notes = db.Column(db.Text)

class DigitalResource(db.Model):
    __tablename__ = 'digital_resources'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id'), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # pdf, doc, video, link
    subject_grade_id = db.Column(db.Integer, db.ForeignKey('subject_grades.id'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    download_count = db.Column(db.Integer, default=0)
```

**Blueprint** (`routes/library.py`):
| Ruta | M\u00e9todo | Descripci\u00f3n |
|------|----------|-------------|
| `/library/books` | GET/POST | Cat\u00e1logo de libros |
| `/library/books/<id>` | GET | Detalle de libro |
| `/library/books/<id>/edit` | GET/POST | Editar libro |
| `/library/books/<id>/delete` | POST | Eliminar libro |
| `/library/loans` | GET/POST | Pr\u00e9stamos activos |
| `/library/loans/<id>/return` | POST | Registrar devoluci\u00f3n |
| `/library/loans/history` | GET | Historial de pr\u00e9stamos |
| `/library/resources` | GET | Recursos digitales |
| `/library/resources/upload` | GET/POST | Subir recurso |
| `/library/resources/<id>/download` | GET | Descargar recurso |

**Especificaciones t\u00e9cnicas**:

1. **Cat\u00e1logo** (`library/books.html`):
   - DataTables con libros
   - B\u00fasqueda por t\u00edtulo, autor, ISBN
   - Filtros por categor\u00eda
   - Badge de disponibilidad (copias disponibles)
   - CRUD completo para admin/bibliotecario

2. **Pr\u00e9stamos** (`library/loans.html`):
   - Tabla de pr\u00e9stamos activos
   - Formulario de nuevo pr\u00e9stamo (select libro + estudiante)
   - Registro de devoluci\u00f3n
   - Alertas de pr\u00e9stamos vencidos
   - Historial completo

3. **Recursos Digitales** (`library/resources.html`):
   - Lista de recursos con iconos por tipo
   - B\u00fasqueda y filtros por materia/grado
   - **Profesores**: pueden subir recursos para sus materias
   - **Estudiantes/Padres**: pueden ver y descargar recursos
   - Contador de descargas

4. **Permisos**:
   - **Admin**: gesti\u00f3n completa de biblioteca
   - **Teacher**: subir recursos, ver pr\u00e9stamos de sus estudiantes
   - **Student/Parent**: ver cat\u00e1logo, descargar recursos, solicitar pr\u00e9stamos

**Script de prueba**: `test_phase3_library.py`

---

### Agente 3.4: Panel de Administraci\u00f3n (Caja de Herramientas)

**Contexto**: Panel de mantenimiento y herramientas de administraci\u00f3n del sistema.

**Archivos a crear**:
- `routes/admin_tools.py`
- `templates/admin_tools/` (dashboard, backup, audit, cleanup)

**Blueprint** (`routes/admin_tools.py`):
| Ruta | M\u00e9todo | Descripci\u00f3n |
|------|----------|-------------|
| `/admin-tools/` | GET | Dashboard de herramientas |
| `/admin-tools/backup/create` | POST | Crear backup de BD |
| `/admin-tools/backup/list` | GET | Lista de backups |
| `/admin-tools/backup/restore/<id>` | POST | Restaurar backup |
| `/admin-tools/audit-logs` | GET | Logs de auditor\u00eda |
| `/admin-tools/cleanup/orphans` | GET/POST | Limpiar datos hu\u00e9rfanos |
| `/admin-tools/stats` | GET | Estad\u00edsticas de uso |

**Especificaciones t\u00e9cnicas**:

1. **Dashboard** (`admin_tools/dashboard.html`):
   - Grid de herramientas con iconos grandes:
     - \ud83d\udcbe Backup/Restore
     - \ud83d\uddd1\ufe0f Limpieza de datos
     - \ud83d\udcca Estad\u00edsticas
     - \ud83d\udccb Logs de auditor\u00eda
   - Estad\u00edsticas r\u00e1pidas: usuarios activos, estudiantes, notas totales

2. **Backup/Restore**:
   - Crear backup: copia del archivo `.db` con timestamp
   - Lista de backups disponibles con tama\u00f1o y fecha
   - Restaurar: reemplazar BD actual con backup
   - **Solo root**: acceso total

3. **Limpieza de hu\u00e9rfanos**:
   - Detectar: Users sin AcademicStudent (role=student), GradeRecords sin estudiante, etc.
   - Preview antes de eliminar
   - Ejecutar limpieza con confirmaci\u00f3n

4. **Estad\u00edsticas de uso**:
   - Usuarios por rol
   - Estudiantes por grado/sede
   - Notas por periodo
   - Asistencias registradas
   - Boletines generados
   - Actividad \u00faltimos 30 d\u00edas

5. **Logs de auditor\u00eda**:
   - Si existe tabla de logs, mostrar hist\u00f3rico
   - Si no existe, crear stub para futura implementaci\u00f3n

**Script de prueba**: `test_phase3_admin_tools.py`

---

### Agente 3.5: Soporte Multi-idioma (i18n)

**Contexto**: Internacionalizaci\u00f3n del sistema para soportar espa\u00f1ol e ingl\u00e9s.

**Archivos a leer**:
- Todos los templates HTML - strings a traducir
- Todos los flash messages en routes - strings a traducir
- `base.html` - agregar selector de idioma

**Librer\u00edas a instalar**: `Flask-Babel`

**Especificaciones t\u00e9cnicas**:

1. **Configuraci\u00f3n Flask-Babel**:
```python
# app.py
from flask_babel import Babel
babel = Babel(app)

@babel.localeselector
def get_locale():
    # 1. Preferencia del usuario en perfil
    # 2. Session
    # 3. Accept-Language header
    return session.get('language', request.accept_languages.best_match(['es', 'en']))
```

2. **Archivos de traducci\u00f3n**:
```
translations/
\u251c\u2500\u2500 es/
\u2502   \u2514\u2500\u2500 LC_MESSAGES/
\u2502       \u251c\u2500\u2500 messages.po
\u2502       \u2514\u2500\u2500 messages.mo
\u2514\u2500\u2500 en/
    \u2514\u2500\u2500 LC_MESSAGES/
        \u251c\u2500\u2500 messages.po
        \u2514\u2500\u2500 messages.mo
```

3. **Marcado de strings en templates**:
```html
{{ _('Promedio General') }}
{{ _('Estudiantes') }}
```

4. **Selector de idioma en UI**:
   - Agregar en `base.html` (header o sidebar footer)
   - Dropdown: \ud83c\uddea\ud83c\uddf8 Espa\u00f1ol | \ud83c\uddec\ud83c\udde7 English
   - Guarda preferencia en session y perfil del usuario

5. **Ruta de cambio de idioma**:
```python
@app.route('/set-language/<lang>')
@login_required
def set_language(lang):
    session['language'] = lang
    current_user.language = lang
    db.session.commit()
    return redirect(request.referrer or url_for('dashboard.index'))
```

6. **Fase de implementaci\u00f3n**:
   - Primero: extraer todos los strings con `pybabel extract`
   - Segundo: traducir manualmente .po
   - Tercero: compilar con `pybabel compile`
   - Prioridad: traducir primero UI principal (sidebar, headers, botones)

**Nota**: Esta es una tarea de gran volumen. Se recomienda empezar con strings cr\u00edticos y expandir gradualmente.

**Script de prueba**: `test_phase3_i18n.py`

---

### Agente 3.6: Notificaciones Push en UI

**Contexto**: Sistema de notificaciones en tiempo real para eventos importantes.

**Archivos a leer**:
- `templates/base.html` - agregar componente de notificaciones
- `static/js/main.js` - agregar polling/toast logic

**Archivos a crear**:
- `models/notification.py` (si se necesita modelo dedicado)
- `static/js/notifications.js`

**Especificaciones t\u00e9cnicas**:

1. **Componente de campana en header** (`base.html`):
   - Icono de campana con badge de count
   - Dropdown con \u00faltimas 5 notificaciones
   - Click en notificaci\u00f3n \u2192 navegar a detalle
   - Bot\u00f3n "Marcar todas como le\u00eddas"

2. **Polling JavaScript** (`static/js/notifications.js`):
   - Poll cada 30 segundos a `/api/notifications/count`
   - Si hay nuevas, actualizar badge
   - Toast notification con animaci\u00f3n para nuevas notificaciones

3. **Tipos de notificaciones**:
   - Nueva nota registrada
   - Nueva observaci\u00f3n
   - Alerta generada
   - Logro otorgado
   - Bolet\u00edn disponible
   - Mensaje recibido

4. **API endpoints**:
```python
@blueprint.route('/api/notifications/count')
@login_required
def notifications_count():
    """Retorna JSON: { count: int, notifications: [...] }"""

@blueprint.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def notifications_mark_read():
    """Marca notificaciones como le\u00eddas."""
```

**Script de prueba**: `test_phase3_notifications.py`

---

## FASE 4 - Producci\u00f3n y Escalabilidad

**Prioridad**: \ud83d\udd35 BAJA (para desarrollo actual, ALTA para deploy)
**Estimaci\u00f3n**: 3 agentes, ~10-15 horas total
**Dependencias**: Fase 1 completada (tests y servicios)
**Complejidad**: Alta - configuraci\u00f3n de infraestructura

---

### Agente 4.1: Deploy a Producci\u00f3n

**Archivos a crear**:
- `deploy/gunicorn_config.py` (o `waitress` config para Windows)
- `deploy/nginx.conf` - reverse proxy config
- `deploy/.env.production` - template de variables de entorno
- `deploy/setup.sh` - script de instalaci\u00f3n en servidor
- `deploy/README.md` - gu\u00eda de deploy
- `wsgi.py` - entry point para producci\u00f3n

**Especificaciones t\u00e9cnicas**:

1. **Configuraci\u00f3n PostgreSQL**:
   - Agregar `SQLALCHEMY_DATABASE_URI` con PostgreSQL en producci\u00f3n
   - Script de migraci\u00f3n de SQLite \u2192 PostgreSQL
   - `pg_dump` y `pg_restore` para backups

2. **Application Server**:
   - Linux: Gunicorn (`gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app`)
   - Windows: Waitress (`waitress-serve --port=5000 wsgi:app`)

3. **Nginx Reverse Proxy**:
```nginx
server {
    listen 80;
    server_name sige.midominio.com;

    location /static/ {
        alias /var/www/sige/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. **HTTPS con Let's Encrypt**:
```bash
certbot --nginx -d sige.midominio.com
```

5. **Variables de entorno** (`.env.production`):
```
FLASK_ENV=production
SECRET_KEY=<random-256-bit-key>
DATABASE_URL=postgresql://user:pass@localhost/sige_db
WEASYPRINT_BASEURL=http://localhost:5000/
```

6. **Systemd service** (Linux):
```ini
[Unit]
Description=SIGE Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/sige
ExecStart=/var/www/sige/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

---

### Agente 4.2: Optimizaci\u00f3n de Rendimiento

**Archivos a leer**:
- Todas las rutas con queries a BD - identificar N+1
- `static/css/` y `static/js/` - assets a optimizar

**Especificaciones t\u00e9cnicas**:

1. **Cach\u00e9 de consultas frecuentes**:
   - Flask-Caching para datos que cambian poco (instituci\u00f3n, periodos, criterios)
   - Cach\u00e9 de templates Jinja2 (ya viene con Flask)
   - Redis como backend de cach\u00e9 (opcional)

2. **Paginaci\u00f3n en listas grandes**:
   - Todas las DataTables ya paginan en cliente
   - Agregar paginaci\u00f3n server-side para listas > 1000 items
   - `paginate(page, per_page)` de SQLAlchemy

3. **Lazy loading de im\u00e1genes**:
   - Agregar `loading="lazy"` a todas las im\u00e1genes
   - Thumbnails para QR codes y avatares

4. **Compresi\u00f3n de assets**:
   - Minificar CSS y JS para producci\u00f3n
   - Gzip compression en Nginx
   - CDN para Bootstrap, DataTables, Chart.js (ya se usa CDN)

5. **Query optimization**:
   - Usar `joinedload()` para relaciones frecuentes
   - \u00cdndices en columnas de b\u00fasqueda frecuente
   - `EXPLAIN QUERY PLAN` para identificar queries lentas

---

### Agente 4.3: Monitoreo y Logs

**Archivos a crear**:
- `logging_config.py` - configuraci\u00f3n de logging
- `routes/health.py` - health check endpoint

**Especificaciones t\u00e9cnicas**:

1. **Logging estructurado**:
```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler('logs/sige.log', maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s [%(name)s] %(message)s'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
```

2. **Sentry para error tracking**:
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1
)
```

3. **Health check endpoint**:
```python
@app.route('/health')
def health_check():
    """Endpoint para monitoreo: retorna status de BD y servicios."""
    try:
        db.session.execute(db.text('SELECT 1'))
        db_ok = True
    except:
        db_ok = False

    return jsonify({
        'status': 'healthy' if db_ok else 'unhealthy',
        'database': 'ok' if db_ok else 'error',
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if db_ok else 503
```

4. **M\u00e9tricas de rendimiento**:
   - Tiempo de respuesta por endpoint
   - Tasa de errores 5xx
   - Uso de memoria y CPU
   - Integraci\u00f3n con Prometheus/Grafana (opcional)

---

## AP\u00c9NDICE - Referencia R\u00e1pida

### Patrones de C\u00f3digo Est\u00e1ndar

#### Nueva Ruta
```python
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
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
        flash('\u26a0\ufe0f Seleccione instituci\u00f3n primero.', 'warning')
        return redirect(url_for('dashboard.index'))

    # L\u00f3gica aqu\u00ed
    return render_template('mi_modulo/vista.html', data=data)
```

#### Registrar Blueprint
```python
# En app.py
from routes.mi_modulo import mi_bp
app.register_blueprint(mi_bp, url_prefix='/mi-prefix')
```

#### Nuevo Template
```html
{% extends "base.html" %}
{% block title %}Mi P\u00e1gina - SIGE{% endblock %}

{% block extra_css %}
<style>
    .mi-card { border: none; border-radius: 15px; }
    .mi-card:hover { transform: translateY(-5px); }
</style>
{% endblock %}

{% block content %}
<div class="container-fluid px-4">
    <div class="d-flex justify-content-between align-items-center mb-4 animate-in">
        <div>
            <h1 class="h3 mb-1 fw-bold text-dark"><i class="bi bi-icon me-2"></i>T\u00edtulo</h1>
            <p class="text-muted mb-0">Descripci\u00f3n</p>
        </div>
        <div class="d-flex gap-2">
            <a href="#" class="btn btn-primary"><i class="bi bi-plus me-1"></i>Nuevo</a>
            <a href="#" class="btn btn-outline-secondary"><i class="bi bi-arrow-left me-1"></i>Volver</a>
        </div>
    </div>
    <!-- Stat Cards, Filtros, Tabla -->
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

#### Nuevo Test (pytest)
```python
# tests/test_mi_modulo.py
class TestMiModulo:
    def test_page_loads(self, admin_client):
        response = admin_client.get('/mi-ruta')
        assert response.status_code == 200

    def test_requires_auth(self, client):
        response = client.get('/mi-ruta')
        assert response.status_code in (302, 401)

    def test_requires_role(self, student_client):
        response = student_client.get('/mi-ruta')
        assert response.status_code in (302, 403)
```

#### Script de Prueba (standalone)
```python
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
    print("=== Mi M\u00f3dulo Tests ===")
    test("Ruta existe", True)

print(f"\nResultados: {passed} passed, {failed} failed, {passed+failed} total")
```

---

### Paleta de Colores

| Uso | Color | Clase | Hex |
|-----|-------|-------|-----|
| Primario | Gradiente | `text-primary` | `#667eea \u2192 #764ba2` |
| \u00c9xito | Verde | `text-success` | `#198754` |
| Advertencia | Amarillo | `text-warning` | `#ffc107` |
| Peligro | Rojo | `text-danger` | `#dc3545` |
| Info | Cyan | `text-info` | `#0dcaf0` |
| Secundario | Gris | `text-muted` | `#6c757d` |

**Regla de iconos**: `bg-{color} bg-opacity-10` para fondos, no colores s\u00f3lidos.

---

### Errores Comunes a Evitar

| Error | Causa | Soluci\u00f3n |
|-------|-------|----------|
| `DetachedInstanceError` | Objeto fuera de session | Usar `db.session.get(Model, id)` |
| Tailwind sin estilos | Proyecto usa Bootstrap 5 | Convertir a clases Bootstrap |
| `BuildError` | Endpoint no existe | Verificar nombre de blueprint y endpoint |
| DataTables "Cannot reinitialise" | Doble inicializaci\u00f3n | Usar `retrieve: true` |
| Estudiantes no aparecen | `institution_id` mismatch | Asignar al crear User Y AcademicStudent |
| `AttributeError: NoneType` | Relationship retorna None | Verificar que el objeto existe |
| Flash messages no se ven | Sin `get_flashed_messages` en template | Agregar en `base.html` |

---

### Comandos \u00fatiles

```bash
# Iniciar aplicaci\u00f3n
.venv\Scripts\python.exe app.py

# Ejecutar tests pytest
.venv\Scripts\pytest.exe tests/ -v

# Ejecutar tests con cobertura
.venv\Scripts\pytest.exe tests/ -v --cov=routes --cov=services --cov=utils --cov-report=html

# Migraciones BD
flask db migrate -m "descripci\u00f3n"
flask db upgrade
flask db downgrade

# Extraer strings para i18n
pybabel extract -F babel.cfg -o messages.pot .
pybabel init -i messages.pot -d translations -l en
pybabel compile -d translations
```

---

### Checklist Pre-Commit para Cada Agente

- [ ] Template usa Bootstrap 5 (NO Tailwind)
- [ ] DataTables configurado en espa\u00f1ol
- [ ] Rutas tienen `@login_required` y `@role_required`
- [ ] Se usa `get_current_institution()` para filtrar datos
- [ ] Formularios retornan `form_data` + `errors` en validaci\u00f3n
- [ ] Flash messages con emojis
- [ ] Script de prueba creado y ejecutado
- [ ] NO se ha hecho `git commit` (esperar verificaci\u00f3n del usuario)
- [ ] Cards tienen `border-radius: 15px` y animaciones fadeInUp
- [ ] Iconos Bootstrap Icons con `me-1` o `me-2`

---

## Resumen de Fases

| Fase | Nombre | Tareas | Horas Est. | Prioridad |
|------|--------|--------|-----------|-----------|
| **0** | Completar Placeholders | 3 agentes | 2-3h | \ud83d\udd34 Alta |
| **1** | Calidad y Robustez | 6 agentes | 8-12h | \ud83d\udfe0 Media-Alta |
| **2** | Integraci\u00f3n QR | 3 agentes | 6-8h | \ud83d\udfe1 Media |
| **3** | Funcionalidades Avanzadas | 6 agentes | 15-20h | \ud83d\udfe2 Media-Baja |
| **4** | Producci\u00f3n y Escalabilidad | 3 agentes | 10-15h | \ud83d\udd35 Baja |
| **TOTAL** | | **21 agentes** | **41-58h** | |

---

> **\u00daltima actualizaci\u00f3n**: 2026-04-12
> **Documento**: AGENT_PLAN_V2.md
> **Mantener actualizado despu\u00e9s de cada sesi\u00f3n de desarrollo**
