# PLAN DE AGENTES PARALELOS - MODULOS PENDIENTES

## ARQUITECTURA GENERAL

Cada agente trabaja de forma independiente en un modulo completo. Los agentes NO hacen commit - dejan los cambios listos para revision del usuario.

### Reglas para TODOS los agentes:
- **NO commitear cambios**
- **Usar Bootstrap 5** (NO Tailwind CSS)
- **Seguir patrones existentes**: stat cards, tablas con DataTables, animaciones fadeInUp
- **Crear script de prueba** para verificar que funciona
- **Usar archivos existentes como referencia** de estilo y estructura
- **Seguir UX/UI estandarizada** documentada en PROGRESS.md

---

## FASE 1 - CORE ACADEMICO (PRIORIDAD ALTA)

### AGENTE 1: Completar Sistema de Notas

**Contexto**: El modulo de notas esta al 60%. Ya existe entrada de notas tipo spreadsheet, calculo automatico con ponderacion, y carga masiva desde Excel. Falta: bloqueo/desbloqueo de notas, notas finales por periodo, y notas anuales.

**Archivos de referencia**:
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\grades.py` (869 lineas - ya implementado parcialmente)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\models\grading.py` (modelos FinalGrade, AnnualGrade ya existen)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\grades\input.html` (template spreadsheet)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\grades\select.html` (seleccion grado/asignatura)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\utils\charts.py` (graficos existentes)

**Archivos a modificar**:
- `routes/grades.py` - Agregar rutas nuevas

**Archivos a crear**:
- `templates/grades/annual_summary.html` - Resumen anual de notas
- `templates/grades/final_grades.html` - Gestion de notas finales por periodo
- `templates/grades/lock_management.html` - Panel de bloqueo de notas
- `test_notes_module.py` - Script de prueba

**Que debe crear el agente**:

1. **Ruta de gestion de notas finales por periodo** (`/grades/final/<int:period_id>`):
   - Tabla con todos los estudiantes, asignaturas y notas finales
   - Calculo automatico desde GradeRecord -> FinalGrade
   - Estado: ganada/perdida/no evaluado
   - Filtros por grado y asignatura
   - Boton para recalcular todas las notas finales

2. **Ruta de notas anuales** (`/grades/annual`):
   - Vista de resumen anual por estudiante/grado
   - Calculo de nota anual como promedio ponderado de periodos
   - Estado: aprobado/reprobado
   - Exportar a CSV

3. **Sistema de bloqueo mejorado** (`/grades/lock`):
   - Panel de administracion para bloquear/desbloquear notas
   - Bloqueo por: grado, asignatura, periodo, o global
   - Solo root/admin/coordinator pueden desbloquear
   - Log de quien bloqueo/desbloqueo y cuando

4. **Template `final_grades.html`**:
   - Header con titulo y selector de periodo
   - Stat cards: Total estudiantes, Aprobados, Reprobados, % aprobacion
   - Tabla con DataTables: Estudiante | Asignatura | Nota Final | Estado
   - Badges de colores: verde (ganada >= 3.0), rojo (perdida < 3.0)
   - Boton de recalcular notas finales

5. **Template `annual_summary.html`**:
   - Selector de ano academico y grado
   - Tabla resumen: Estudiante | Asignatura | P1 | P2 | P3 | P4 | Nota Anual | Estado
   - Grafico de distribucion de notas anuales (usar `utils/charts.py`)
   - Exportar a CSV

6. **Template `lock_management.html`**:
   - Panel de administracion de bloqueo
   - Tabla de estados de bloqueo actuales
   - Formulario para bloquear/desbloquear
   - Log de cambios de estado

7. **Script de prueba `test_notes_module.py`**:
   - Verificar que las rutas responden correctamente
   - Verificar que el calculo de notas finales funciona
   - Verificar que el bloqueo funciona
   - Verificar que las notas anuales se calculan

**Dependencias**: Ninguna (modulo independiente)

**Verificacion**:
```bash
.venv\Scripts\python.exe test_notes_module.py
```
- Todas las rutas deben responder sin error 500
- Calculo de notas finales debe ser correcto
- Bloqueo debe impedir modificacion de notas

---

### AGENTE 2: Boletines PDF

**Contexto**: El modulo de boletines tiene templates placeholder y un modelo ReportCard existente. Ya existe `utils/pdf_generator.py` con funcion `generate_report_card_pdf`. Falta la logica completa de generacion, descarga y visualizacion.

**Archivos de referencia**:
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\report_cards.py` (placeholder actual)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\models\report.py` (modelos ReportCard, ReportCardObservation)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\utils\pdf_generator.py` (funcion PDF ya existe)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\report_cards\generate.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\report_cards\view.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\report_cards\history.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\grades.py` (para obtener datos de notas)

**Archivos a modificar**:
- `routes/report_cards.py` - Implementar logica completa
- `templates/report_cards/generate.html` - Reemplazar placeholder
- `templates/report_cards/view.html` - Reemplazar placeholder
- `templates/report_cards/history.html` - Reemplazar placeholder

**Archivos a crear**:
- `templates/report_cards/pdf_template.html` - Template HTML para renderizado PDF
- `test_report_cards.py` - Script de prueba

**Que debe crear el agente**:

1. **Ruta de generacion** (`/report-cards/` GET/POST):
   - Formulario para seleccionar: grado, periodo academico
   - Lista de estudiantes del grado seleccionado
   - Boton "Generar Boletin Individual" por estudiante
   - Boton "Generar Todos los Boletines" del grado
   - Al generar: crea ReportCard en BD, genera PDF, permite descarga

2. **Ruta de visualizacion** (`/report-cards/<int:id>`):
   - Muestra boletin completo en HTML
   - Datos del estudiante, grado, periodo, institucion
   - Tabla de notas por asignatura y criterio
   - Observaciones por asignatura (ReportCardObservation)
   - Observacion general
   - Boton "Descargar PDF"
   - Boton "Marcar como Entregado"

3. **Ruta de descarga PDF** (`/report-cards/<int:id>/download`):
   - Genera PDF usando `utils/pdf_generator.py`
   - Guarda en sistema de archivos
   - Devuelve archivo para descarga
   - Actualiza `pdf_path` en ReportCard

4. **Ruta de historial** (`/report-cards/history/<int:student_id>`):
   - Lista todos los boletines del estudiante
   - Periodo, fecha de generacion, estado de entrega
   - Botones: Ver, Descargar PDF
   - Indicador visual: entregado (verde) / pendiente (amarillo)

5. **Ruta de entrega** (`/report-cards/<int:id>/mark-delivered` POST):
   - Cambia `delivery_status` a 'entregado'
   - Registra `delivery_date`

6. **Template `pdf_template.html`**:
   - Diseno profesional para PDF
   - Logo/header de institucion
   - Datos del estudiante
   - Tabla de notas detallada
   - Observaciones
   - Firmas

7. **Template `generate.html`**:
   - Selector de grado y periodo
   - Tabla de estudiantes con botones de generacion
   - Barra de progreso para generacion masiva
   - Stat cards: Boletines generados, Pendientes, Entregados

8. **Template `view.html`**:
   - Vista completa del boletin en HTML
   - Formato similar al PDF pero interactivo
   - Botones de accion: Descargar, Marcar entregado, Volver

9. **Template `history.html`**:
   - Tabla historial de boletines
   - Filtros por ano academico
   - Badges de estado

10. **Script de prueba `test_report_cards.py`**:
    - Verificar generacion de boletin individual
    - Verificar generacion masiva
    - Verificar descarga PDF
    - Verificar historial
    - Verificar marcado como entregado

**Dependencias**: Sistema de Notas (necesita FinalGrade calculadas)

**Verificacion**:
```bash
.venv\Scripts\python.exe test_report_cards.py
```
- Debe generar archivos PDF validos
- PDF debe contener datos correctos del estudiante
- Historial debe mostrar todos los boletines

---

## FASE 2 - ANALITICA (PRIORIDAD MEDIA)

### AGENTE 3: Metricas del Profesor

**Contexto**: Template placeholder existe. Ya hay funciones de graficos en `utils/charts.py`. Falta toda la logica de calculo de metricas y templates con datos reales.

**Archivos de referencia**:
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\metrics.py` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\metrics\teacher.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\utils\charts.py` (funciones de graficos)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\grades.py` (para obtener datos de notas)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\attendance.py` (para datos de asistencia)

**Archivos a modificar**:
- `routes/metrics.py` - Implementar `teacher_metrics()`

**Archivos a crear**:
- `templates/metrics/teacher.html` - Reemplazar placeholder

**Que debe crear el agente**:

1. **Ruta `teacher_metrics()`** (`/metrics/teacher`):
   - Calcula metricas para el profesor logueado (o todos si root/admin)
   - Promedio general de notas de sus asignaturas
   - Tasa de aprobacion (% estudiantes >= 3.0)
   - Distribucion de notas por asignatura
   - Tendencia de rendimiento por periodo
   - Asistencia promedio de sus estudiantes
   - Top 5 estudiantes con mejor rendimiento
   - Top 5 estudiantes en riesgo

2. **Template `teacher.html`**:
   - Selector de periodo academico
   - Stat cards: Promedio General, % Aprobacion, Total Estudiantes, Asistencia Promedio
   - Grafico de distribucion de notas (histograma) - usar `generate_grade_distribution_chart`
   - Grafico de aprobado/reprobado (pie chart) - usar `generate_pie_chart_pass_fail`
   - Grafico de tendencia por periodo (line chart) - usar `generate_line_chart_trends`
   - Tabla: Asignatura | Promedio | Aprobados | Reprobados | % Aprobacion
   - Lista top 5 mejores estudiantes
   - Lista top 5 estudiantes en riesgo (nota < 3.0)

**Dependencias**: Sistema de Notas (necesita datos de notas)

**Verificacion**:
- Pagina carga sin errores 500
- Graficos se generan correctamente
- Metricas calculan valores correctos

---

### AGENTE 4: Metricas Institucionales

**Contexto**: Template placeholder existe. Falta logica de calculo de metricas a nivel institucion.

**Archivos de referencia**:
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\metrics.py`
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\metrics\institution.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\metrics\heatmap.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\utils\charts.py`
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\utils\institution_resolver.py`

