from fastapi import APIRouter, HTTPException
from api.models.schemas import TaskResponse
from api.services import task_service

router = APIRouter()


@router.get("/{task_id}", response_model=TaskResponse, summary="Consultar tarea por ID")
async def get_task(task_id: str):
    """
    Consulta el estado de una tarea asíncrona por su `task_id`.
    El status puede ser: **running**, **done** o **error**.
    """
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return {"id": task["_id"], "task_id": task["task_id"], "status": task["status"]}
