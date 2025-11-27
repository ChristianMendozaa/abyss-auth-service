# Auth Service - Microservicio de Autenticación

Microservicio completo de autenticación y autorización basado en roles (RBAC) desarrollado con FastAPI, utilizando Supabase para autenticación y PostgreSQL para persistencia de datos.

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura](#arquitectura)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Base de Datos](#base-de-datos)
- [Autenticación y Autorización](#autenticación-y-autorización)
- [API Endpoints](#api-endpoints)
- [Flujos de Trabajo](#flujos-de-trabajo)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Colección Postman](#colección-postman)

## 🎯 Descripción General

Este servicio proporciona un sistema completo de autenticación y autorización multi-empresa con las siguientes características:

- **Autenticación mediante HTTP-only cookies** usando Supabase Auth
- **Gestión multi-empresa** con dueños y empleados
- **Sistema de roles y permisos (RBAC)** flexible y granular
- **Validación de datos** con Pydantic
- **Operaciones asíncronas** con SQLAlchemy async
- **Control de acceso basado en permisos** (dueños tienen acceso completo)

## 🏗️ Arquitectura

El servicio está organizado siguiendo principios de arquitectura modular:

```
auth-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación FastAPI principal
│   ├── config.py            # Configuración y variables de entorno
│   ├── database.py          # Configuración de SQLAlchemy async
│   ├── deps.py              # Dependencias y utilidades de autenticación
│   ├── models/              # Modelos SQLAlchemy (ORM)
│   │   ├── empresa.py
│   │   ├── usuario.py
│   │   ├── rol.py
│   │   └── permiso.py
│   ├── schemas/             # Schemas Pydantic (validación)
│   │   ├── auth.py
│   │   ├── empresa.py
│   │   ├── usuario.py
│   │   ├── usuario_rol.py
│   │   ├── rol.py
│   │   └── permiso.py
│   ├── routers/             # Endpoints de la API
│   │   ├── auth.py
│   │   ├── empresa.py
│   │   ├── usuarios.py
│   │   ├── roles.py
│   │   └── permisos.py
│   └── services/            # Lógica de negocio
│       ├── auth_service.py
│       └── supabase_service.py
├── requirements.txt
├── postman_collection.json
└── README.md
```

## 🛠️ Tecnologías Utilizadas

- **FastAPI** (0.115.0+): Framework web moderno y rápido
- **SQLAlchemy** (2.0.36+): ORM asíncrono para PostgreSQL
- **psycopg** (3.2.0+): Driver async para PostgreSQL (Python 3.13 compatible)
- **Supabase** (2.8.0+): Backend para autenticación y gestión de usuarios
- **Pydantic** (2.10.0+): Validación de datos y serialización
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Python 3.13+**: Lenguaje de programación

## 📦 Requisitos Previos

- Python 3.13 o superior
- PostgreSQL (proporcionado por Supabase)
- Cuenta de Supabase con proyecto activo
- pip (gestor de paquetes de Python)

## 🚀 Instalación

1. **Clonar el repositorio** (o asegúrate de estar en el directorio del proyecto)

2. **Crear entorno virtual:**
```bash
python -m venv .venv
```

3. **Activar entorno virtual:**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

1. **Crear archivo `.env` en la raíz del proyecto:**

```env
# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key_aqui

# JWT Configuration
JWT_SECRET=tu_jwt_secret_aqui

# Cookie Configuration
COOKIE_NAME=auth_tokens

# Database Configuration (PostgreSQL desde Supabase)
# Opción 1: Conexión directa
DATABASE_URL=postgresql://postgres:TU_PASSWORD@db.TU_PROJECT_REF.supabase.co:5432/postgres

# Opción 2: Connection Pooler (recomendado para producción)
# DATABASE_URL=postgresql://postgres.TU_PROJECT_REF:TU_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

2. **Obtener credenciales de Supabase:**
   - Ve a tu proyecto en [Supabase Dashboard](https://supabase.com/dashboard)
   - Settings > API: Copia `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY`
   - Settings > Database > Connection string: Copia la URL de PostgreSQL

3. **Configurar base de datos:**
   - Las tablas y secuencias ya deben existir en tu base de datos de Supabase
   - El servicio usa las tablas exactamente como están definidas (ver sección Base de Datos)

## 📁 Estructura del Proyecto

### Models (app/models/)
Definen la estructura de la base de datos usando SQLAlchemy:
- `empresa.py`: Modelo de empresas
- `usuario.py`: Modelo de usuarios
- `rol.py`: Modelos de roles y relaciones (Rol, RolPermiso, UsuarioRol)
- `permiso.py`: Modelo de permisos globales

### Schemas (app/schemas/)
Definen la validación y serialización con Pydantic:
- Request schemas: Para validar datos de entrada
- Response schemas: Para estructurar respuestas de la API
- Incluyen validaciones de longitud según restricciones de la BD

### Routers (app/routers/)
Contienen todos los endpoints de la API organizados por dominio:
- `auth.py`: Autenticación (registro, login, logout, me)
- `empresa.py`: Gestión de empresas (GET, PUT, DELETE)
- `usuarios.py`: CRUD de empleados y gestión de roles de usuario
- `roles.py`: CRUD de roles con creación de permisos inline
- `permisos.py`: CRUD de permisos globales

### Services (app/services/)
Contienen la lógica de negocio:
- `auth_service.py`: Lógica de autenticación y registro
- `supabase_service.py`: Cliente de Supabase

### Dependencies (app/deps.py)
Utilidades y dependencias reutilizables:
- `get_current_user()`: Obtiene y valida usuario autenticado desde cookie
- `require_permission(action, resource)`: Valida permisos específicos
- `require_owner()`: Requiere que el usuario sea dueño
- `CurrentUser`: Clase contenedora con usuario, empresa, roles y permisos

## 🗄️ Base de Datos

### Estructura de Tablas

El servicio utiliza las siguientes tablas (ya deben existir en tu base de datos):

#### `empresas`
- `id_empresa` (PK, Sequence)
- `nombre` (VARCHAR 30)
- `razon_social` (VARCHAR 20)
- `nit` (VARCHAR 20)
- `telefono` (VARCHAR 15)
- `email` (VARCHAR 50)
- `direccion` (VARCHAR 300)
- `estado` (BOOLEAN)
- `fecha_creacion` (TIMESTAMPTZ)

#### `usuarios`
- `id_usuario` (PK, Sequence)
- `auth_uid` (UUID, UNIQUE) - ID de Supabase Auth
- `nombre` (VARCHAR 30)
- `apellido` (VARCHAR 30)
- `email` (VARCHAR 50)
- `es_dueno` (BOOLEAN)
- `estado` (BOOLEAN)
- `fecha_creacion` (TIMESTAMPTZ)
- `empresas_id_empresa` (FK → empresas)

#### `permisos`
- `id_permiso` (PK, Sequence)
- `accion` (VARCHAR 30) - Ej: "create", "read", "update", "delete"
- `recurso` (VARCHAR 30) - Ej: "usuario", "empresa", "rol"

#### `roles`
- `id_rol` (PK, Sequence)
- `nombre` (VARCHAR 30)
- `descripcion` (VARCHAR 300)
- `empresas_id_empresa` (FK → empresas)

#### `roles_permisos` (tabla de unión)
- `permisos_id_permiso` (PK, FK → permisos)
- `roles_id_rol` (PK, FK → roles)

#### `usuarios_roles` (tabla de unión)
- `usuarios_id_usuario` (PK, FK → usuarios)
- `roles_id_rol` (PK, FK → roles)

## 🔐 Autenticación y Autorización

### Flujo de Autenticación

1. **Registro de Dueño:**
   - Usuario envía datos personales + datos de empresa
   - Se crea usuario en Supabase Auth
   - Se crea empresa en PostgreSQL
   - Se crea usuario con `es_dueno=true` en PostgreSQL

2. **Login:**
   - Usuario envía email y password
   - Se valida con Supabase Auth
   - Se obtiene `access_token` y `refresh_token`
   - Se establece cookie HTTP-only con el `access_token`
   - Se retorna información completa del usuario con empresa, roles y permisos

3. **Acceso a Endpoints Protegidos:**
   - La cookie se envía automáticamente en cada request
   - `get_current_user()` valida el token con Supabase
   - Se obtiene usuario + empresa + roles + permisos de PostgreSQL
   - Se retorna `CurrentUser` con toda la información

### Sistema de Autorización (RBAC)

El sistema utiliza un modelo de control de acceso basado en roles (RBAC) con permisos granulares definidos por **acción** y **recurso**.

#### Estructura de Permisos

Cada permiso tiene dos componentes:
- **Acción**: Qué puede hacer (`create`, `read`, `update`, `delete`)
- **Recurso**: Sobre qué tabla/entidad (`empresas`, `usuarios`, `roles`, `permisos`, `roles_permisos`, `usuarios_roles`)

#### Permisos Disponibles

Los permisos se definen automáticamente al insertar en la base de datos según este patrón:

```sql
-- Para cada recurso (empresas, usuarios, roles, permisos, roles_permisos, usuarios_roles)
INSERT INTO permisos (accion, recurso) VALUES
  ('create', 'recurso'),
  ('read',   'recurso'),
  ('update', 'recurso'),
  ('delete', 'recurso');
```

**Recursos disponibles:**
- `empresas`: Gestión de información de la empresa
- `usuarios`: Gestión de empleados
- `roles`: Gestión de roles
- `permisos`: Gestión de permisos globales
- `roles_permisos`: Asignación de permisos a roles
- `usuarios_roles`: Asignación de roles a usuarios

#### Niveles de Acceso:

1. **Dueños (`es_dueno=true`):**
   - Acceso completo a todas las funciones de su empresa
   - Tienen automáticamente todos los permisos sin necesidad de roles
   - Pueden gestionar empresa, usuarios, roles y permisos
   - La función `has_permission()` siempre retorna `True` para dueños

2. **Empleados:**
   - Acceso basado en permisos asignados mediante roles
   - Solo pueden realizar acciones para las que tienen permiso
   - Los permisos se obtienen de los roles asignados
   - Deben tener roles con permisos específicos para acceder a funciones

#### Mapeo de Endpoints a Permisos:

| Endpoint | Método | Permiso Requerido |
|----------|--------|-------------------|
| `/empresa` | GET | `read` en `empresas` |
| `/empresa` | PUT | `update` en `empresas` |
| `/empresa` | DELETE | `delete` en `empresas` |
| `/usuarios` | POST | `create` en `usuarios` |
| `/usuarios` | GET | `read` en `usuarios` |
| `/usuarios/{id}` | PATCH | `update` en `usuarios` |
| `/usuarios/{id}` | DELETE | `delete` en `usuarios` |
| `/usuarios/{id}/roles` | POST | `create` en `usuarios_roles` |
| `/usuarios/{id}/roles` | GET | `read` en `usuarios_roles` |
| `/usuarios/{id}/roles/{rol_id}` | DELETE | `delete` en `usuarios_roles` |
| `/roles` | POST | `create` en `roles` + `create` en `roles_permisos` (si asigna permisos) |
| `/roles` | GET | `read` en `roles` |
| `/roles/{id}` | PATCH | `update` en `roles` + `update/delete/create` en `roles_permisos` (si modifica permisos) |
| `/roles/{id}` | DELETE | `delete` en `roles` |
| `/permisos` | POST | `create` en `permisos` |
| `/permisos` | GET | `read` en `permisos` |
| `/permisos/{id}` | GET | `read` en `permisos` |
| `/permisos/{id}` | PATCH | `update` en `permisos` |
| `/permisos/{id}` | DELETE | `delete` en `permisos` |

#### Dependencias de Autorización:

```python
# Requiere usuario autenticado (cualquier usuario de la empresa)
current_user: CurrentUser = Depends(get_current_user)

# Requiere permiso específico (dueños tienen acceso automático)
# Ejemplo: requiere permiso "create" en recurso "usuarios"
current_user: CurrentUser = Depends(require_permission("create", "usuarios"))

# Requiere ser dueño (para operaciones críticas)
current_user: CurrentUser = Depends(require_owner())
```

#### Validaciones Especiales:

- **Asignar permisos a roles**: Requiere permiso `create` en `roles_permisos`
- **Modificar permisos de un rol**: Requiere `update` y `delete` en `roles_permisos`
- **Asignar roles a usuarios**: Requiere permiso `create` en `usuarios_roles`
- **Crear nuevos permisos al crear rol**: Requiere permiso `create` en `permisos`

## 📡 API Endpoints

### Autenticación (`/auth`)

#### `POST /auth/register-owner`
Registra un nuevo dueño con su empresa.

**Request:**
```json
{
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@example.com",
  "password": "password123",
  "nombre_empresa": "Mi Empresa S.A.",
  "razon_social": "Mi Empresa S.A.",
  "nit": "123456789",
  "telefono": "+1234567890",
  "email_empresa": "contacto@miempresa.com",
  "direccion": "Calle 123, Ciudad"
}
```

**Response:** 201 Created
```json
{
  "id_usuario": 1,
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@example.com",
  "es_dueno": true,
  "id_empresa": 1,
  "nombre_empresa": "Mi Empresa S.A."
}
```

#### `POST /auth/login`
Inicia sesión y establece cookie HTTP-only.

**Request:**
```json
{
  "email": "juan@example.com",
  "password": "password123"
}
```

**Response:** 200 OK (con cookie establecida)
```json
{
  "message": "Login successful",
  "user": {
    "id_usuario": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan@example.com",
    "es_dueno": true,
    "empresa": { ... },
    "roles": [ ... ],
    "permisos": [ ... ]
  }
}
```

#### `POST /auth/logout`
Cierra sesión y elimina la cookie.

**Response:** 200 OK
```json
{
  "message": "Logout successful"
}
```

#### `GET /auth/me`
Obtiene información del usuario autenticado actual.

**Response:** 200 OK
```json
{
  "id_usuario": 1,
  "nombre": "Juan",
  "apellido": "Pérez",
  "email": "juan@example.com",
  "es_dueno": true,
  "empresa": { ... },
  "roles": [ ... ],
  "permisos": [ ... ]
}
```

### Empresa (`/empresa`)

Todos los endpoints requieren autenticación.

#### `GET /empresa`
Obtiene información de la empresa del usuario actual (requiere permiso `read` en `empresas`).

**Response:** 200 OK

#### `PUT /empresa`
Actualiza información de la empresa (requiere permiso `update` en `empresas`).

**Request:**
```json
{
  "nombre": "Empresa Actualizada",
  "razon_social": "Nueva Razón Social",
  "nit": "987654321",
  "telefono": "+9876543210",
  "email_empresa": "nuevo@empresa.com",
  "direccion": "Nueva Dirección",
  "estado": true
}
```

**Restricciones:** 
- `nombre`: máximo 30 caracteres
- `razon_social`: máximo 20 caracteres
- `nit`: máximo 20 caracteres
- `telefono`: máximo 15 caracteres

#### `DELETE /empresa`
Elimina (soft delete) la empresa (requiere permiso `delete` en `empresas`).

**Response:** 204 No Content

### Usuarios (`/usuarios`)

#### `POST /usuarios`
Crea un nuevo empleado (requiere permiso `create` en `usuarios`).

**Request:**
```json
{
  "nombre": "María",
  "apellido": "González",
  "email": "maria@example.com",
  "password": "password123"
}
```

**Validaciones:**
- Email no debe existir en base de datos ni en Supabase Auth
- `nombre` y `apellido`: máximo 30 caracteres cada uno

#### `GET /usuarios`
Lista todos los empleados de la empresa (requiere permiso `read` en `usuarios`).

**Response:** 200 OK (lista de usuarios, excluye dueños)

#### `PATCH /usuarios/{usuario_id}`
Actualiza información de un empleado (requiere permiso `update` en `usuarios`).

**Request:**
```json
{
  "nombre": "María",
  "apellido": "González López",
  "email": "maria.nueva@example.com",
  "estado": true
}
```

**Validaciones:**
- Si se actualiza email, verifica que no esté en uso

#### `DELETE /usuarios/{usuario_id}`
Elimina (soft delete) un empleado (requiere permiso `delete` en `usuarios`).

#### `POST /usuarios/{usuario_id}/roles`
Asigna roles a un usuario (requiere permiso `create` en `usuarios_roles`).

**Request:**
```json
{
  "roles_ids": [1, 2, 3]
}
```

**Validaciones:**
- Todos los roles deben pertenecer a la misma empresa
- Elimina duplicados automáticamente
- Si la lista está vacía, quita todos los roles

#### `GET /usuarios/{usuario_id}/roles`
Obtiene los roles asignados a un usuario (requiere permiso `read` en `usuarios_roles`).

#### `DELETE /usuarios/{usuario_id}/roles/{rol_id}`
Quita un rol específico de un usuario (requiere permiso `delete` en `usuarios_roles`).

**Response:** 204 No Content

#### `POST /usuarios/{usuario_id}/roles`
Asigna roles a un usuario (reemplaza roles existentes).

**Request:**
```json
{
  "roles_ids": [1, 2, 3]
}
```

**Validaciones:**
- Todos los roles deben pertenecer a la misma empresa
- Elimina duplicados automáticamente
- Si la lista está vacía, quita todos los roles

#### `GET /usuarios/{usuario_id}/roles`
Obtiene los roles asignados a un usuario.

**Response:** 200 OK
```json
{
  "id_usuario": 2,
  "nombre": "María",
  "apellido": "González",
  "email": "maria@example.com",
  "es_dueno": false,
  "estado": true,
  "roles": [
    {
      "id_rol": 1,
      "nombre": "Gerente",
      "descripcion": "Rol de gerente"
    }
  ]
}
```

#### `DELETE /usuarios/{usuario_id}/roles/{rol_id}`
Quita un rol específico de un usuario.

**Response:** 204 No Content

### Roles (`/roles`)

#### `POST /roles`
Crea un nuevo rol (requiere permiso `create` en `roles`).

**Permisos adicionales requeridos:**
- Si asigna permisos existentes: requiere permiso `create` en `roles_permisos`
- Si crea nuevos permisos: requiere permiso `create` en `permisos` además de `roles_permisos`

**Request:**
```json
{
  "nombre": "Gerente",
  "descripcion": "Rol de gerente con permisos administrativos",
  "permisos_ids": [1, 2, 3],
  "permisos_nuevos": [
    {
      "accion": "approve",
      "recurso": "documento"
    },
    {
      "accion": "reject",
      "recurso": "documento"
    }
  ]
}
```

**Características:**
- `permisos_ids`: IDs de permisos existentes a asignar
- `permisos_nuevos`: Permisos nuevos a crear si no existen (se reutilizan si ya existen)

#### `GET /roles`
Lista todos los roles de la empresa (requiere permiso `read` en `roles`).

**Response:** 200 OK (lista de roles con sus permisos)

#### `PATCH /roles/{rol_id}`
Actualiza un rol (requiere permiso `update` en `roles`).

**Permisos adicionales si modifica permisos:**
- Requiere `update` y `delete` en `roles_permisos` para modificar permisos del rol
- Requiere `create` en `roles_permisos` para asignar nuevos permisos

**Request:**
```json
{
  "nombre": "Gerente Senior",
  "descripcion": "Rol actualizado",
  "permisos_ids": [1, 2, 3, 4]
}
```

#### `DELETE /roles/{rol_id}`
Elimina un rol (requiere permiso `delete` en `roles`).

**Response:** 204 No Content

### Permisos (`/permisos`)

#### `POST /permisos`
Crea un nuevo permiso global (requiere permiso `create` en `permisos`).

**Request:**
```json
{
  "accion": "create",
  "recurso": "documento"
}
```

**Validaciones:**
- La combinación `accion + recurso` debe ser única
- `accion` y `recurso`: máximo 30 caracteres cada uno

#### `GET /permisos`
Lista todos los permisos globales disponibles.

**Response:** 200 OK (lista de permisos ordenados por recurso y acción)

#### `GET /permisos/{permiso_id}`
Obtiene un permiso específico.

**Response:** 200 OK

#### `PATCH /permisos/{permiso_id}`
Actualiza un permiso (requiere permiso `update` en `permisos`).

**Request:**
```json
{
  "accion": "update",
  "recurso": "documento"
}
```

#### `DELETE /permisos/{permiso_id}`
Elimina un permiso (requiere permiso `delete` en `permisos`).

**Validaciones:**
- No se puede eliminar si está siendo usado por algún rol

**Response:** 204 No Content

## 🔄 Flujos de Trabajo

### Flujo 1: Registro y Configuración Inicial

1. Dueño se registra con `/auth/register-owner`
2. Se crea empresa y usuario dueño
3. Dueño inicia sesión con `/auth/login`
4. Dueño crea permisos con `/permisos` POST
5. Dueño crea roles con `/roles` POST (asigna permisos o crea nuevos)
6. Dueño crea empleados con `/usuarios` POST
7. Dueño asigna roles a empleados con `/usuarios/{id}/roles` POST

### Flujo 2: Empleado con Roles

1. Empleado inicia sesión con `/auth/login`
2. Sistema carga usuario + empresa + roles + permisos
3. Empleado accede a endpoints según sus permisos
4. Si no tiene permiso, recibe 403 Forbidden

### Flujo 3: Gestión de Permisos

1. Dueño crea nuevos permisos con `/permisos` POST
2. Dueño asigna permisos a roles al crear o actualizar roles
3. Los empleados con esos roles automáticamente obtienen los permisos
4. Al consultar `/auth/me`, se incluyen todos los permisos del usuario

## 💡 Ejemplos de Uso

### Ejemplo 1: Registro completo de empresa

```bash
# 1. Registrar dueño
curl -X POST http://localhost:8000/auth/register-owner \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan@example.com",
    "password": "password123",
    "nombre_empresa": "Mi Empresa S.A.",
    "razon_social": "Mi Empresa S.A.",
    "nit": "123456789"
  }'

# 2. Login (las cookies se guardan automáticamente)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@example.com",
    "password": "password123"
  }' \
  -c cookies.txt

# 3. Crear permisos
curl -X POST http://localhost:8000/permisos \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "accion": "create",
    "recurso": "usuario"
  }'

# 4. Crear rol con permisos
curl -X POST http://localhost:8000/roles \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "nombre": "Gerente",
    "descripcion": "Rol de gerente",
    "permisos_ids": [1],
    "permisos_nuevos": [
      {"accion": "read", "recurso": "usuario"},
      {"accion": "update", "recurso": "usuario"}
    ]
  }'

