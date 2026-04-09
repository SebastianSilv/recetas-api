from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


# ── Recetas ────────────────────────────────────────────────────────────────────

class Ingrediente(BaseModel):
    nombre: str
    cantidad: str  # e.g. "200g", "2 tazas"


class RecetaCreate(BaseModel):
    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Ensalada César",
                "calorias": 350,
                "pasos": ["Lavar la lechuga", "Mezclar con aderezo"],
                "ingredientes": [
                    {"nombre": "Lechuga", "cantidad": "200g"},
                    {"nombre": "Pollo", "cantidad": "150g"},
                ],
            }
        }
    }

    nombre: str
    calorias: int = Field(..., gt=0)
    pasos: List[str]
    ingredientes: List[Ingrediente]


class RecetaUpdate(BaseModel):
    nombre: Optional[str] = None
    calorias: Optional[int] = Field(None, gt=0)
    pasos: Optional[List[str]] = None
    ingredientes: Optional[List[Ingrediente]] = None


class RecetaResponse(BaseModel):
    id: str
    nombre: str
    calorias: int
    pasos: List[str]
    ingredientes: List[Ingrediente]


# ── Tasks ──────────────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    running = "running"
    done = "done"
    error = "error"


class TaskResponse(BaseModel):
    id: str
    task_id: str
    status: TaskStatus
