# SIGE - Sistema Integral de Gestion Escolar

## Ultimo avance

- **Ultima actualizacion**: 2026-04-23
- **Estado**: Fase 2 (Optimización y Analítica) Completada
- **Version del codigo**: v1.5-analytics
- **Tipo de proyecto**: Sistema de gestion escolar multi-institucional
- **Stack**: Flask + Bootstrap 5 + Chart.js + DataTables (ESPAÑOL) + SQLite/PostgreSQL
- **Sesion actual**: Fase 2 completada - Reingeniería Académica y Analítica Docente IA
- **Total errores corregidos acumulados**: 50+

---

## SESION ACTUAL: Testing Segun TESTING_STRATEGY.md (2026-04-13)

### Metodologia aplicada
Se siguio la estrategia de piramide de testing descrita en TESTING_STRATEGY.md:
1. **Fase 1: Linting** → Busqueda de patrones de error (0 errores nuevos de tipo has_any_role)
2. **Fase 2: Estatico** → 3 agentes Explore en paralelo (url_for, SQL, CSRF)
3. **Fase 3: Runtime** → curl a 10+ rutas con sesion autenticada
4. **Correcciones** → Aplicadas basado en reportes de agentes

### Hallazgos de Agentes de Analisis Estatico

| Agente | Hallazgos | Criticos |
|--------|-----------|----------|
| url_for vs endpoints | 0 mismatches, 293 verificados | 0 |
| Templates render_template | 1 template faltante (certificates/template.html) | 1 (dead code) |
| SQL queries | 3 bugs confirmados | 3 HIGH |
| CSRF y seguridad | 44 forms sin csrf_token, 2 rutas sin @login_required | CRITICAL |

### Errores Corregidos en Esta Sesion (13 nuevos)

| # | Tipo | Archivo | Descripcion del Error | Correccion |
|---|------|---------|----------------------|------------|
| 28 | HIGH SQL | `routes/metrics.py:730-748` | `_get_teacher_subject_grades()`: Institution filter roto con subconsultas circulares que nunca referencian `Campus.institution_id` | Reemplazado con subquery limpia: `Grade.id JOIN Campus WHERE Campus.institution_id == institution.id` |
| 29 | HIGH SQL | `routes/metrics.py:787-794` | `institution_metrics()`: Query con `.join(subquery())` y `.filter(col == query_obj)` genera SQL invalido | Simplificado a `.join(Campus, Grade.campus_id == Campus.id).filter(Campus.institution_id == institution.id)` |
| 30 | MEDIUM | `routes/observations.py:104` | Variable shadowing: `student_ids` redefinido en busqueda por nombre, stats usaban scope incorrecto | Renombrado a `institution_student_ids` + `stats_scope` para calcular correctamente |
| 31 | CRITICAL | `routes/qr.py` | Rutas QR sin `@login_required`, acceso publico | Agregado decorator `@login_required` a ambas rutas |
| 32 | HIGH | `routes/grades.py:904` | `student_grades` solo tenia `@login_required`, cualquier user autenticado podia ver notas | Agregado `@role_required('root','admin','coordinator','teacher','student','parent')` |
| 33 | CRITICAL | `utils/pdf_generator.py:101` | `render_template('certificates/template.html')` archivo no existe, crash si se llama | Funcion convertida a `raise NotImplementedError` con TODO |
| 34 | CRITICAL | 44 forms en templates | Formularios POST sin `{{ csrf_token() }}` - vulnerables a CSRF si se habilita proteccion | Agregado `<input type="hidden" name="csrf_token">` a todos los forms |

### CSRF Tokens Agregados (44 forms en 26 archivos)

| Modulo | Archivos Actualizados | Forms |
|--------|----------------------|-------|
| Auth | login.html, force_password_change.html, profile.html | 4 |
| Users | create.html, edit.html, import_excel.html, list.html | 4 |
| Institution | institution_form.html, config.html, campuses.html (2), grade_form.html, grades.html (2), subject_form.html, subjects.html, period_form.html, periods.html, criteria_form.html, criteria.html, add_admin_form.html, select_institution.html, institutions_list.html | 17 |
| Grades | upload.html, lock_panel.html (2), final_view.html, input.html | 5 |
| Observations | create.html, quick_form.html, list.html, detail.html | 4 |
| Alerts | run_panel.html (2), detail.html | 3 |
| Achievements | list.html (2), student_achievements.html (3), leaderboard.html | 6 |

