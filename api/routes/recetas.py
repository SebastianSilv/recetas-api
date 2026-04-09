from fastapi import APIRouter, HTTPException, status
from api.models.schemas import RecetaCreate, RecetaUpdate, RecetaResponse
from api.services import receta_service, task_service

router = APIRouter()


# ── GET /recetas  (Síncrono) ───────────────────────────────────────────────────
@router.get("/", response_model=list[RecetaResponse], summary="Consultar todas las recetas")
async def get_recetas():
    return await receta_service.get_all_recetas()


# ── GET /recetas/{id}  (Síncrono) ─────────────────────────────────────────────
@router.get("/{receta_id}", response_model=RecetaResponse, summary="Consultar receta por ID")
async def get_receta(receta_id: str):
    receta = await receta_service.get_receta_by_id(receta_id)
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return receta


# ── POST /recetas  (Asíncrono - retorna TaskId) ────────────────────────────────
@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Insertar receta (asíncrono)",
)
async def create_receta(receta: RecetaCreate):
    """
    Crea una tarea con status **running**, publica el mensaje en RabbitMQ
    y retorna el `task_id` para que el cliente consulte el resultado luego.
    """
    task = await task_service.create_task()
    receta_service.publish_insert_receta(receta, task["task_id"])
    return {"task_id": task["task_id"], "status": "running"}


# ── PUT /recetas/{id}  (Síncrono) ─────────────────────────────────────────────
@router.put("/{receta_id}", response_model=RecetaResponse, summary="Actualizar receta")
async def update_receta(receta_id: str, data: RecetaUpdate):
    updated = await receta_service.update_receta(receta_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Receta no encontrada")
    return updated


# ── DELETE /recetas/{id}  (Asíncrono - retorna TaskId) ────────────────────────
@router.delete(
    "/{receta_id}",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Eliminar receta (asíncrono)",
)
async def delete_receta(receta_id: str):
    """
    Crea una tarea con status **running**, publica el mensaje de eliminación
    en RabbitMQ y retorna el `task_id`.
    """
    task = await task_service.create_task()
    receta_service.publish_delete_receta(receta_id, task["task_id"])
    return {"task_id": task["task_id"], "status": "running"}