**Archivos a modificar**:
- `routes/metrics.py` - Implementar `institution_metrics()` y `metrics_heatmap()`

**Archivos a crear**:
- `templates/metrics/institution.html` - Reemplazar placeholder
- `templates/metrics/heatmap.html` - Reemplazar placeholder

**Que debe crear el agente**:

1. **Ruta `institution_metrics()`** (`/metrics/institution`):
   - Solo root/admin/coordinator
   - Promedio general de toda la institucion
   - Comparativa entre grados
   - Comparativa entre asignaturas
   - Tasa de aprobacion general
   - Asistencia promedio institucional
   - Estudiantes en riesgo (promedio < 3.0)
   - Graficos comparativos

2. **Ruta `metrics_heatmap()`** (`/metrics/heatmap`):
   - Mapa de calor: filas = grados, columnas = asignaturas
   - Valores = promedio de notas
   - Colores: rojo (bajo), amarillo (medio), verde (alto)
   - Usar `generate_heatmap_data` de `utils/charts.py`

3. **Template `institution.html`**:
   - Stat cards: Promedio Institucional, % Aprobacion, Total Estudiantes, Asistencia Promedio
   - Grafico comparativo entre grados (bar chart)
   - Grafico comparativo entre asignaturas (bar chart)
   - Pie chart: Aprobados vs Reprobados
   - Tabla: Grado | Promedio | Aprobados | Reprobados | % Aprobacion
   - Lista de estudiantes en riesgo

