# 📑 PLAN DE INTEGRACIÓN QR - SISTEMA ESCOLAR (SIGE)

> **Versión**: 1.0 (Evaluada y Refinada)
> **Referencia Técnica**: PROYECTO-LAB
> **Estado**: Listo para Implementación

---

## 🎯 Objetivo General
Implementar un sistema de acceso y verificación de identidad mediante códigos QR, compatible con el protocolo de hardware de **PROYECTO-LAB**, integrando la validación con los horarios (`Schedule`) y salones (`Classroom`) del SIGE.

---

## 🛠️ Arquitectura Técnica

### 1. Modelos de Datos (`models/qr_access.py`)
- **`QRToken`**:
    - `user_id`: Relación con el usuario.
    - `token`: String único (token de acceso).
    - `is_active`: Estado del token.
    - `created_at`: Marca de tiempo de generación.
- **`QRAccessLog`**:
    - `user_id`: Usuario que intentó acceder.
    - `classroom_id`: Salón donde se escaneó.
    - `timestamp`: Fecha y hora del evento.
    - `status`: Resultado (`authorized`, `denied`, `invalid_token`).

### 2. Servicio Core (`services/qr_service.py`)
Clase `QRService` encargada de:
- Generar tokens únicos y seguros.
- Validar tokens contra la base de datos.
- **Lógica de Cruce de Horarios**: Verificar si el usuario tiene permiso en el salón `X` en el día y hora `Y`.

### 3. API de Validación (Protocolo PROYECTO-LAB)
Endpoint: `POST /qr/validate`
- **Request (JSON)**:
  ```json
  {
    "labID": "Nombre del Salón",
    "qr": "Token del Usuario"
  }
  ```
- **Response (JSON)**:
  ```json
  {
    "status": "success | unauthorized | error",
    "labID": "Nombre del Salón",
    "message": "Mensaje descriptivo del resultado"
  }
  ```

---

## 🚀 Fases de Implementación

### Fase 1: Infraestructura y Modelado
1. Crear el archivo `models/qr_access.py`.
2. Registrar los modelos en `models/__init__.py`.
3. Ejecutar migración de base de datos (`flask db migrate`).

### Fase 2: Lógica y Servicios
1. Implementar `QRService` con lógica de validación temporal (Scheduling).
2. Crear rutas en `routes/qr.py`.
3. **Simulador de Escaneo**: Crear `GET /qr/simulator` restringido **exclusivamente para usuario ROOT**, permitiendo probar el sistema sin lector físico.

### Fase 3: Interfaz de Usuario (UX)
1. Desarrollar `templates/qr/my_qr.html` con diseño Glassmorphism.
2. Añadir botón de descarga de carnet digital.
3. Integrar badges de estado en el perfil del estudiante.

---

## 🛡️ Seguridad y Control
- **Rate Limiting**: Protección contra escaneos masivos en el endpoint de validación.
- **Rotación**: Al regenerar un QR, el anterior queda invalidado permanentemente.
- **Logging**: Cada intento de acceso queda registrado para analítica de asistencia.

---

## 🧪 Plan de Pruebas
1. **Prueba Unitaria**: Validar que el token se asocie correctamente al usuario.
2. **Prueba de Horario**: Intentar acceder a un salón fuera de la hora asignada (debe retornar `unauthorized`).
3. **Prueba de Integración**: Usar el simulador ROOT para verificar el registro en `QRAccessLog`.
