import uuid
from api.core.database import get_database


async def create_task() -> dict:
    """Crea una nueva tarea con status 'running' y retorna su task_id."""
    db = get_database()
    task_id = str(uuid.uuid4())
    doc = {"task_id": task_id, "status": "running"}
    result = await db["tasks"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


async def get_task_by_id(task_id: str) -> dict | None:
    """Retorna una tarea por su task_id."""
    db = get_database()
    doc = await db["tasks"].find_one({"task_id": task_id})
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def update_task_status(task_id: str, status: str):
    """Actualiza el status de una tarea."""
    db = get_database()
    await db["tasks"].update_one(
        {"task_id": task_id},
        {"$set": {"status": status}}
    )
