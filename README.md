# 🥗 Recetas API

API REST para gestión de recetas con procesamiento asíncrono usando FastAPI, RabbitMQ y MongoDB.

## Arquitectura

```
Actor → API REST → RabbitMQ → Worker → MongoDB
                ↘              ↗
                  Tasks (running/done/error)
```

- **API REST** (FastAPI): expone los endpoints. Las operaciones de escritura pesadas (insertar, eliminar) son asíncronas y retornan un `task_id`.
- **RabbitMQ**: cola de mensajes entre la API y el Worker.
- **Worker**: consume mensajes y ejecuta las operaciones en MongoDB.
- **MongoDB**: dos colecciones — `recetas` y `tasks`.

## Endpoints

| Método | Ruta | Tipo | Descripción |
|--------|------|------|-------------|
| GET | `/recetas` | Síncrono | Listar todas las recetas |
| GET | `/recetas/{id}` | Síncrono | Obtener receta por ID |
| POST | `/recetas` | **Asíncrono** | Crear receta → retorna `task_id` |
| PUT | `/recetas/{id}` | Síncrono | Actualizar receta |
| DELETE | `/recetas/{id}` | **Asíncrono** | Eliminar receta → retorna `task_id` |
| GET | `/tasks/{task_id}` | Síncrono | Consultar estado de tarea |

La documentación interactiva (Swagger) está disponible en `/docs`.

## Estructura del proyecto

```
recetas-api/
├── api/
│   ├── core/
│   │   └── database.py        # Conexión MongoDB + Parameter Store
│   ├── models/
│   │   └── schemas.py         # Modelos Pydantic
│   ├── routes/
│   │   ├── recetas.py         # Endpoints de recetas
│   │   └── tasks.py           # Endpoint de tareas
│   ├── services/
│   │   ├── receta_service.py  # Lógica de negocio + RabbitMQ
│   │   └── task_service.py    # CRUD de tareas
│   └── main.py                # Aplicación FastAPI
├── worker/
│   └── worker.py              # Worker RabbitMQ
├── tests/
│   └── test_recetas.py        # Pruebas unitarias
├── terraform/
│   ├── main.tf                # Infraestructura principal
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── ec2/               # Módulo EC2 + IAM
│   │   ├── sg/                # Security Groups
│   │   └── alb/               # Application Load Balancer
│   └── scripts/               # Scripts de instalación por servicio
├── docker-compose.yml         # Entorno local
├── Dockerfile.api
├── Dockerfile.worker
├── requirements.txt
└── .flake8
```

## Correr localmente

### 1. Requisitos
- Docker y Docker Compose instalados

### 2. Levantar todos los servicios
```bash
docker-compose up --build
```

### 3. Acceder a la API
- **Swagger UI**: http://localhost:8000/docs
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

## Pruebas unitarias

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar pruebas
pytest tests/ -v
```

## Chequeo de código estático

```bash
flake8 api/ worker/ tests/
```

## Despliegue en AWS con Terraform

### Requisitos previos
1. Tener [OpenTofu](https://opentofu.org/docs/intro/install/) o Terraform instalado
2. Configurar credenciales de AWS:
   ```bash
   aws configure
   ```
3. Crear un **Key Pair** en AWS EC2 y descargar el archivo `.pem`
4. Subir el código a GitHub y reemplazar `TU_USUARIO` en los scripts de `terraform/scripts/`

### Pasos para desplegar

```bash
cd terraform

# 1. Inicializar Terraform
tofu init        # o: terraform init

# 2. Ver qué va a crear
tofu plan -var="key_name=mi-key-pair"

# 3. Desplegar
tofu apply -var="key_name=mi-key-pair"
```

Al finalizar, Terraform imprime la URL del Load Balancer y la URL de Swagger:
```
swagger_url = "http://recetas-alb-XXXXXX.us-east-1.elb.amazonaws.com/docs"
```

### Para destruir la infraestructura
```bash
tofu destroy -var="key_name=mi-key-pair"
```

## Colecciones MongoDB

**recetas**
```json
{
  "_id": "ObjectId",
  "nombre": "string",
  "calorias": "number",
  "pasos": ["string"],
  "ingredientes": [{ "nombre": "string", "cantidad": "string" }]
}
```

**tasks**
```json
{
  "_id": "ObjectId",
  "task_id": "uuid string",
  "status": "running | done | error"
}
```

## Variables de entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `MONGO_URI` | URI de MongoDB (local) | `mongodb://localhost:27017` |
| `MONGO_URI_PARAM` | Nombre del parámetro en SSM | `/recetas/mongo_uri` |
| `RABBITMQ_URL` | URL de RabbitMQ (local) | `amqp://guest:guest@localhost:5672/` |
| `RABBITMQ_URL_PARAM` | Nombre del parámetro en SSM | `/recetas/rabbitmq_url` |
| `MONGO_DB_NAME` | Nombre de la base de datos | `recetas_db` |
| `AWS_REGION` | Región de AWS | `us-east-1` |
