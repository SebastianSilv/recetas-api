"""
Pruebas unitarias para servicios y modelos de la API de Recetas.
Ejecutar con: pytest tests/ -v
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from api.models.schemas import RecetaCreate, RecetaUpdate, Ingrediente
from api.services import task_service, receta_service
from worker.worker import process_message


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def receta_valida():
    return RecetaCreate(
        nombre="Ensalada César",
        calorias=350,
        pasos=["Lavar lechuga", "Mezclar ingredientes"],
        ingredientes=[
            Ingrediente(nombre="Lechuga", cantidad="200g"),
            Ingrediente(nombre="Pollo", cantidad="150g"),
        ],
    )


@pytest.fixture
def mock_db():
    """Simula la colección de MongoDB."""
    db = MagicMock()
    db["recetas"].insert_one = MagicMock()
    db["recetas"].delete_one = MagicMock()
    db["recetas"].find_one = AsyncMock(return_value=None)
    db["tasks"].insert_one = MagicMock()
    db["tasks"].find_one = AsyncMock(return_value=None)
    db["tasks"].update_one = MagicMock()
    return db


# ── Tests de modelos ──────────────────────────────────────────────────────────

class TestModelos:
    def test_receta_create_valida(self, receta_valida):
        assert receta_valida.nombre == "Ensalada César"
        assert receta_valida.calorias == 350
        assert len(receta_valida.pasos) == 2
        assert len(receta_valida.ingredientes) == 2

    def test_receta_calorias_invalidas(self):
        with pytest.raises(Exception):
            RecetaCreate(
                nombre="Test",
                calorias=-100,
                pasos=["paso"],
                ingredientes=[Ingrediente(nombre="Algo", cantidad="1g")],
            )

    def test_receta_update_parcial(self):
        update = RecetaUpdate(nombre="Nuevo nombre")
        assert update.nombre == "Nuevo nombre"
        assert update.calorias is None
        assert update.pasos is None

    def test_ingrediente_schema(self):
        ing = Ingrediente(nombre="Tomate", cantidad="3 unidades")
        assert ing.nombre == "Tomate"
        assert ing.cantidad == "3 unidades"


# ── Tests del worker ──────────────────────────────────────────────────────────

class TestWorker:
    def test_process_insert(self, mock_db):
        message = json.dumps({
            "action": "insert",
            "task_id": "task-123",
            "data": {
                "nombre": "Sopa",
                "calorias": 200,
                "pasos": ["Hervir agua"],
                "ingredientes": [{"nombre": "Agua", "cantidad": "500ml"}],
            },
        }).encode()
        process_message(message, mock_db)
        mock_db["recetas"].insert_one.assert_called_once()
        mock_db["tasks"].update_one.assert_called_once_with(
            {"task_id": "task-123"}, {"$set": {"status": "done"}}
        )

    def test_process_unknown_action(self, mock_db):
        message = json.dumps({
            "action": "desconocida",
            "task_id": "task-456",
        }).encode()
        process_message(message, mock_db)
        mock_db["tasks"].update_one.assert_called_once_with(
            {"task_id": "task-456"}, {"$set": {"status": "error"}}
        )

    def test_process_delete(self, mock_db):
        from bson import ObjectId
        fake_id = str(ObjectId())
        message = json.dumps({
            "action": "delete",
            "task_id": "task-789",
            "receta_id": fake_id,
        }).encode()
        process_message(message, mock_db)
        mock_db["recetas"].delete_one.assert_called_once()
        mock_db["tasks"].update_one.assert_called_once_with(
            {"task_id": "task-789"}, {"$set": {"status": "done"}}
        )


# ── Tests de servicios (con mocks de BD) ──────────────────────────────────────

class TestTaskService:
    @pytest.mark.asyncio
    async def test_create_task(self):
        mock_result = MagicMock()
        mock_result.inserted_id = "abc123"
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock(return_value=mock_result)

        with patch("api.services.task_service.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_get_db.return_value = mock_db
            task = await task_service.create_task()

        assert "task_id" in task
        assert task["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)

        with patch("api.services.task_service.get_database") as mock_get_db:
            mock_db = MagicMock()
            mock_db.__getitem__ = MagicMock(return_value=mock_collection)
            mock_get_db.return_value = mock_db
            result = await task_service.get_task_by_id("no-existe")

        assert result is None


class TestRecetaService:
    def test_publish_insert_receta(self, receta_valida):
        with patch("api.services.receta_service._publish_message") as mock_pub:
            receta_service.publish_insert_receta(receta_valida, "task-001")
            mock_pub.assert_called_once()
            args = mock_pub.call_args[0][0]
            assert args["action"] == "insert"
            assert args["task_id"] == "task-001"
            assert args["data"]["nombre"] == "Ensalada César"

    def test_publish_delete_receta(self):
        with patch("api.services.receta_service._publish_message") as mock_pub:
            receta_service.publish_delete_receta("receta-999", "task-002")
            mock_pub.assert_called_once()
            args = mock_pub.call_args[0][0]
            assert args["action"] == "delete"
            assert args["task_id"] == "task-002"
            assert args["receta_id"] == "receta-999"