# 5. Crear empleado
curl -X POST http://localhost:8000/usuarios \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "nombre": "María",
    "apellido": "González",
    "email": "maria@example.com",
    "password": "password123"
  }'

# 6. Asignar rol a empleado
curl -X POST http://localhost:8000/usuarios/2/roles \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "roles_ids": [1]
  }'
```

### Ejemplo 2: Consultar información del usuario actual

```bash
curl -X GET http://localhost:8000/auth/me \
  -b cookies.txt
```

## 📬 Colección Postman

Incluida en `postman_collection.json` con todos los endpoints documentados y ejemplos de requests.

**Importar en Postman:**
1. Abre Postman
2. File > Import
3. Selecciona `postman_collection.json`
4. Todas las requests estarán disponibles para probar

**Nota:** Las cookies se manejan automáticamente en Postman al usar la colección.

## 🚀 Ejecución

### Desarrollo

```bash
uvicorn app.main:app --reload
```

El servicio estará disponible en `http://localhost:8000`

### Producción

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Documentación Interactiva

Una vez ejecutando, puedes acceder a:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔍 Validaciones y Restricciones

### Validaciones de Longitud

Todos los campos tienen validaciones según las restricciones de la base de datos:

- `nombre` (usuario/empresa): máximo 30 caracteres
- `apellido`: máximo 30 caracteres
- `razon_social`: máximo 20 caracteres
- `nit`: máximo 20 caracteres
- `telefono`: máximo 15 caracteres
- `email`: máximo 50 caracteres
- `direccion`: máximo 300 caracteres
- `accion` (permiso): máximo 30 caracteres
- `recurso` (permiso): máximo 30 caracteres
- `nombre` (rol): máximo 30 caracteres
- `descripcion` (rol): máximo 300 caracteres

