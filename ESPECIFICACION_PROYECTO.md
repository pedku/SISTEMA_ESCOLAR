# 🏫 Sistema Integral de Gestión Escolar (SIGE)

## Contexto

Este proyecto nace de la evolución del sistema de acceso QR a laboratorios (`qr_access_system`). 
Se requiere un sistema completo para gestión escolar que abarque: notas, boletines, métricas docentes, 
análisis de rendimiento y portal para padres de familia.

## Institución Base (Ejemplo inicial)
- **Nombre:** Institución Educativa [Nombre]
- **Sedes:** Múltiples sedes por municipio
- **Grados:** 0° (transición) hasta 11°
- **Periodos Académicos:** 4 periodos por año lectivo
- **Escala de Calificación:** 1.0 - 5.0 (donde < 3.0 = reprobado)

---

## 📋 MODELOS DE BASE DE DATOS

### 1. Institution (Institución)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| name | String(150) | Nombre completo de la institución |
| nit | String(20) | NIT de la institución |
| address | String(200) | Dirección principal |
| phone | String(20) | Teléfono de contacto |
| email | String(100) | Correo institucional |
| logo | String(200) | Ruta del logo |
| municipality | String(100) | Municipio |
| department | String(100) | Departamento |
| resolution | String(100) | Resolución de aprobación |
| academic_year | String(20) | Año lectivo actual (ej: "2026") |
| created_at | DateTime | Fecha de creación |

### 2. Campus (Sede)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| institution_id | Integer FK | → institutions.id |
| name | String(150) | Nombre de la sede |
| code | String(20) | Código DANE de la sede |
| address | String(200) | Dirección de la sede |
| jornada | String(50) | 'mañana', 'tarde', 'completa' |
| active | Boolean | Sede activa o inactiva |

### 3. Grade (Grado)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| campus_id | Integer FK | → campuses.id |
| name | String(50) | Nombre (ej: "6-1", "11°B", "Transición A") |
| director_id | Integer FK | → users.id (profesor director de grupo) |
| academic_year | String(20) | Año lectivo |
| max_students | Integer | Capacidad máxima |

### 4. Subject (Asignatura)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| name | String(100) | Nombre (ej: "Matemáticas", "Ciencias Naturales") |
| code | String(20) | Código interno |
| grades | Relationship | Relación M:M con Grade (una materia en varios grados) |
| teachers | Relationship | Relación M:M con User (varios profesores pueden dar la misma materia) |

### 5. SubjectGrade (Asignatura en Grado)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| subject_id | Integer FK | → subjects.id |
| grade_id | Integer FK | → grades.id |
| teacher_id | Integer FK | → users.id (profesor asignado) |
| Unique | (subject_id, grade_id, teacher_id) | No repetir |

### 6. AcademicStudent (Estudiante Académico)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| user_id | Integer FK | → users.id |
| institution_id | Integer FK | → institutions.id |
| campus_id | Integer FK | → campuses.id |
| grade_id | Integer FK | → grades.id |
| document_type | String(20) | 'TI', 'CC', 'RC', 'Pasaporte' |
| document_number | String(30) | Número de identificación |
| birth_date | Date | Fecha de nacimiento |
| address | String(200) | Dirección de residencia |
| neighborhood | String(100) | Barrio |
| stratum | Integer | Estrato socioeconómico (1-6) |
| gender | String(10) | 'M', 'F', 'Otro' |
| blood_type | String(5) | Tipo de sangre |
| eps | String(100) | EPS / Salud |
| guardian_name | String(150) | Nombre del acudiente |
| guardian_phone | String(20) | Teléfono del acudiente |
| guardian_email | String(100) | Email del acudiente |
| photo | String(200) | Foto del estudiante |
| enrolled_year | String(20) | Año de matrícula |
| status | String(20) | 'activo', 'retirado', 'graduado' |

### 7. AcademicPeriod (Periodo Académico)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| institution_id | Integer FK | → institutions.id |
| name | String(50) | "Periodo 1", "Periodo 2", etc. |
| short_name | String(10) | "P1", "P2", "P3", "P4" |
| start_date | Date | Fecha de inicio |
| end_date | Date | Fecha de fin |
| is_active | Boolean | Periodo actual |
| academic_year | String(20) | Año lectivo |
| order | Integer | Orden (1, 2, 3, 4) |