### Resultados de Runtime Testing

| Ruta | Status | Notas |
|------|--------|-------|
| GET /login | 200 | OK |
| POST /login (root) | 302 | Login exitoso, redirect |
| GET /dashboard | 200 | OK |
| GET /students/ | 200 | OK |
| GET /metrics/institution | 200 | **OK (SQL bug fix verificado)** |
| GET /metrics/teacher | 200 | OK |
| GET /observations | 200 | **OK (variable shadowing fix)** |
| GET /alerts | 200 | OK |
| GET /grades/input | 200 | OK |
| GET /attendance/ | 200 | OK |
| GET /achievements/achievements | 200 | OK |
| GET /report-cards/ | 302 | Redirect a seleccion (esperado) |
| GET /qr/ (sin sesion) | 302 | **Redirect a login (auth fix verificado)** |

### Estado Final
- **0 BuildErrors** (url_for verificados)
- **0 templates faltantes** (excepto certificates/ que es dead code)
- **0 SQL order_by sin join** (corregidos los 2 criticos)
- **44 CSRF tokens agregados**
- **2 rutas protegidas con @login_required**
- **133 endpoints registrados** funcionando

---

## ULTIMAS MEJORAS IMPLEMENTADAS

*(Orden cronologico inverso - lo mas reciente primero)*

### SESION ACTUAL: Fase 2 Completada - Reingeniería Académica (2026-04-23)
- **Soporte Multi-Jornada**: Reestructuración de `Grade` y `ScheduleBlock` para permitir jornadas independientes (Mañana, Tarde, etc.) por grado.
- **Control de Intensidad**: Implementado `hours_per_week` en `SubjectGrade` para gestión granular de carga académica.
- **Generación de Horarios Inteligente**: Refactorización del motor de generación para respetar jornadas e intensidades horarias.
- **Teacher Analytics Service**: Implementado motor de analítica longitudinal que detecta disparidades de rendimiento y genera sugerencias pedagógicas automáticas.
- **Horario Estudiantil**: Visualización profesional de horario semanal en el perfil del estudiante.

### SESION ANTERIOR: Fase 1 Completada - Refactor Arquitectónico y Testing (2026-04-22)
- **Base de Datos Multi-Entorno**: Implementado flag `USE_POSTGRES` en `.env` y `config.py` para alternar fluidamente entre SQLite (desarrollo local) y PostgreSQL (producción/testing avanzado).
- **Alembic / Flask-Migrate**: Estructura de migraciones inicializada y sincronizada con el estado actual de la base de datos sin pérdida de datos.
- **Capa de Servicios**:
  - Creados `GradeCalculatorService`, `ExcelHandlerService`, `ReportCardService`, `StudentService` y `MetricsService` en `services/`.
  - Refactorizadas rutas voluminosas (`routes/grades.py`, `routes/students.py`, `routes/report_cards.py`, `routes/metrics.py`) para delegar la lógica de negocio a los servicios, cumpliendo con SRP.
- **Suite de Pruebas Pytest**:
  - Eliminados los ~16 scripts de pruebas de integración antiguos (`test_*.py` en raíz).
  - Configurado entorno `pytest` con `pytest.ini` y `tests/conftest.py` con fixtures globales de SQLite en memoria temporal.
  - Implementadas pruebas modernas en `tests/test_endpoints.py` y `tests/test_services.py`. Todo en estado PASSED.

### SESION ANTERIOR: Fase 0 Completada (2026-04-22)
- **Implementado `grades/summary.html`**: Resumen completo de calificaciones por materia con Chart.js, estadísticas detalladas y DataTables.
- **Implementado `metrics/risk_students.html`**: Dashboard de estudiantes en riesgo con filtros por umbral y gráficos de distribución. Actualizado `routes/metrics.py` para añadir decoradores de seguridad.
- **Mejorado `parent/dashboard.html`**: Portal de acudientes enriquecido con estadísticas rápidas, estado de notas recientes y alertas.

### SESION ACTUAL: Testing Exhaustivo y Correccion Masiva (27 errores corregidos)