### Validaciones de Email

- El email se valida en la base de datos antes de crear
- El email se valida en Supabase Auth antes de crear
- Se valida formato con Pydantic EmailStr

### Validaciones de Negocio

- Un usuario no puede ser dueño de múltiples empresas
- Los roles son específicos por empresa
- Los permisos son globales (compartidos entre empresas)
- No se puede eliminar un permiso si está en uso
- No se puede eliminar un dueño
- No se puede eliminar una empresa si tiene usuarios activos

## 🐛 Troubleshooting

### Error: "failed to resolve host"
- Verifica que tu proyecto de Supabase esté **ACTIVO** (no pausado)
- Verifica que el `DATABASE_URL` tenga el formato correcto
- Usa el formato de Connection Pooler si tienes problemas con conexión directa

### Error: "Email already registered"
- El email ya existe en la base de datos o en Supabase Auth
- Verifica usando `/auth/me` o consultando directamente

### Error: "Permission denied"
- El usuario no tiene el permiso requerido
- Verifica los roles asignados al usuario
- Los dueños tienen acceso completo automáticamente

### Error: "Roles not found or do not belong to your company"
- Los IDs de roles no existen o pertenecen a otra empresa
- Lista los roles disponibles con `GET /roles`
- Asegúrate de usar IDs de roles de tu empresa

## 📝 Notas Importantes

1. **Cookies HTTP-only:** Por seguridad, las cookies se establecen como HTTP-only. En producción, configura `secure=True` y `samesite="strict"`.

2. **Base de datos:** Las tablas y secuencias deben existir previamente. El servicio no crea la estructura de la base de datos.

3. **Supabase:** Asegúrate de usar el `SERVICE_ROLE_KEY` (no el `ANON_KEY`) para operaciones administrativas.

4. **Python 3.13:** El servicio está optimizado para Python 3.13 usando `psycopg` v3 para mejor compatibilidad.

5. **Dueños vs Empleados:** Los dueños (`es_dueno=true`) tienen acceso completo sin necesidad de permisos específicos.