### 8. GradeCriteria (Criterios de Evaluación)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| institution_id | Integer FK | → institutions.id |
| name | String(100) | "Seguimiento", "Formativo", "Cognitivo", "Procedimental" |
| weight | Float | Peso porcentual (ej: 20.0, 30.0) |
| description | String(300) | Descripción del criterio |
| order | Integer | Orden de visualización |

*Valores por defecto:*
- Seguimiento: 20%
- Formativo: 20%
- Cognitivo: 30%
- Procedimental: 30%

### 9. GradeRecord (Registro de Notas)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| student_id | Integer FK | → academic_students.id |
| subject_grade_id | Integer FK | → subject_grades.id |
| period_id | Integer FK | → academic_periods.id |
| criterion_id | Integer FK | → grade_criteria.id |
| score | Float(5,2) | Calificación (1.0 - 5.0) |
| observation | String(500) | Observación del profesor |
| created_at | DateTime | Fecha de registro |
| updated_at | DateTime | Última modificación |
| created_by | Integer FK | → users.id (quién registró) |
| locked | Boolean | Nota cerrada (no editable) |

### 10. FinalGrade (Nota Final por Periodo)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| student_id | Integer FK | → academic_students.id |
| subject_grade_id | Integer FK | → subject_grades.id |
| period_id | Integer FK | → academic_periods.id |
| final_score | Float(5,2) | Nota final calculada |
| status | String(20) | 'ganada', 'perdida', 'no evaluado' |
| observation | String(500) | Observación final |
| calculated_at | DateTime | Fecha de cálculo |

### 11. AnnualGrade (Nota Anual / Definitiva)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| student_id | Integer FK | → academic_students.id |
| subject_grade_id | Integer FK | → subject_grades.id |
| annual_score | Float(5,2) | Nota definitiva del año |
| status | String(20) | 'aprobado', 'reprobado' |
| academic_year | String(20) | Año lectivo |

### 12. Attendance (Asistencia Académica)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| student_id | Integer FK | → academic_students.id |
| subject_grade_id | Integer FK | → subject_grades.id |
| date | Date | Fecha de la clase |
| status | String(20) | 'presente', 'ausente', 'justificado', 'excusado' |
| observation | String(300) | Justificación si aplica |
| recorded_by | Integer FK | → users.id |

### 13. Observation (Observaciones de Comportamiento)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| student_id | Integer FK | → academic_students.id |
| author_id | Integer FK | → users.id (quién escribe) |
| type | String(20) | 'positiva', 'negativa', 'seguimiento', 'convivencia' |
| category | String(50) | Categoría (ej: "Disciplina", "Rendimiento", "Valores") |
| description | Text | Descripción detallada |
| date | DateTime | Fecha del incidente |
| commitments | Text | Compromisos adquiridos (si aplica) |
| notified | Boolean | Si se notificó al acudiente |

### 14. ReportCard (Boletín de Calificaciones)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| student_id | Integer FK | → academic_students.id |
| period_id | Integer FK | → academic_periods.id |
| generated_at | DateTime | Fecha de generación |
| pdf_path | String(300) | Ruta del PDF generado |
| general_observation | Text | Observación general del director de grupo |
| generated_by | Integer FK | → users.id |
| delivery_status | String(20) | 'pendiente', 'entregado' |
| delivery_date | Date | Fecha de entrega al padre |

### 15. ReportCardObservation (Observación de Boletín por Materia)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| report_card_id | Integer FK | → report_cards.id |
| subject_grade_id | Integer FK | → subject_grades.id |
| observation | String(500) | Observación del profesor para el boletín |

### 16. Achievement (Logro/Gamificación)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| name | String(100) | "Superador", "Asistencia Perfecta", "Excelencia" |
| description | String(300) | Descripción del logro |
| icon | String(100) | Icono/emoji del logro |
| criteria | String(200) | Criterio para obtenerlo |
| category | String(50) | 'académico', 'asistencia', 'comportamiento', 'mejora' |

### 17. StudentAchievement (Logro del Estudiante)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer PK | Auto-incremental |
| student_id | Integer FK | → academic_students.id |
| achievement_id | Integer FK | → achievements.id |
| earned_at | DateTime | Fecha de obtención |
| period_id | Integer FK | → academic_periods.id |

---

## 👥 ROLES DE USUARIO