4. **Template `heatmap.html`**:
   - Selector de periodo academico
   - Heatmap grande (usar chart de `utils/charts.py`)
   - Leyenda de colores
   - Tabla de datos subyacente

**Dependencias**: Sistema de Notas

**Verificacion**:
- Metricas calculan correctamente
- Heatmap se genera con datos reales
- Comparativas son precisas

---

### AGENTE 5: Alertas Tempranas

**Contexto**: Modulo no iniciado. Necesita un motor de reglas que detecte estudiantes en riesgo automaticamente.

**Archivos de referencia**:
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\models\grading.py` (FinalGrade, GradeRecord)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\models\attendance.py` (AttendanceRecord)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\models\observation.py` (Observation)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\grades.py`
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\attendance.py`
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\observations.py`

**Archivos a crear**:
- `models/alert.py` - Modelo de alerta temprana
- `utils/alert_engine.py` - Motor de reglas de alertas
- `routes/alerts.py` - Blueprint de rutas de alertas
- `templates/alerts/list.html` - Lista de alertas activas
- `templates/alerts/detail.html` - Detalle de alerta
- `templates/alerts/rules.html` - Configuracion de reglas
- `test_alerts_module.py` - Script de prueba

**Que debe crear el agente**:

1. **Modelo `EarlyAlert`** (`models/alert.py`):
   ```python
   class EarlyAlert(db.Model):
       id, student_id, alert_type, severity, description
       triggered_at, resolved_at, resolved_by
       is_active, rule_name, reference_data (JSON)
   ```
   - Tipos: 'academico', 'asistencia', 'comportamiento', 'multiple'
   - Severidad: 'baja', 'media', 'alta', 'critica'

