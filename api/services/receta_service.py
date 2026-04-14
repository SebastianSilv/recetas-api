import json
import pika
from bson import ObjectId
from api.core.database import get_database, get_rabbitmq_url
from api.models.schemas import RecetaCreate, RecetaUpdate

QUEUE_NAME = "recetas_queue"


def _publish_message(message: dict):
    """Publica un mensaje en la cola de RabbitMQ."""
    url = get_rabbitmq_url()
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


async def get_all_recetas() -> list:
    db = get_database()
    recetas = []
    async for doc in db["recetas"].find():
        doc["id"] = str(doc.pop("_id"))
        recetas.append(doc)
    return recetas


async def get_receta_by_id(receta_id: str) -> dict | None:
    db = get_database()
    try:
        doc = await db["recetas"].find_one({"_id": ObjectId(receta_id)})
    except Exception:
        return None
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


async def update_receta(receta_id: str, data: RecetaUpdate) -> dict | None:
    """Actualización síncrona de una receta."""
    db = get_database()
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        return await get_receta_by_id(receta_id)
    try:
        await db["recetas"].update_one(
            {"_id": ObjectId(receta_id)},
            {"$set": update_data}
        )
    except Exception:
        return None
    return await get_receta_by_id(receta_id)


def publish_insert_receta(receta: RecetaCreate, task_id: str):
    """Envía mensaje para insertar una receta vía worker."""
    _publish_message({
        "action": "insert",
        "task_id": task_id,
        "data": receta.model_dump(),
    })


def publish_delete_receta(receta_id: str, task_id: str):
    """Envía mensaje para eliminar una receta vía worker."""
    _publish_message({
        "action": "delete",
        "task_id": task_id,
        "receta_id": receta_id,
    })