| Rol | Permisos |
|-----|----------|
| **root** | Super-admin. Acceso a todo. Multi-institución. |
| **admin** | Admin de su institución. Crea usuarios, configura grados, asignaturas, periodos. |
| **coordinator** | Coordinador académico. Ve todas las notas, boletines, métricas, alertas. No edita config institucional. |
| **teacher** | Profesor. Sube notas de SUS asignaturas. Ve SUS métricas. Registra asistencia y observaciones. |
| **student** | Estudiante. Ve SUS notas, asistencia, boletines, logros. |
| **parent** | Acudiente. Ve notas/asistencia/observaciones de SUS estudiantes asignados. |
| **viewer** | Consulta general (supervisores, secretaría). Solo lectura. |

---

## 🌐 RUTAS / ENDPOINTS

### Autenticación (reutilizar del sistema actual)
```
GET/POST  /login
GET       /logout
GET       /profile
POST      /update_profile
POST      /change_password
```

### Dashboard
```
GET       /                           → Dashboard principal (diferente por rol)
GET       /dashboard                  → Dashboard con métricas
GET       /alerts                     → Alertas tempranas (coordinator, admin)
```

### Gestión Institucional (admin, root)
```
GET/POST  /institution                → Configurar institución
GET/POST  /campuses                   → CRUD de sedes
GET/POST  /grades                     → CRUD de grados
GET/POST  /subjects                   → CRUD de asignaturas
GET/POST  /assign_teacher             → Asignar profesor a materia-grado
GET/POST  /periods                    → CRUD de periodos académicos
GET/POST  /evaluation_criteria        → Configurar criterios de evaluación
```

### Gestión de Estudiantes (admin, coordinator, teacher)
```
GET/POST  /students                   → Lista de estudiantes (filtros por grado, sede)
GET/POST  /students/upload            → Carga masiva desde Excel
GET       /students/<id>              → Perfil académico del estudiante
GET/POST  /students/<id>/assign_grade → Asignar/transferir estudiante a grado
GET/POST  /students/<id>/guardian     → Datos del acudiente
```

### Sistema de Notas (teacher, coordinator, admin)
```
GET/POST  /grades/input               → Selección: profesor elige grado + materia + periodo
GET/POST  /grades/input/<sg_id>/<period_id>  → Planilla de notas (manual)
POST      /grades/upload              → Carga masiva de notas por Excel
GET       /grades/<student_id>        → Ver notas de un estudiante
GET       /grades/summary/<sg_id>/<period_id> → Resumen de notas del grupo
POST      /grades/lock                → Cerrar notas de un periodo
GET       /grades/final/<sg_id>/<period_id>   → Notas finales por periodo
GET       /grades/annual/<student_id>         → Notas anuales del estudiante
```

### Boletines (coordinator, admin)
```
GET       /report_cards               → Generar boletines
POST      /report_cards/generate      → Generar boletín individual (PDF)
POST      /report_cards/generate_bulk → Generar boletines de un grado completo
GET       /report_cards/<id>          → Ver/Descargar boletín
GET       /report_cards/history/<student_id> → Historial de boletines
```

### Asistencia (teacher)
```
GET/POST  /attendance                 → Tomar asistencia (por grado + materia)
GET       /attendance/student/<id>    → Historial de asistencia de estudiante
GET       /attendance/summary         → Resumen de asistencia del grupo
```

### Observaciones (teacher, coordinator)
```
GET/POST  /observations               → Crear observación (seleccionar estudiante)
GET       /observations/student/<id>  → Historial de observaciones de estudiante
GET       /observations/notifications → Observaciones notificadas a acudientes
POST      /observations/<id>/notify   → Notificar al acudiente
```

### Métricas y Analítica (coordinator, admin, teacher)
```
GET       /metrics/teacher            → Métricas personales del profesor
GET       /metrics/institution        → Métricas de toda la institución
GET       /metrics/heatmap            → Mapa de calor: materias/grados con más pérdidas
GET       /metrics/teacher_comparison → Comparativa anónima entre profesores
GET       /metrics/trends             → Tendencias de rendimiento por periodo
GET       /metrics/attendance         → Correlación asistencia vs rendimiento
GET       /metrics/risk_students      → Lista de estudiantes en riesgo
GET       /metrics/export             → Exportar métricas a Excel
```

### Logros / Gamificación (teacher, student)
```
GET       /achievements               → Lista de logros disponibles
POST      /achievements/award         → Otorgar logro a estudiante (teacher)
GET       /achievements/student/<id>  → Logros de un estudiante
GET       /leaderboard                → Ranking positivo (student, teacher)
```

### Portal de Acudientes (parent)
```
GET       /parent/dashboard           → Dashboard del acudiente
GET       /parent/grades/<student_id> → Notas de su acudido
GET       /parent/attendance/<student_id> → Asistencia de su acudido
GET       /parent/observations/<student_id> → Observaciones de su acudido
GET       /parent/report_cards/<student_id> → Boletines de su acudido
```