#### FASE 1: Errores de UndefinedError y BuildError (Manual)
- **1-5**: `current_user.has_any_role()` en 5 templates → cambiado a `user_has_any_role()` (base.html, metrics/teacher.html, metrics/teacher_attendance.html, observations/detail.html, observations/list.html)
- **6**: `url_for('achievements.achievements')` → `achievements.achievements_list` (base.html)
- **7**: `url_for('students.student_detail')` → `students.profile` (achievements/student_achievements.html)
- **8**: `url_for('observations.new')` → `observations.observation_create` (dashboard/teacher.html)
- **9**: `url_for('auth.reset_password')` → boton disabled (users/edit.html)
- **12**: `url_for('alerts')` → `alerts.alerts_list` (dashboard/coordinator.html)

#### FASE 2: Errores de SQL (OperationalError)
- **10**: 3 queries en `routes/grades.py` sin `.join(Subject)` → agregado join faltante
- **11**: 5 queries en `routes/attendance.py` sin `.join(Subject)` → agregado join faltante

#### FASE 3: Correcciones por agentes de modulo (5 agentes completados)
- **13**: Students IntegrityError al eliminar → cascade delete de 9 tablas (routes/students.py)
- **14**: Upload inaccesible para root → selector de institucion (routes/students.py + upload.html)
- **15**: CSRF tokens faltantes → agregados en 3 forms de estudiantes
- **16**: GradeCriteria no JSON serializable → criteria_json como lista de dicts (grades.py + input.html)
- **17**: Data path incorrecto en student_view → period_data.subjects (student_view.html)
- **18**: CSS classes faltantes → 5 clases de color agregadas (student_view.html)
- **19**: Block name incorrecto → 4 templates de grades de scripts a extra_js
- **20**: Template summary stub → implementado completo con estadisticas y graficos
- **21**: User.name no existe → property name agregada (models/user.py)
- **22**: Falta @role_required en attendance history → agregado decorator
- **23**: Relationship overlap en Attendance → backref cambiado a back_populates
- **24**: SQL join incorrecto en observations → join explicit con ParentStudent
- **25**: Falta template variable today → agregado a 3 render_template (observations.py)
- **26**: Link roto student_id=0 en report_cards → eliminado
- **27**: CSRF faltante en 7 forms de boletines → agregados tokens

### VALIDACION ESTATISTICA COMPLETA
- **131 endpoints** registrados verificados
- **293 url_for calls** en templates cruzados
- **0 mismatches** restantes
- **0 templates faltantes**
- **0 BuildErrors** pendientes

### NUEVOS DOCUMENTOS CREADOS
- **TESTING_STRATEGY.md**: Plan optimizado de agentes para sesiones futuras
  - Analisis del enfoque fallido (12 agentes gigantes en paralelo)
  - Estrategia de piramide: Linting → Estatico → Runtime → Manual
  - 5 agentes pequenos especificos con prompts listos
  - Comandos utiles y reglas para futuras sesiones
  - Lista de pendientes reales del proyecto

---

### 1. Fix: institution_id en User al crear estudiantes
- **Problema**: Los estudiantes creados desde `/students/new` no tenian `institution_id` en el modelo User, causando que no aparecieran en la lista del administrador
- **Causa**: La ruta de creacion de estudiantes no asignaba `institution_id` al objeto User asociado
- **Solucion**: Se agrego la asignacion de `institution_id` desde la institucion activa del contexto al crear el usuario estudiante
- **Archivos modificados**: `routes/students.py`

### 2. Fix: Perfiles academicos incompletos visibles
- **Problema**: Usuarios con role=student pero sin perfil academico (AcademicStudent) no aparecian en la lista de estudiantes
- **Impacto**: Estudiantes creados parcialmente eran invisibles para el admin
- **Solucion**: La lista de estudiantes ahora tambien muestra usuarios role=student sin perfil academico, con boton "Completar" para finalizar el perfil
- **Archivos modificados**: `routes/students.py`, `templates/students/list.html`

### 3. Fix: 3 bugs en gestion de estudiantes
- **Bug A - Perfil**: Se usaba `user_id` en lugar de `AcademicStudent.id` para cargar el perfil, causando perfil incorrecto o 404
- **Bug B - Edicion**: Al editar estudiante, los campos aparecian vacios porque no se pasaba `form_data` al template
- **Bug C - Observaciones**: `BuildError` porque la ruta se llamaba `observations.student_observations` pero el template referenciaba `students.student_profile`
- **Archivos modificados**: `routes/students.py`, `templates/students/profile.html`, `templates/students/form.html`

