from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from .agent import ClickUpAgent

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ClickUpAgent()

@app.get("/health")
async def health_check():
    """Endpoint para verificar que el servicio está funcionando"""
    return {"status": "healthy"}

@app.post("/monitor/{task_id}")
async def start_monitoring(task_id: str, background_tasks: BackgroundTasks):
    """Inicia el monitoreo de una tarea específica"""
    try:
        # Ejecutar el monitoreo en segundo plano
        background_tasks.add_task(agent.monitor_comments, task_id)
        return {"status": "success", "message": f"Iniciando monitoreo de tarea {task_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 