### QR Access (mantener del sistema actual)
```
POST      /qr                         → Validar QR de acceso
POST      /validate_student_access    → Validar acceso de estudiante
GET       /my_qr                      → Ver mi código QR
```

---

## 📊 SISTEMA DE CALIFICACIÓN

### Escala Numérica: 1.0 - 5.0
| Rango | Desempeño | Estado |
|-------|-----------|--------|
| 4.6 - 5.0 | Superior | ✅ Ganada |
| 4.0 - 4.5 | Alto | ✅ Ganada |
| 3.0 - 3.9 | Básico | ✅ Ganada |
| 1.0 - 2.9 | Bajo | ❌ Perdida |

### Criterios de Evaluación (configurables):
| Criterio | Peso | Descripción |
|----------|------|-------------|
| Seguimiento | 20% | Tareas, quizzes, participación diaria |
| Formativo | 20% | Trabajos, proyectos formativos |
| Cognitivo | 30% | Pruebas escritas, evaluaciones de conocimiento |
| Procedimental | 30% | Prácticas, aplicaciones, trabajos en clase |

### Nota Final del Periodo:
```
Nota Final = (Seguimiento × 0.20) + (Formativo × 0.20) + (Cognitivo × 0.30) + (Procedimental × 0.30)
```

### Nota Anual:
```
Nota Anual = (P1 + P2 + P3 + P4) / 4
```
*Configurable: algunas instituciones dan más peso a P3 y P4*

---

## 📄 BOLETÍN (PDF)

### Contenido del Boletín:
1. **Encabezado institucional**
   - Logo, nombre de la institución, resolución, NIT
   - Sede, grado, grupo
   
2. **Datos del estudiante**
   - Nombre completo, documento, foto
   
3. **Tabla de calificaciones**
   | Asignatura | P1 | P2 | P3 | P4 | DEF | Estado |
   |------------|----|----|----|----|-----|--------|
   | Matemáticas | 3.5 | 4.0 | - | - | - | - |
   | Español | 4.2 | 3.8 | - | - | - | - |

4. **Observaciones por materia**
5. **Observación general** (director de grupo)
6. **Asistencia del periodo** (presentes/ausentes)
7. **Firmas**: Director de grupo, Coordinador, Rector

---

## 🚨 SISTEMA DE ALERTAS TEMPRANAS

### Reglas de Alerta:
| Alerta | Condición | Color | Acción |
|--------|-----------|-------|--------|
| **Riesgo Académico** | Nota promedio < 3.0 en cualquier materia | 🔴 | Notificar coordinator + padre |
| **Tendencia Negativa** | Bajó >0.5 puntos entre periodos | 🟡 | Seguimiento al estudiante |
| **Inasistencia Crítica** | >20% de inasistencias en un mes | 🟠 | Notificar coordinación |
| **Grupo en Riesgo** | >30% del grupo pierde con mismo profesor | 🔴 | Revisión pedagógica |
| **Riesgo de Deserción** | Ausencias + notas bajas combinadas | 🔴 | Protocolo de deserción |
| **Mejora Destacable** | Subió >1.0 punto entre periodos | 🟢 | Felicitación + logro |

---

## 📈 MÉTRICAS DE PROFESORES

### Dashboard del Profesor:
1. **Resumen General**
   - Promedio general de sus grupos
   - % de aprobación por grupo
   - % de inasistencia de sus estudiantes
   
2. **Análisis por Grupo**
   - Distribución de notas (histograma)
   - Estudiantes en riesgo
   - Tendencia por periodo

3. **Comparativa Anónima**
   - Su rendimiento vs promedio institucional (sin nombres de otros profes)
   - Percentil en el que se encuentra

4. **Recomendaciones Automáticas**
   - "El 40% de 7-2 perdió el último examen. Considere refuerzo."
   - "3 estudiantes con baja del rendimiento. Sugerir observación."

---

## 🏆 GAMIFICACIÓN

### Logros Automáticos:
| Logro | Criterio | Icono |
|-------|----------|-------|
| Superador | Subió 1+ punto entre periodos | 📈 |
| Excelencia | Nota >= 4.5 en periodo | ⭐ |
| Asistencia Perfecta | 0 inasistencias en periodo | ✅ |
| Todo Terrain | Todas las materias ganadas | 🏅 |
| Resiliente | Recuperó una materia perdida | 💪 |
| Compañero | Ayudó a mejorar a otro | 🤝 |
| Constancia | 3 periodos seguidos >= 4.0 | 🔥 |

