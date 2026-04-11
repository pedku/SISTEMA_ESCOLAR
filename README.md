# SIGE - Sistema Integral de Gestión Escolar

Sistema completo para la gestión académica de instituciones educativas, desarrollado con Flask (Python).

## Características

- ✅ Autenticación y autorización multi-rol
- ✅ Gestión institucional (sedes, grados, asignaturas, periodos)
- ✅ Gestión de estudiantes (registro, perfil, acudientes)
- ✅ Sistema de notas con criterios de evaluación ponderados
- ✅ Boletines de calificaciones en PDF
- ✅ Control de asistencia
- ✅ Observaciones de comportamiento
- ✅ Métricas y análisis de rendimiento
- ✅ Sistema de logros/gamificación
- ✅ Portal para padres de familia
- ✅ Carga masiva de datos desde Excel
- ✅ Alertas tempranas de riesgo académico
- ✅ Sistema de acceso QR

## Requisitos

- Python 3.9+
- PostgreSQL
- pip

## Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar base de datos:**
Crear la base de datos en PostgreSQL:
```sql
CREATE DATABASE sistema_escolar;
```

3. **Configurar variables de entorno:**
Editar el archivo `.env` y ajustar las credenciales de la base de datos.

4. **Inicializar la base de datos:**
```bash
python init_db.py
```

Esto creará todas las tablas y datos semilla incluyendo:
- Usuario root: `root` / `root123`
- Usuario admin: `admin` / `admin123`
- Usuario coordinador: `coordinator` / `coord123`
- Usuario profesor: `teacher` / `teacher123`

## Ejecución

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

## Estructura del Proyecto

```
sistema_escolar/
├── app.py                     # Aplicación principal
├── config.py                  # Configuración
├── init_db.py                 # Inicialización de BD
├── requirements.txt           # Dependencias
├── .env                       # Variables de entorno
│
├── models/                    # Modelos de datos
│   ├── user.py               # Usuarios y autenticación
│   ├── institution.py        # Institución y sedes
│   ├── academic.py           # Grados, asignaturas, estudiantes
│   ├── grading.py            # Sistema de notas
│   ├── attendance.py         # Asistencia
│   ├── observation.py        # Observaciones
│   ├── report.py             # Boletines
│   └── achievement.py        # Logros
│
├── routes/                    # Rutas por módulo
│   ├── auth.py               # Autenticación
│   ├── dashboard.py          # Dashboards
│   ├── institution.py        # Gestión institucional
│   ├── students.py           # Gestión de estudiantes
│   ├── grades.py             # Sistema de notas
│   ├── report_cards.py       # Boletines
│   ├── attendance.py         # Asistencia
│   ├── observations.py       # Observaciones
│   ├── metrics.py            # Métricas
│   ├── achievements.py       # Logros
│   ├── parent.py             # Portal padres
│   └── qr.py                 # Acceso QR
│
├── services/                  # Lógica de negocio
├── utils/                     # Utilidades
├── templates/                 # Plantillas HTML
├── static/                    # Archivos estáticos
├── uploads/                   # Archivos subidos
├── migrations/                # Migraciones de BD
└── tests/                     # Pruebas
```

## Roles de Usuario

| Rol | Descripción |
|-----|-------------|
| **root** | Super-administrador, acceso total |
| **admin** | Administrador de institución |
| **coordinator** | Coordinador académico |
| **teacher** | Profesor |
| **student** | Estudiante |
| **parent** | Acudiente / Padre |
| **viewer** | Solo lectura |

## Sistema de Calificación

- **Escala:** 1.0 - 5.0
- **Aprobatorio:** 3.0
- **Criterios:**
  - Seguimiento: 20%
  - Formativo: 20%
  - Cognitivo: 30%
  - Procedimental: 30%

### Niveles de Desempeño

| Rango | Nivel |
|-------|-------|
| 4.6 - 5.0 | Superior |
| 4.0 - 4.5 | Alto |
| 3.0 - 3.9 | Básico |
| 1.0 - 2.9 | Bajo |

## Desarrollo

### Agregar migraciones:
```bash
flask db migrate -m "descripción"
flask db upgrade
```

### Ejecutar en modo desarrollo:
```bash
set FLASK_ENV=development
python app.py
```

## Tecnologías

- **Backend:** Flask (Python)
- **Base de datos:** PostgreSQL + SQLAlchemy
- **Frontend:** Bootstrap 5, DataTables, Chart.js
- **PDF:** WeasyPrint
- **Alertas:** SweetAlert2

## Licencia

Proyecto educativo de código abierto.