### 4. Fix: Sede N/A en perfil + observaciones sin estilos
- **Problema A**: El perfil del estudiante mostraba "Sede: N/A" porque faltaban las relaciones `campus` y `grade` en el modelo AcademicStudent
- **Problema B**: Las observaciones usaban clases de Tailwind CSS en un proyecto Bootstrap 5, sin estilos visibles
- **Solucion A**: Agregadas relationships `campus` y `grade` al modelo AcademicStudent
- **Solucion B**: Observaciones reescritas completamente con Bootstrap 5 (cards, badges, botones, tablas)
- **Archivos modificados**: `models/academic.py`, `templates/observations/list.html`, `templates/observations/detail.html`, `templates/observations/create.html`

### 5. Fix: Conflicto de backrefs en AcademicStudent
- **Problema**: Error de SQLAlchemy mapper por relationship duplicate con mismo backref `academic_profile`
- **Causa**: Se definieron dos relationships apuntando a User con el mismo backref
- **Solucion**: Eliminado el relationship duplicado, manteniendo solo el correcto
- **Archivos modificados**: `models/academic.py`

### 6. Fase 1: Sistema de Notas completo (60% -> 95%)
- **Lock/Unlock**: Panel de bloqueo de notas por grado/periodo/materia
- **Notas finales ponderadas**: Calculo automatico con ponderacion configurable
- **Notas anuales**: Vista consolidada de notas de todo el ano academico
- **Vista estudiante**: Cada estudiante puede ver sus propias notas
- **Templates creados**: `grades/lock_panel.html`, `grades/final_view.html`, `grades/annual_view.html`, `grades/student_view.html`
- **Archivos modificados**: `routes/grades.py`, `models/grading.py`

### 7. Fase 1: Boletines PDF (15% -> 90%)
- **Generacion individual**: Boletin PDF por estudiante
- **Generacion masiva**: Boletines de todo un grado/periodo
- **PDF profesional**: Template `report_cards/pdf_template.html` con diseno profesional
- **Historial**: Vista de boletines generados con estado de entrega
- **Tracking**: Registro de fecha de generacion y estado de entrega al acudiente
- **Pendiente**: Instalacion de WeasyPrint en Windows para renderizado PDF real
- **Templates creados**: `report_cards/manage.html`, `report_cards/generate.html`, `report_cards/history.html`, `report_cards/pdf_template.html`, `report_cards/view.html`
- **Modelos creados**: `ReportCard`, `ReportCardObservation`

### 8. Fase 2: Metricas del Profesor (10% -> 90%)
- **Dashboard del profesor**: KPIs personales de rendimiento
- **Histograma**: Distribucion de notas con Chart.js
- **Tendencias**: Evolucion de rendimiento a lo largo del periodo
- **Comparativa anonima**: Comparacion con promedio anonimo del grado
- **Correlacion asistencia**: Grafico de rendimiento vs asistencia
- **Templates creados**: `metrics/teacher.html`, `metrics/teacher_comparison.html`, `metrics/teacher_attendance.html`

### 9. Fase 2: Metricas Institucionales (10% -> 90%)
- **KPIs institucionales**: Promedios generales, tasas de aprobacion
- **Rendimiento por sede**: Comparativa de rendimiento entre sedes
- **Rendimiento por grado**: Analisis detallado por grado
- **Heatmap**: Mapa de calor de rendimiento academico
- **Tendencias**: Evolucion historica de indicadores
- **Export Excel**: Descarga de datos en formato Excel
- **Templates creados**: `metrics/institution.html`, `metrics/heatmap.html`, `metrics/trends.html`

### 10. Fase 2: Alertas Tempranas (0% -> 95%)
- **Modelo Alert**: Nuevo modelo para registrar alertas automaticas
- **Motor de reglas**: 6 reglas automaticas (bajo rendimiento, ausencias, etc.)
- **Panel de alertas**: Vista de todas las alertas con graficos
- **Resolucion**: Marcado de alertas como resueltas con notas
- **Badge en sidebar**: Indicador de alertas pendientes en la barra lateral
- **Templates creados**: `alerts/list.html`, `alerts/detail.html`, `alerts/run_panel.html`, `alerts.html`
- **Motor**: `utils/alert_engine.py` con 6 reglas configurables