2. **Motor de alertas** (`utils/alert_engine.py`):
   - Regla 1: Promedio < 3.0 en cualquier asignatura -> alerta academica
   - Regla 2: 3+ ausencias injustificadas en un mes -> alerta asistencia
   - Regla 3: 2+ observaciones negativas en un mes -> alerta comportamiento
   - Regla 4: Promedio < 2.5 en 2+ asignaturas -> alerta multiple (critica)
   - Regla 5: Tendencia de notas en descenso (comparar periodos) -> alerta academica
   - Funcion `run_all_checks(institution_id=None, period_id=None)`
   - Funcion `create_alert(student_id, type, severity, description, rule_name, ref_data)`
   - Funcion `resolve_alert(alert_id, resolved_by)`

3. **Ruta de lista de alertas** (`/alerts/`):
   - Solo root/admin/coordinator/teacher
   - Filtros: tipo, severidad, estado (activa/resuelta), grado
   - Tabla: Estudiante | Tipo | Severidad | Descripcion | Fecha | Acciones
   - Stat cards: Alertas Activas, Criticas, Resueltas Hoy, Total
   - Badge de severidad con colores

4. **Ruta de detalle** (`/alerts/<int:id>`):
   - Detalle completo de la alerta
   - Datos del estudiante
   - Historial de notas del estudiante
   - Historial de asistencia
   - Boton "Marcar como Resuelta"

5. **Ruta de configuracion de reglas** (`/alerts/rules`):
   - Solo root/admin
   - Activar/desactivar reglas individuales
   - Configurar umbrales (ej: cambiar nota minima de alerta)
   - Configurar frecuencia de ejecucion automatica

6. **Ruta de ejecucion manual** (`/alerts/run-checks` POST):
   - Ejecuta `run_all_checks()`
   - Retorna conteo de alertas nuevas

7. **Template `list.html`**:
   - Header con stat cards
   - Filtros avanzados
   - Tabla con DataTables
   - Colores por severidad: rojo (critica), naranja (alta), amarillo (media), azul (baja)

8. **Template `detail.html`**:
   - Info de alerta con badge de severidad
   - Datos academicos del estudiante
   - Grafico de tendencia de notas
   - Historial de asistencia reciente
   - Acciones: Resolver, Ignorar, Contactar acudiente

9. **Template `rules.html`**:
   - Lista de reglas con switches
   - Formulario de configuracion de umbrales
   - Descripcion de cada regla

10. **Script de prueba `test_alerts_module.py`**:
    - Crear datos de prueba (notas bajas, ausencias)
    - Ejecutar motor de alertas
    - Verificar que se generan alertas correctas
    - Verificar resolucion de alertas

**Dependencias**: Sistema de Notas, Asistencia, Observaciones

**Verificacion**:
```bash
.venv\Scripts\python.exe test_alerts_module.py
```
- Motor detecta correctamente estudiantes en riesgo
- Alertas se clasifican por severidad correcta
- Resolucion de alertas funciona

---

## FASE 3 - GAMIFICACION Y PORTAL (PRIORIDAD BAJA)

### AGENTE 6: Sistema de Logros - Auto-Award

**Contexto**: Modelo Achievement y StudentAchievement ya existen con seed data. Templates placeholder existen. Falta el sistema de auto-otorgamiento basado en logros.

