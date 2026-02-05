# # # book_catalog_app

# Descripción General

Aplicación full-stack para gestionar un catálogo personal de libros con integración a Google Books API.
Permite buscar libros, completar información faltante manualmente, guardarlos con estado inicial pending, marcarlos como read,listarlos y eliminarlos.

# Funcionalidades:

Crear libro manualmente.
Buscar libros usando Google Books API.
Guardar resultados con estado inicial pending.
Completar campos faltantes manualmente antes de guardar.
Marcar libro como read.
Listar libros del usuario.
Eliminar libros.


# Características Técnicas

Arquitectura: Se aplica una separación de responsabilidades para que el proyecto mantenible, escalable, testeable y fácil de trabajar.

Gestión de Usuarios y Seguridad: Implementación de autenticación mediante JWT (OAuth2 Password Flow). Almacenamiento seguro de credenciales utilizando hashing con Bcrypt. Endpoint dedicado para validación de sesión y control de acceso basado en roles a nivel de recurso.

Módulo de Libros: Integración con Google Books API utilizando patrones de debounce para optimización de llamadas de red y prevención de rate-limiting. Funcionalidad de fallback para creación manual de registros cuando no existen resultados externos. Operaciones CRUD completas con validación estricta de datos. Persistencia de estado de lectura y prevención de duplicidad de registros.

Frontend: Arquitectura Single Page Application. Diseño modular de componentes desacoplados para búsqueda, dashboard y modales. Gestión de estado global y renderizado dinámico del DOM sin dependencias de frameworks externos.

# Stack Tecnológico

Backend: Framework: FastAPI (Python 3.11+) ORM: SQLAlchemy 
Validación de datos: Pydantic v2 
Base de Datos: PostgreSQL 
Testing: Pytest
Frontend: HTML5, CSS3 (Custom Properties), JavaScript (ES6 Modules)
Infraestructura: Docker y Docker Compose para orquestación de contenedores.

# Estructura del Proyecto

backend/
├── app/
│   ├── api/            # Routers
│   ├── controllers/   # Lógica de endpoints
│   ├── services/      # Lógica de negocio
│   ├── models/        # SQLAlchemy Models
│   ├── schemas/       # Pydantic Schemas
│   ├── core/          # Config, auth, security
│   ├── utils/         # Google API
│   └── tests/         
frontend/
├── index.html
├── login.html
├── register.html
├── app.js
├── store.js           # Global Store
├── api.js             # Cliente HTTP
└── styles.css


# Instalación y Ejecución con Docker
1. Requisitos Previos
Docker Desktop instalado y en ejecución.

2. Configuración de Variables de Entorno
Crea un archivo .env en la raíz del proyecto (donde se encuentra el archivo docker-compose.yml):

POSTGRES_USER=sofiadmin
POSTGRES_PASSWORD=infinite123
POSTGRES_DB=booktracker
POSTGRES_SERVER=db
POSTGRES_PORT=5432
SECRET_KEY=9f36f3c559779354051662456456456456456456456456456

3. Levantar la Aplicación
Desde la terminal en la raíz del proyecto, ejecuta:
docker-compose up --build

#  Backend: Accesible en http://localhost:8000.

Documentación (Swagger): http://localhost:8000/docs.

#  Frontend: http://localhost:5500

#  Ejecución de Tests

docker-compose exec api pytest
docker-compose exec api pytest app/tests/test_user.py -v
docker-compose exec api pytest --cov=app --cov-report=term-missing

#  Changes
docker-compose down -v
docker-compose up --build
docker-compose restart api
docker-compose logs api