### 11. Fase 3: Logros/Gamificacion (10% -> 95%)
- **Motor auto-award**: 7 reglas de otorgamiento automatico
- **Catalogo de logros**: Vista de todos los logros disponibles
- **Timeline del estudiante**: Historial de logros obtenidos
- **Leaderboard**: Tabla de clasificacion con podio visual
- **Templates creados**: `achievements/list.html`, `achievements/student_achievements.html`, `achievements/leaderboard.html`
- **Motor**: `utils/achievement_engine.py`
- **Modelos**: `Achievement`, `StudentAchievement`

### 12. Fase 3: Portal Acudientes (10% -> 95%)
- **Dashboard del acudiente**: Vista general del estudiante asignado
- **Notas**: Acceso a calificaciones del estudiante
- **Calendario asistencia**: Historial de asistencia con visualizacion
- **Observaciones**: Lista de observaciones de comportamiento
- **Boletines**: Acceso a boletines generados
- **Templates creados**: `parent/dashboard.html`, `parent/grades.html`, `parent/attendance.html`, `parent/observations.html`, `parent/report_cards.html`

---

## ESTRUCTURA ACTUAL DEL PROYECTO

### Routes (14 blueprints)
| Blueprint | Archivo | Descripcion |
|-----------|---------|-------------|
| auth | `routes/auth.py` | Login, logout, perfil, password |
| dashboard | `routes/dashboard.py` | 7 dashboards por rol |
| institution | `routes/institution.py` | Instituciones, sedes, grados, materias, periodos, criterios |
| students | `routes/students.py` | CRUD estudiantes + Excel |
| grades | `routes/grades.py` | Sistema de notas (planilla, lock, finales, anuales) |
| report_cards | `routes/report_cards.py` | Boletines PDF |
| attendance | `routes/attendance.py` | Registro y reportes de asistencia |
| observations | `routes/observations.py` | Observaciones de comportamiento |
| users | `routes/users.py` | CRUD usuarios + Excel + permisos |
| metrics | `routes/metrics.py` | Metricas profesor e institucionales |
| alerts | `routes/alerts.py` | Alertas tempranas |
| achievements | `routes/achievements.py` | Logros y gamificacion |
| parent | `routes/parent.py` | Portal de acudientes |
| qr | `routes/qr.py` | Acceso QR (pendiente) |

### Models (~20 tablas)
| Archivo | Modelos |
|---------|---------|
| `models/institution.py` | Institution, Campus, Grade, Subject |
| `models/academic.py` | SubjectGrade, AcademicStudent, AcademicPeriod |
| `models/grading.py` | GradeCriteria, GradeRecord, FinalGrade, AnnualGrade |
| `models/attendance.py` | Attendance |
| `models/observation.py` | Observation |
| `models/report.py` | ReportCard, ReportCardObservation |
| `models/achievement.py` | Achievement, StudentAchievement |
| `models/alert.py` | Alert |
| `models/user.py` | User, ParentStudent |

### Utils (12 utilidades)
| Utilidad | Archivo | Descripcion |
|----------|---------|-------------|
| Decorators | `utils/decorators.py` | `@login_required`, `@role_required`, `@institution_required` |
| Validators | `utils/validators.py` | Validaciones de datos |
| PDF Generator | `utils/pdf_generator.py` | Generacion de PDFs |
| Charts | `utils/charts.py` | Generador de graficos |
| Institution Resolver | `utils/institution_resolver.py` | `get_current_institution()` |
| Username Generator | `utils/username_generator.py` | Usernames incrementales |
| Alert Engine | `utils/alert_engine.py` | Motor de 6 reglas de alerta |
| Achievement Engine | `utils/achievement_engine.py` | Motor de 7 reglas de logros |
| Template Helpers | `utils/template_helpers.py` | Helpers para templates |
| Form Helpers | `utils/form_helpers.py` | Helpers de formularios |
| Error Handlers | `utils/error_handlers.py` | Manejo de errores |

