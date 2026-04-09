from fastapi import FastAPI
from api.routes import recetas, tasks
from api.core.database import connect_db, close_db

app = FastAPI(
    title="Recetas API",
    description="API REST para gestión de recetas con procesamiento asíncrono",
    version="1.0.0",
)

app.add_event_handler("startup", connect_db)
app.add_event_handler("shutdown", close_db)

app.include_router(recetas.router, prefix="/recetas", tags=["Recetas"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Recetas API corriendo"}