**Archivos de referencia**:
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\achievements.py` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\models\achievement.py` (modelos existentes)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\achievements\list.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\achievements\student_achievements.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\achievements\leaderboard.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\grades.py` (para verificar condiciones)

**Archivos a modificar**:
- `routes/achievements.py` - Implementar logica completa

**Archivos a crear**:
- `utils/achievement_engine.py` - Motor de otorgamiento automatico
- `templates/achievements/list.html` - Reemplazar placeholder
- `templates/achievements/student_achievements.html` - Reemplazar placeholder
- `templates/achievements/leaderboard.html` - Reemplazar placeholder
- `test_achievements.py` - Script de prueba

**Que debe crear el agente**:

1. **Motor de logros** (`utils/achievement_engine.py`):
   - Regla: "Excelencia Academica" -> Promedio >= 4.5 en un periodo
   - Regla: "Superacion Personal" -> Mejoro nota en 1+ punto respecto periodo anterior
   - Regla: "Asistencia Perfecta" -> 0 ausencias en un periodo
   - Regla: "Mejor Comportamiento" -> 0 observaciones negativas en periodo
   - Regla: "Esfuerzo Constante" -> Todas las asignaturas aprobadas
   - Regla: "Lider Academico" -> Mejor promedio del grado
   - Funcion `check_and_award(student_id, period_id)` - verifica y otorga
   - Funcion `check_all_students(institution_id, period_id)` - ejecuta masivamente

2. **Ruta de lista de logros** (`/achievements/achievements`):
   - Lista todos los logros disponibles
   - Filtros por categoria
   - Indicador de cuantos estudiantes lo tienen
   - Icono, descripcion, criterios

3. **Ruta de logros del estudiante** (`/achievements/achievements/student/<int:id>`):
   - Logros obtenidos por el estudiante
   - Logros disponibles pero no obtenidos (gris)
   - Fecha de obtencion
   - Timeline visual de logros

4. **Ruta de leaderboard** (`/achievements/leaderboard`):
   - Ranking de estudiantes por cantidad de logros
   - Filtros por grado y periodo
   - Top 10 estudiantes
   - Medallas: oro, plata, bronce
   - Tabla: Posicion | Estudiante | Grado | Logros | Categoria Principal

5. **Integracion automatica**:
   - Hook en calculo de FinalGrade -> llamar `check_and_award`
   - Hook al final de periodo -> `check_all_students`

6. **Template `list.html`**:
   - Grid de cards de logros
   - Icono grande, nombre, descripcion, criterios
   - Badge de categoria
   - Contador de estudiantes que lo tienen

7. **Template `student_achievements.html`**:
   - Perfil del estudiante
   - Grid: logros obtenidos (color) vs no obtenidos (gris)
   - Timeline vertical de logros obtenidos
   - Stats: Total logros, por categoria

8. **Template `leaderboard.html`**:
   - Podio top 3 con medallas
   - Tabla del resto del ranking
   - Filtros por grado/periodo
   - Animaciones de entrada

9. **Script de prueba `test_achievements.py`**:
    - Crear estudiante con notas altas
    - Ejecutar motor
    - Verificar que obtiene logros correctos
    - Verificar leaderboard

**Dependencias**: Sistema de Notas

**Verificacion**:
```bash
.venv\Scripts\python.exe test_achievements.py
```
- Logros se otorgan automaticamente al cumplir condiciones
- Leaderboard muestra ranking correcto

---

### AGENTE 7: Portal de Acudientes - Dashboards

**Contexto**: Template `parent/dashboard.html` ya tiene algo de UI (muestra hijos si existen). Las otras rutas son placeholders. Falta conectar con datos reales.

**Archivos de referencia**:
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\parent.py` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\parent\dashboard.html` (ya tiene UI parcial)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\parent\grades.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\parent\attendance.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\templates\parent\report_cards.html` (placeholder)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\grades.py` (para obtener notas)
- `c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR\routes\attendance.py` (para asistencia)

**Archivos a modificar**:
- `routes/parent.py` - Implementar logica completa
- `templates/parent/dashboard.html` - Conectar con datos reales
- `templates/parent/grades.html` - Reemplazar placeholder
- `templates/parent/attendance.html` - Reemplazar placeholder
- `templates/parent/report_cards.html` - Reemplazar placeholder

**Archivos a crear**:
- `test_parent_portal.py` - Script de prueba

**Que debe crear el agente**:

1. **Ruta `parent_dashboard()`** (`/parent/dashboard`):
   - Obtener hijos del acudiente (User -> AcademicStudent via parent relationship)
   - Para cada hijo: resumen de notas, asistencia, observaciones recientes
   - Cards de acceso rapido: Notas, Asistencia, Observaciones, Boletines
   - Alertas activas del hijo (si hay modulo de alertas implementado)

2. **Ruta `parent_view_grades(<student_id>)`** (`/parent/grades/<id>`):
   - Verificar que el acudiente tiene permiso de ver ese estudiante
   - Notas por periodo y asignatura
   - Estado: aprobada/reprobada
   - Promedio general
   - Sin botones de edicion (solo lectura)

3. **Ruta `parent_view_attendance(<student_id>)`** (`/parent/attendance/<id>`):
   - Historial de asistencia del estudiante
   - Estadisticas: presentes, ausentes, justificados
   - Grafico simple de asistencia
   - Detalle por fecha

4. **Ruta `parent_view_report_cards(<student_id>)`** (`/parent/report-cards/<id>`):
   - Boletines entregados del estudiante
   - Boton de descarga PDF
   - Solo boletines con `delivery_status = 'entregado'`

5. **Template `dashboard.html`** (mejorar el existente):
   - Mantener selector de hijos
   - Para cada hijo: mini dashboard con notas, asistencia, alertas
   - Cards de acceso rapido con links funcionales
   - Notificaciones recientes

6. **Template `grades.html`**:
   - Selector de periodo
   - Tabla: Asignatura | Nota Final | Estado | Observacion
   - Promedio general destacado
   - Sin opciones de edicion

7. **Template `attendance.html`**:
   - Resumen mensual de asistencia
   - Grafico de barras: presentes vs ausentes por mes
   - Tabla de detalle: Fecha | Estado | Justificacion

8. **Template `report_cards.html`**:
   - Lista de boletines entregados
   - Periodo, fecha entrega
   - Boton descargar PDF

9. **Script de prueba `test_parent_portal.py`**:
    - Crear acudiente con hijo
    - Verificar que dashboard muestra datos correctos
    - Verificar que no puede ver datos de otros estudiantes
    - Verificar permisos

**Dependencias**: Sistema de Notas, Asistencia, Boletines (para report cards), Alertas (opcional)

**Verificacion**:
```bash
.venv\Scripts\python.exe test_parent_portal.py
```
- Acudiente ve solo datos de sus hijos
- Templates muestran datos reales
- Permisos funcionan correctamente

---

## ORDEN DE EJECUCION RECOMENDADO

```
FASE 1 (Ejecutar primero, en paralelo si es posible):
  ├── Agente 1: Sistema de Notas (independiente)
  └── Agente 2: Boletines PDF (depende de Notas, pero puede empezar templates)