---

## 🗂️ ESTRUCTURA DE ARCHIVOS PROPUESTA

```
sistema_escolar/
├── app.py                          # Aplicación Flask principal
├── config.py                       # Configuración de la app
├── requirements.txt
├── .env
├── init_db.py                      # Inicialización de BD + datos semilla
│
├── models/                         # Modelos separados por módulo
│   ├── __init__.py
│   ├── user.py                     # User (reutilizar del sistema actual)
│   ├── institution.py              # Institution, Campus
│   ├── academic.py                 # Grade, Subject, SubjectGrade, AcademicStudent
│   ├── grading.py                  # AcademicPeriod, GradeCriteria, GradeRecord, FinalGrade, AnnualGrade
│   ├── attendance.py               # Attendance
│   ├── observation.py              # Observation
│   ├── report.py                   # ReportCard, ReportCardObservation
│   └── achievement.py              # Achievement, StudentAchievement
│
├── routes/                         # Rutas separadas por módulo
│   ├── __init__.py
│   ├── auth.py                     # Login, logout, profile
│   ├── dashboard.py                # Dashboards por rol
│   ├── institution.py              # Config institucional
│   ├── students.py                 # Gestión de estudiantes
│   ├── grades.py                   # Sistema de notas
│   ├── report_cards.py             # Boletines
│   ├── attendance.py               # Asistencia
│   ├── observations.py             # Observaciones
│   ├── metrics.py                  # Analítica y métricas
│   ├── achievements.py             # Logros
│   ├── parent.py                   # Portal de acudientes
│   └── qr.py                       # Acceso QR (del sistema actual)
│
├── services/                       # Lógica de negocio
│   ├── __init__.py
│   ├── grade_calculator.py         # Cálculo de notas, ponderaciones
│   ├── report_card_generator.py    # Generación de PDFs de boletines
│   ├── excel_handler.py            # Carga masiva (estudiantes + notas)
│   ├── alert_engine.py             # Motor de alertas tempranas
│   ├── metrics_engine.py           # Motor de métricas y análisis
│   ├── achievement_engine.py       # Verificación automática de logros
│   └── username_generator.py       # Generador de usernames
│
├── utils/                          # Utilidades
│   ├── __init__.py
│   ├── decorators.py               # @role_required, @login_required
│   ├── pdf_generator.py            # Generación de PDFs
│   ├── charts.py                   # Gráficos para dashboards
│   └── validators.py               # Validaciones de datos
│
├── templates/                      # Templates HTML
│   ├── base.html                   # Layout base
│   ├── login.html
│   ├── 404.html / 500.html
│   │
│   ├── dashboard/                  # Dashboards por rol
│   │   ├── admin.html
│   │   ├── coordinator.html
│   │   ├── teacher.html
│   │   ├── student.html
│   │   └── parent.html
│   │
│   ├── institution/                # Gestión institucional
│   │   ├── config.html
│   │   ├── campuses.html
│   │   ├── grades.html
│   │   ├── subjects.html
│   │   ├── periods.html
│   │   └── criteria.html
│   │
│   ├── students/                   # Gestión de estudiantes
│   │   ├── list.html
│   │   ├── profile.html
│   │   ├── upload.html
│   │   └── guardian.html
│   │
│   ├── grades/                     # Sistema de notas
│   │   ├── select.html             → Selección grado+materia+periodo
│   │   ├── input.html              → Planilla de notas manual
│   │   ├── upload.html             → Carga masiva Excel
│   │   ├── summary.html            → Resumen del grupo
│   │   └── student_view.html       → Notas de un estudiante
│   │
│   ├── report_cards/               # Boletines
│   │   ├── generate.html
│   │   ├── view.html
│   │   └── history.html
│   │
│   ├── attendance/                 # Asistencia
│   │   ├── take.html
│   │   └── summary.html
│   │
│   ├── observations/               # Observaciones
│   │   ├── create.html
│   │   └── student_history.html
│   │
│   ├── metrics/                    # Métricas
│   │   ├── teacher.html            → Métricas del profesor
│   │   ├── institution.html        → Métricas institucionales
│   │   ├── heatmap.html            → Mapa de calor
│   │   ├── teacher_comparison.html → Comparativa
│   │   └── risk_students.html      → Estudiantes en riesgo
│   │
│   ├── achievements/               # Logros
│   │   ├── list.html
│   │   └── student_achievements.html
│   │
│   ├── parent/                     → Portal de acudientes
│   │   ├── dashboard.html
│   │   ├── grades.html
│   │   ├── attendance.html
│   │   └── report_cards.html
│   │
│   └── qr/                         → Acceso QR (del sistema actual)
│       ├── validate.html
│       └── my_qr.html
│
├── static/
│   ├── css/
│   │   ├── main.css                → Estilos principales
│   │   ├── dashboard.css
│   │   ├── grades.css
│   │   ├── metrics.css
│   │   └── report_card.css         → Estilos para PDF de boletín
│   │
│   ├── js/
│   │   ├── main.js                 → DataTables, selects, etc.
│   │   ├── grades_input.js         → Planilla de notas (cálculo en vivo)
│   │   ├── metrics.js              → Gráficos de métricas
│   │   └── alerts.js               → Sistema de alertas en tiempo real
│   │
│   ├── images/
│   │   ├── logo.png
│   │   └── achievements/           → Iconos de logros
│   │
│   └── vendor/                     → Librerías de terceros
│       ├── bootstrap/
│       ├── DataTables/
│       ├── Chart.js                → Para gráficos
│       └── SweetAlert2/
│
├── uploads/                        → Archivos subidos
│   ├── logos/                      → Logos de instituciones
│   ├── photos/                     → Fotos de estudiantes
│   ├── excel_imports/              → Excels importados
│   └── report_cards/               → PDFs de boletines generados
│
├── migrations/                     → Flask-Migrate
└── tests/                          → Tests unitarios
```