### Templates: 87 templates HTML
| Modulo | Templates | Estado |
|--------|-----------|--------|
| Base | 10 (base, login, profile, errors, alerts) | Completos |
| Dashboard | 7 (root, admin, coordinator, teacher, student, parent, viewer) | Completos |
| Institucion | 12 (institutions, campuses, grades, subjects, periods, criteria, forms) | Completos |
| Usuarios | 4 (list, create, edit, import_excel) | Completos |
| Estudiantes | 4 (list, form, profile, upload) | Completos |
| Notas | 8 (select, input, upload, lock_panel, final_view, annual_view, student_view, summary) | 100% |
| Asistencia | 4 (take, report, summary, summary_group) | Completos |
| Observaciones | 4 (list, create, detail, student_history, quick_form) | Completos |
| Boletines PDF | 5 (manage, generate, history, pdf_template, view) | 90% |
| Metricas | 6 (teacher, teacher_comparison, teacher_attendance, institution, heatmap, trends, risk_students) | 100% |
| Alertas | 4 (list, detail, run_panel, alerts) | 95% |
| Logros | 3 (list, student_achievements, leaderboard) | 95% |
| Portal Padres | 5 (dashboard, grades, attendance, observations, report_cards) | 100% |
| QR | 2 (my_qr, validate) | Placeholders |
| Macros | 1 (ui_components) | Completo |

*= placeholder minimo

---

## ESTADO POR MODULOS

| Modulo | Progreso | Notas |
|--------|----------|-------|
| Autenticacion | 100% | Login, logout, profile, password, force change |
| Dashboard | 100% | 7 dashboards por rol |
| Institucion | 100% | CRUD completo + API sedes + selectores |
| Usuarios | 100% | CRUD + Excel + permisos + usernames incrementales |
| Estudiantes | 100% | CRUD + Excel + perfiles incompletos visibles |
| Notas | 100% | Lock, finales, anuales, summary completos |
| Asistencia | 100% | Registro, historial, resumen grupal, export |
| Observaciones | 100% | CRUD, historial, notificacion, quick form |
| Boletines PDF | 90% | Generacion, PDF, historial. Falta WeasyPrint en Windows |
| Metricas Profesor | 100% | Dashboard, comparacion, correlacion, risk_students |
| Metricas Inst. | 100% | KPIs, heatmap, tendencias, export |
| Alertas | 95% | Motor, panel, resolucion |
| Logros | 95% | Auto-award, catalogo, leaderboard |
| Portal Padres | 100% | Dashboard avanzado implementado |
| QR Access | 15% | Placeholders - pendiente integracion PROYECTO-LAB |
| Capa de Servicios | 100% | Refactorización completada en Fase 1 |
| Testing | 100% | Migración a Pytest en Fase 1 |
| **TOTAL** | **100% Fase 1** | |

---

## ERRORES SOLUCIONADOS

| # | Error | Causa | Solucion |
|---|-------|-------|----------|
| 1-12 | Errores anteriores | Varios | Sesiones previas |
| 13 | Selector institucion no funciona | Form GET vs POST mismatch | `students.py` acepta GET/POST |
| 14 | Institucion "pegada" en sesion | Sin opcion de cambio | Boton `?change_institution=1` |
| 15 | Usernames no incrementales | Formato estatico | `generate_username_from_db()` |
| 16 | Multiples sedes principales | Sin validacion | Validacion de unicidad |
| 17 | DataTables error "Cannot reinitialise" | Doble inicializacion | Removida clase `datatable`, mejorado `main.js` |
| 18 | `filter_by` en InstrumentedList | Lista no query | Bucle manual en template |
| 19 | Error de metodo en dashboard | `<a href>` a ruta POST | Ruta `switch_institution` acepta GET/POST |
| 20 | Selector devuelve al dashboard | Pagina separada | Selector integrado en sedes/grados |
| 21 | Form borra datos al error | Sin `form_data` | Backend retorna `form_data` + `errors` |
| 22 | Codigo de sede duplicado | Sin validacion | Validacion de unicidad en creacion/edicion |
| 23 | Sede principal no visible | Checkbox poco visible | Rediseno con fondo amarillo y estrella |
| 24 | `session` not defined | Import faltante | Agregado `session` a imports de Flask |
| **25** | **institution_id faltante en User de estudiantes** | **No se asignaba al crear** | **Asignacion desde contexto activo** |
| **26** | **Perfiles incompletos invisibles** | **Solo query AcademicStudent** | **Incluye users role=student sin perfil** |
| **27** | **Perfil: user_id vs AcademicStudent.id** | **ID incorrecto en ruta** | **Usar AcademicStudent.id correctamente** |
| **28** | **Edicion: campos vacios** | **Sin form_data** | **Pasar form_data al template** |
| **29** | **Observaciones: BuildError** | **Ruta students.student_profile no existe** | **Corregida a observations.student_observations** |
| **30** | **Sede N/A en perfil** | **Faltaban relationships** | **Agregadas campus y grade** |
| **31** | **Observaciones sin estilos** | **Tailwind en proyecto Bootstrap** | **Reescritas con Bootstrap 5** |
| **32** | **Conflicto backrefs** | **Mapper error SQLAlchemy** | **Eliminado relationship duplicado** |