FASE 2 (Ejecutar despues de Fase 1):
  ├── Agente 3: Metricas del Profesor (depende de Notas)
  ├── Agente 4: Metricas Institucionales (depende de Notas)
  └── Agente 5: Alertas Tempranas (depende de Notas, Asistencia, Observaciones)

FASE 3 (Ejecutar al final):
  ├── Agente 6: Sistema de Logros (depende de Notas)
  └── Agente 7: Portal de Acudientes (depende de Notas, Asistencia, Boletines)
```

## SCRIPT DE VERIFICACION GENERAL

Crear `test_all_modules.py` al final que ejecute:
```python
import subprocess
import sys

modules = [
    'test_notes_module.py',
    'test_report_cards.py', 
    'test_alerts_module.py',
    'test_achievements.py',
    'test_parent_portal.py'
]

for module in modules:
    print(f"\n{'='*60}")
    print(f"Probando: {module}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, module], capture_output=False)
    if result.returncode != 0:
        print(f"ERROR en {module}")
    else:
        print(f"OK: {module}")
```

## NOTAS IMPORTANTES PARA CADA AGENTE

1. **NO commitear** bajo ninguna circunstancia
2. **Usar Bootstrap 5** - NO Tailwind CSS
3. **Seguir patrones de disenno** documentados en PROGRESS.md seccion "RECOMENDACIONES DE UX/UI"
4. **Usar archivos existentes como referencia** de estilo
5. **DataTables en espanol** para todas las tablas
6. **Animaciones fadeInUp** con delays escalonados
7. **Stat cards** con iconos circulares y hover effects
8. **Badges de colores** para estados y tipos
9. **Formularios con persistencia** (form_data + errors pattern)
10. **Validacion en tiempo real** con `form-validation.js`
