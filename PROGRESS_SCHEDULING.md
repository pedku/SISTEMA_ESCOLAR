# SIGE - Sistema Integral de Gestion Escolar

## Ultimo avance

- **Ultima actualizacion**: 2026-04-13
- **Estado**: ~99% Implementado
- **Version del codigo**: rama main
- **Tipo de proyecto**: Sistema de gestion escolar multi-institucional
- **Stack**: Flask + Bootstrap 5 + Chart.js + DataTables (ESPAÃ'OL) + SQLite
- **Sesion actual**: Implementacion de sistema de matricula, asignacion de profesores y generacion de horarios
- **Total errores corregidos acumulados**: 40+

---

## SESION ACTUAL: Sistema Completo de Matricula y Horarios (2026-04-13)

### Resumen de la Funcionalidad
Se ha implementado un sistema completo para:
1. **Matricular estudiantes** en materias de manera optima
2. **Asignar profesores** a materias y grados
3. **Asignar materias** a grados/cursos
4. **Generar horarios automaticamente** para profesores y estudiantes
5. **Asignar salones** a cada clase en el horario
6. **Visualizar horarios** por profesor, estudiante o grado

### Nuevos Modelos de Base de Datos (5 tablas)

| Modelo | Tabla | Descripcion |
|--------|-------|-------------|
| **Classroom** | `classrooms` | Gestion de salones/aulas por sede |
| **StudentEnrollment** | `student_enrollments` | Matricula de estudiantes en materias |
| **TeacherSubjectAssignment** | `teacher_subject_assignments` | Asignacion de profesores a materias |
| **Schedule** | `schedules` | Horarios de clases (materia + salon + hora) |
| **ScheduleBlock** | `schedule_blocks` | Bloques de tiempo para generacion de horarios |

### Nuevas Rutas Implementadas (26 endpoints)

#### Matricula de Estudiantes
- `/scheduling/enrollments` - Lista de matriculas
- `/scheduling/enrollments/new` - Crear matricula (seleccion multiple de estudiantes y materias)
- `/scheduling/enrollments/<id>/edit` - Editar matricula
- `/scheduling/enrollments/<id>/delete` - Eliminar matricula

#### Asignacion de Profesores
- `/scheduling/assignments` - Lista de asignaciones
- `/scheduling/assignments/new` - Asignar profesor a materia
- `/scheduling/assignments/<id>/edit` - Editar asignacion
- `/scheduling/assignments/<id>/delete` - Eliminar asignacion

#### Materias por Grado
- `/scheduling/subject-grades` - Lista de materias asignadas a grados
- `/scheduling/subject-grades/new` - Asignar materias a grados (multiple)
- `/scheduling/subject-grades/<id>/delete` - Eliminar asignacion

#### Gestion de Salones
- `/scheduling/classrooms` - Lista de salones
- `/scheduling/classrooms/new` - Crear salon
- `/scheduling/classrooms/<id>/edit` - Editar salon
- `/scheduling/classrooms/<id>/delete` - Eliminar salon

#### Generacion de Horarios
- `/scheduling/schedules` - Ver horarios (filtrado por rol: admin, teacher, student)
- `/scheduling/schedules/generate` - Vista para generar horarios
- `/scheduling/schedules/generate/run` - Ejecutar algoritmo de generacion automatica
- `/scheduling/schedules/<id>/delete` - Eliminar horario

#### Bloques de Tiempo
- `/scheduling/blocks` - Lista de bloques horarios
- `/scheduling/blocks/new` - Crear bloque
- `/scheduling/blocks/<id>/edit` - Editar bloque
- `/scheduling/blocks/<id>/delete` - Eliminar bloque

#### APIs AJAX
- `/scheduling/api/students/by-grade/<grade_id>` - Obtener estudiantes por grado
- `/scheduling/api/subject-grades/by-grade/<grade_id>` - Obtener materias por grado

### Templates Creados (12 templates)

| Modulo | Templates | Estado |
|--------|-----------|--------|
| Enrollments | list.html, form.html | Completos con Bootstrap 5 |
| Assignments | list.html, form.html | Completos con Bootstrap 5 |
| Subject Grades | list.html, form.html | Completos con Bootstrap 5 |
| Classrooms | list.html, form.html | Completos con Bootstrap 5 |
| Schedules | list.html, generate.html | Completos con Bootstrap 5 |
| Blocks | list.html, form.html | Completos con Bootstrap 5 |

### Caracteristicas Implementadas

#### 1. Sistema de Matricula Optimo
- **Matricula multiple**: Seleccionar varios estudiantes y varias materias simultaneamente
- **Validacion inteligente**: Evita matriculas duplicadas
- **Filtros avanzados**: Por grado, materia, estado y aÃ±o academico
- **Estadisticas en tiempo real**: Total de matriculas, matriculas activas
- **Carga AJAX de estudiantes**: Los estudiantes se cargan dinamicamente al seleccionar un grado

#### 2. Asignacion de Profesores
- **Asignacion directa**: Profesor -> Materia -> Grado
- **Integracion con SubjectGrade**: Crea automaticamente el SubjectGrade si no existe
- **Estado de asignacion**: Activo, inactivo, temporal
- **Control de conflictos**: Verifica que el profesor no tenga conflictos antes de asignar

#### 3. Asignacion de Materias a Grados
- **Asignacion multiple**: Seleccionar varios grados y varias materias
- **Profesor opcional**: Se puede asignar el profesor en el mismo paso o despues
- **Validacion de duplicados**: Evita asignaciones repetidas

#### 4. Generador Automatico de Horarios
El sistema incluye un **algoritmo inteligente de generacion de horarios** que:
- **Evita conflictos de profesores**: Un profesor no puede estar en dos lugares al mismo tiempo
- **Evita conflictos de salones**: Un salon no puede tener dos clases simultaneas
- **Respeta bloques de tiempo**: Usa los bloques definidos para cada sede
- **Asigna salones automaticamente**: Distribuye clases en salones disponibles
- **Generacion configurable**: Puede generar para toda la institucion, una sede o un grado especifico
- **Resultados detallados**: Muestra cantidad de clases asignadas y conflictos encontrados

#### 5. Gestion de Salones
- **Tipos de salon**: Aula, laboratorio, auditorio, cancha
- **Informacion completa**: Capacidad, edificio, piso, recursos disponibles
- **Filtros por sede**: Organizacion por campus
- **Estadisticas**: Total de salones, aulas, laboratorios

#### 6. Visualizacion de Horarios
- **Vista de grilla**: Horarios organizados por dia y hora
- **Filtrado por rol**:
  - **Admin/Coordinator**: Ven todos los horarios
  - **Teacher**: Ven solo sus horarios asignados
  - **Student**: Ven los horarios de su grado
- **Informacion completa**: Cada muestra materia, profesor, salon y grado
- **Tarjetas visuales**: Formato atractivo con iconos y colores

#### 7. Bloques de Tiempo
- **Definicion flexible**: Cada sede puede tener sus propios bloques horarios
- **Bloques de descanso**: Recreos, almuerzos (no se asignan con materias)
- **Orden configurable**: Se puede definir el orden de los bloques
- **Ejemplo incluido**: Template muestra ejemplo tipico de bloques

### Flujo de Trabajo Completo

```
1. CREAR ESTRUCTURA BASE
   ├─> Crear sedes (campuses)
   ├─> Crear grados (grades) por sede
   └─> Crear materias (subjects)

2. ASIGNAR MATERIAS A GRADOS
   └─> /scheduling/subject-grades/new
       └─> Seleccionar grados + materias + profesor opcional

3. ASIGNAR PROFESORES A MATERIAS
   └─> /scheduling/assignments/new
       └─> Seleccionar grado + materia + profesor

4. MATRICULAR ESTUDIANTES
   └─> /scheduling/enrollments/new
       └─> Seleccionar grado -> carga estudiantes -> seleccionar materias

5. CREAR SALONES
   └─> /scheduling/classrooms/new
       └─> Definir salones por sede con capacidad y tipo

6. DEFINIR BLOQUES DE TIEMPO
   └─> /scheduling/blocks/new
       └─> Crear bloques horarios para cada sede

7. GENERAR HORARIOS
   └─> /scheduling/schedules/generate
       └─> Ejecutar generador automatico
       
8. VISUALIZAR HORARIOS
   └─> /scheduling/schedules
       └─> Ver horarios por rol (admin/teacher/student)
```

### Algoritmo de Generacion de Horarios

El algoritmo implementado funciona de la siguiente manera:

```python
1. Obtener grados a programar (todos, por sede, o grado especifico)
2. Obtener bloques de tiempo de la sede
3. Obtener salones disponibles
4. Para cada grado:
   a. Obtener todas las SubjectGrade asignadas
   b. Crear slots disponibles (dia x bloque)
   c. Para cada SubjectGrade:
      - Verificar si ya tiene horario
      - Para cada slot disponible:
        * Verificar disponibilidad del profesor
        * Verificar disponibilidad del salon
        * Si ambos disponibles -> crear Schedule
        * Si no -> intentar otro slot
5. Retornar estadisticas (asignados, conflictos)
```

### Migration Script Creado
- **Archivo**: `migrate_scheduling.py`
- **Funcion**: Crear las 5 nuevas tablas en la base de datos
- **Ejecucion**: `python migrate_scheduling.py`

### Archivos Creados/Modificados

#### Nuevos Archivos (3 archivos principales)
1. **`models/scheduling.py`** - 5 nuevos modelos de base de datos
2. **`routes/scheduling.py`** - Blueprint completo con 26 endpoints
3. **`migrate_scheduling.py`** - Script de migracion

#### Templates Creados (12 archivos)
- `templates/scheduling/enrollments/list.html`
- `templates/scheduling/enrollments/form.html`
- `templates/scheduling/assignments/list.html`
- `templates/scheduling/assignments/form.html`
- `templates/scheduling/subject_grades/list.html`
- `templates/scheduling/subject_grades/form.html`
- `templates/scheduling/classrooms/list.html`
- `templates/scheduling/classrooms/form.html`
- `templates/scheduling/schedules/list.html`
- `templates/scheduling/schedules/generate.html`
- `templates/scheduling/blocks/list.html`
- `templates/scheduling/blocks/form.html`

#### Archivos Modificados (3 archivos)
1. **`app.py`** - Agregado registro del blueprint `scheduling_bp`
2. **`models/academic.py`** - Agregadas relaciones a SubjectGrade (enrollments, teacher_assignment, schedules)
3. **`DOCUMENTATION.md`** - Documentacion actualizada con nuevos modelos y rutas

### Estadisticas del Modulo

| Metrica | Valor |
|---------|-------|
| Modelos nuevos | 5 |
| Tablas nuevas | 5 |
| Endpoints HTTP | 26 |
| Templates HTML | 12 |
| Lineas de codigo Python (scheduling.py) | ~950 |
| Lineas de codigo Python (models) | ~200 |
| Lineas de templates HTML | ~1800 |
| Rutas API AJAX | 2 |
| Roles con acceso | root, admin, coordinator, teacher, student |

### Integracion con Modulos Existentes

El nuevo modulo se integra perfectamente con:
- **Modulo de Estudiantes**: Matricula estudiantes existentes
- **Modulo de Institution**: Usa grados, sedes y materias existentes
- **Modulo de Users**: Asigna profesores (role=teacher)
- **Modulo de Grades**: SubjectGrade ahora tiene relaciones extendidas
- **Modulo de Attendance**: Puede usar horarios para tomar asistencia
- **Modulo de Observations**: Profesores pueden ver horarios de sus clases

### Mejoras Futuras Sugeridas

1. **Algoritmo de optimizacion**: Usar algoritmos geneticos o de optimizacion para mejorar la distribucion
2. **Restricciones avanzadas**: 
   - Materias que requieren laboratorios especificos
   - Profesores con disponibilidad limitada
   - Estudiantes con conflictos de horario
3. **Exportar horarios**: Generar PDF de horarios por estudiante/profesor/grado
4. **Notificacion automatica**: Notificar a profesores y estudiantes cuando se asignen horarios
5. **Ajuste manual**: Interfaz drag-and-drop para ajustar horarios manualmente
6. **Rotacion de salones**: Sistema para rotar salones periodicamente
7. **Validacion de capacidad**: Verificar que salones no excedan capacidad

---

## COMO PROBAR EL NUEVO MODULO

```bash
cd "c:\Users\PEKU\Desktop\PROYECTO COLEGIO\SISTEMA_ESCOLAR"

# 1. Ejecutar migracion para crear nuevas tablas
.venv\Scripts\python.exe migrate_scheduling.py

# 2. Iniciar aplicacion
.venv\Scripts\python.exe app.py
```

**URL**: http://localhost:5000
**Login**: `root` / `root123`

**Rutas para probar**:
- Matriculas: http://localhost:5000/scheduling/enrollments
- Asignaciones: http://localhost:5000/scheduling/assignments
- Materias por grado: http://localhost:5000/scheduling/subject-grades
- Salones: http://localhost:5000/scheduling/classrooms
- Generar horarios: http://localhost:5000/scheduling/schedules/generate
- Ver horarios: http://localhost:5000/scheduling/schedules
- Bloques: http://localhost:5000/scheduling/blocks

---

## ESTADO ACTUAL DEL PROYECTO

| Modulo | Progreso | Notas |
|--------|----------|-------|
| Autenticacion | 100% | Completo |
| Dashboard | 100% | 7 dashboards por rol |
| Institucion | 100% | CRUD completo |
| Usuarios | 100% | CRUD + Excel |
| Estudiantes | 100% | CRUD + Excel |
| Notas | 95% | Completo |
| Asistencia | 100% | Completo |
| Observaciones | 100% | Completo |
| Boletines PDF | 90% | Completo |
| Metricas | 90% | Completo |
| Alertas | 95% | Completo |
| Logros | 95% | Completo |
| Portal Padres | 95% | Completo |
| **Programacion y Horarios** | **95%** | **NUEVO - Completo** |
| QR Access | 15% | Placeholder |
| **TOTAL** | **~98%** | |

---

**Documentacion actualizada completamente con el nuevo modulo de programacion y horarios**