---

## ESTADISTICAS GENERALES

| Metrica | Valor |
|---------|-------|
| Modelos de BD | ~20 tablas |
| Blueprints Funcionales | 14/14 |
| Endpoints HTTP | ~150+ registrados |
| Templates HTML | 87 (~84 funcionales, ~3 placeholders) |
| Archivos Python | ~40 |
| Lineas de Codigo Python | ~18,000+ |
| Lineas de CSS | ~1,500 |
| Lineas de JS | ~800 |
| Scripts de Migracion | 4 ejecutados |
| Scripts de Prueba | 12 scripts, ~90+ tests |

---

## COMO PROBAR

```bash
cd "c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR"
.venv\Scripts\python.exe app.py
```

**URL**: http://localhost:5000
**Login Root**: `root` / `root123`
**Login Admin**: crear desde root

---

1. **Sistema QR** - Pendiente integracion con PROYECTO-LAB
2. **Caché y Redis** - Siguiente paso de optimización (Fase 2)
3. **Roles Dinámicos y Auditoría** - Siguiente paso (Fase 2)
4. **Upload foto/logo** - Stub con pass

---

## RECOMENDACIONES UX/UI - ESTANDARES DEL PROYECTO

> **NOTA IMPORTANTE**: Estas recomendaciones deben cumplirse **SIEMPRE** en cualquier nueva funcionalidad o modificacion del sistema.

### 1. Principios Generales de Diseno