---

## 🎨 DISEÑO / UX

### Principios:
- **Mobile-first**: Muchos profesores usarán celular
- **DataTables**: Todas las tablas con búsqueda, ordenamiento, paginación
- **SweetAlert2**: Confirmaciones y alertas bonitas
- **Bootstrap 5**: Framework CSS consistente
- **Colores semánticos**: Verde=bueno, Rojo=malo, Amarillo=alerta
- **Iconografía**: Iconos claros por sección (notas 📝, asistencia 📋, boletín 📄)

---

## 🔐 SEGURIDAD

- Hash de contraseñas con `werkzeug.security`
- CSRF protection en todos los formularios
- Rate limiting en endpoints críticos
- Validación de archivos Excel (solo .xlsx, max 10MB)
- Logs de auditoría: quién cambió qué nota y cuándo
- Notas "locked": una vez cerradas, solo admin puede desbloquear
- Roles verificados en cada ruta con decoradores

---

## 📦 DEPENDENCIAS PRINCIPALES

```
Flask==3.1.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-WTF==1.2.1
Flask-Limiter==3.5.0
Flask-Cors==4.0.0
psycopg2==2.9.11
pandas==2.x
openpyxl==3.1.x
werkzeug==3.1.3
pytz
python-dotenv
WeasyPrint o pdfkit (para generar PDFs de boletines)
matplotlib o plotly (para gráficos de métricas)
```

---

## 🚀 PASOS PARA INICIAR EL PROYECTO

### 1. Crear carpeta del proyecto
```
mkdir sistema_escolar
cd sistema_escolar
```

### 2. Crear entorno virtual
```
python -m venv .venv
.venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias
```
pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-WTF Flask-Limiter Flask-Cors psycopg2-binary pandas openpyxl python-dotenv pytz werkzeug
```

### 4. Estructura de carpetas
```
mkdir models routes services utils templates static uploads migrations tests
```

### 5. Crear .env
```
SECRET_KEY=<tu_clave_secreta>
DATABASE_USER=postgres
DATABASE_PASSWORD=peku72
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=sistema_escolar
```

### 6. Crear app.py mínimo
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 7. Crear base de datos en PostgreSQL
```sql
CREATE DATABASE sistema_escolar;
```

### 8. Ejecutar migraciones
```
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

---

## 📌 NOTAS IMPORTANTES

1. **Multi-institución**: El sistema está diseñado para soportar múltiples instituciones, pero se inicia con una.
2. **Migración de datos**: Los usuarios existentes del sistema QR se pueden migrar manteniendo sus QR codes.
3. **QR Access**: El módulo de acceso QR se mantiene intacto, solo se conecta al modelo de Student.
4. **Año Lectivo**: Todo está vinculado al año lectivo para poder tener históricos.
5. **Escalabilidad**: Los servicios están separados para poder agregar más funcionalidades después.