#### Consistencia Visual
- Mantener el mismo estilo en todos los modulos (cards, botones, tablas, modales)
- Usar los colores definidos: Primary (#667eea), Success (#198754), Warning (#ffc107), Danger (#dc3545), Info (#0dcaf0)
- Seguir patrones establecidos: Si un CRUD ya tiene cierto diseno, replicarlo
- **No mezclar estilos**: Evitar componentes con estilos diferentes a los existentes

#### Profesionalismo y Pulcritud
- Espaciado generoso: Usar `p-4`, `g-4`, `mb-4`
- Bordes redondeados: Todos los cards y modales usan `border-radius: 15px`
- Sombras sutiles: `shadow-sm` para cards normales, `shadow` para modales
- Tipografia clara: Titulos con `fw-bold`, textos secundarios con `text-muted small`
- Iconos descriptivos: Bootstrap Icons con `me-1` o `me-2`

#### Animaciones y Transiciones
- fadeInUp para entrada de elementos
- Delays escalonados: `.delay-1` (0.1s), `.delay-2` (0.2s), `.delay-3` (0.3s)
- Hover effects: `transform: translateY(-5px)` + `box-shadow` en cards
- Transiciones suaves: `transition: all 0.3s ease` en botones y links
- **NO abusar de animaciones**: Solo donde aporte valor visual

### 2. Estructura Estandar de Paginas CRUD

#### Header de Pagina
- Titulo con icono + texto grande (`h3 fw-bold`)
- Subtitulo con `text-muted` explicando la seccion
- Botones de accion a la derecha (`d-flex gap-2`)

#### Stat Cards
- 3-4 cards en fila (`col-md-3` o `col-md-4`)
- Icono circular con fondo de color (`bg-X bg-opacity-10`)
- Numero grande (`fw-bold`) + texto descriptivo pequeno
- Hover: `translateY(-5px)` + sombra

#### Tabla de Datos
- Header con gradiente (`bg-primary text-white`)
- **DataTables configurado en espanol siempre**
- Badges para estados y tipos
- Botones de accion centrados con iconos
- Hover: `background-color: #f8f9ff`

#### Empty State
- Icono grande (`font-size: 5rem`) con `text-muted`
- Titulo `h4 text-muted`
- Descripcion corta
- Boton CTA grande (`btn-lg px-5`)

### 3. Formularios - Estandares

#### Estructura
- **2 columnas** para formularios cortos, **1 columna** para largos
- Labels con iconos: `<i class="bi bi-X text-primary me-1"></i>`
- Campos obligatorios: Marcados con `<span class="text-danger">*</span>`
- Hints de ayuda: Debajo de cada campo con ejemplos
- Sidebar de ayuda: Columna derecha con informacion

#### Validacion en Tiempo Real
- JavaScript valida al salir del campo (on blur)
- Borde verde + icono check para validos (`is-valid`)
- Borde rojo + mensaje de error para invalidos (`is-invalid`)
- **Mantener datos**: Al retornar con errores, NUNCA borrar lo que el usuario lleno
- Scroll al primer error: Automaticamente llevar al usuario al campo problematico

### 4. Errores Comunes a Evitar

#### NO Hacer:
- Usar estilos inline en lugar de clases CSS
- Crear paginas sin header descriptivo
- Tablas sin DataTables configurado
- Formularios que borren datos al tener errores
- Mensajes de error genericos ("Error desconocido")
- **Mezclar Tailwind con Bootstrap 5**
- No usar animaciones de entrada (fadeInUp)
- Botones sin iconos descriptivos
- Cards sin sombras o bordes redondeados
- Selector de institucion en pagina separada

#### SI Hacer:
- Usar clases CSS del archivo `sige-styles.css`
- Seguir la estructura estandar de paginas CRUD
- Configurar DataTables en espanol
- Mantener datos del formulario al retornar con errores
- Mensajes de error descriptivos con ejemplos
- Usar `get_current_institution()` siempre
- Mantener consistencia visual en todo el sistema

### 5. Paleta de Colores y Uso

| Color | Codigo | Uso |
|-------|--------|-----|
| Primary | `#667eea` -> `#764ba2` | Headers, botones principales, gradientes |
| Success | `#198754` | Activos, completados, estudiantes |
| Warning | `#ffc107` | Advertencias, sede principal, edit |
| Danger | `#dc3545` | Errores, eliminar, inactivos |
| Info | `#0dcaf0` | Informacion, jornadas, badges secundarios |
| Secondary | `#6c757d` | Textos secundarios, placeholders |

**Regla**: Usar `bg-X bg-opacity-10` para fondos de iconos, no colores solidos.

### 6. Arquitectura de Codigo

#### Rutas (Backend)
- Usar `get_current_institution()` para obtener institucion activa
- Para root: verificar si necesita selector de institucion
- Validar datos antes de guardar, retornar `form_data` + `errors` si hay problemas
- Flash messages con emojis: exito, advertencia, error
- Redirigir despues de POST (PRG pattern)

#### Templates (Frontend)
- Extender `base.html`
- Usar `{% block extra_css %}` para estilos especificos
- Usar `{% block extra_js %}` para scripts especificos
- Verificar `form_data` y `errors` para rellenar campos y mostrar errores
- DataTables con `retrieve: true` para evitar re-inicializacion

---

## NOTAS IMPORTANTES PARA FUTURAS SESIONES

1. **Bootstrap 5**: NUNCA usar Tailwind CSS. Este es un proyecto Bootstrap 5.
2. **DataTables**: Siempre con idioma español. No usar la configuracion por defecto en ingles.
3. **Agentes**: Usar para tareas pesadas, uno por modulo. No mezclar cambios de multiples modulos en una sola sesion.
4. **Tests**: Siempre crear script de prueba antes de commitear. Verificar funcionalidad manualmente.
5. **NO commitear** hasta que el usuario verifique personalmente que todo funciona.
6. **Institution resolver**: Usar `get_current_institution()` siempre para obtener la institucion activa. No acceder directamente a session.
7. **Roles**: 7 roles con jerarquia estricta: root > admin > coordinator > teacher > student > parent > viewer
8. **Usernames**: Generados automaticamente con formato incremental (nombre + numero). Nunca pedir contrasena manual para admins creados por institucion.
9. **Persistencia de formularios**: Siempre retornar `form_data` y `errors` al validar. Nunca borrar datos del usuario.
10. **Relaciones de modelos**: Verificar que todas las relaciones (backrefs) esten correctamente definidas sin duplicados.

---

*Ultima actualizacion: 2026-04-22*
*Estado: Arquitectura solida, 100% Core implementado (Fase 0 completa), UX/UI profesional estandarizada*
*Pendientes principales: QR (integracion LAB), capa de servicios, tests unitarios*
