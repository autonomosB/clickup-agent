from crewai import Agent, Task, Crew
import os
import time
import logging
import requests

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClickUpAgent:
    def __init__(self):
        self.api_key = os.getenv('CLICKUP_API_TOKEN')
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        self.base_url = "https://api.clickup.com/api/v2"
        
    def get_task(self, task_id):
        """Obtiene una tarea por su ID"""
        url = f"{self.base_url}/task/{task_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None
        
    def get_task_comments(self, task_id):
        """Obtiene los comentarios de una tarea"""
        url = f"{self.base_url}/task/{task_id}/comment"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get('comments', [])
        return []
        
    def create_comment(self, task_id, comment_text):
        """Crea un comentario en una tarea"""
        url = f"{self.base_url}/task/{task_id}/comment"
        data = {"comment_text": comment_text}
        response = requests.post(url, headers=self.headers, json=data)
        return response.status_code == 200
        
    def monitor_comments(self, task_id: str):
        """Monitorea los comentarios de una tarea"""
        logger.info(f"Iniciando monitoreo de tarea: {task_id}")
        processed_comments = set()  # Guardamos los IDs de comentarios ya procesados
        
        while True:
            try:
                task = self.get_task(task_id)
                if task:
                    logger.info(f"Tarea encontrada: {task['name']}")
                    
                    comments = self.get_task_comments(task_id)
                    logger.info(f"Comentarios encontrados: {len(comments)}")
                    
                    for comment in comments:
                        comment_id = comment.get('id')
                        if comment_id not in processed_comments and '@AI' in comment.get('comment_text', ''):
                            pregunta = comment['comment_text'].replace('@AI', '').strip()
                            logger.info(f"Nueva pregunta encontrada: {pregunta}")
                            respuesta = self.responder_pregunta(task, pregunta)
                            self.create_comment(task_id, respuesta)
                            processed_comments.add(comment_id)
                            logger.info("Respuesta enviada")
                
                logger.info("Esperando 30 segundos...")
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error general: {str(e)}")
                time.sleep(30)
    
    def responder_pregunta(self, task, pregunta: str) -> str:
        """Responde preguntas sobre tareas en ClickUp"""
        # Crear el agente
        agent = Agent(
            role='Asistente de ClickUp',
            goal='Proporcionar respuestas precisas sobre tareas en ClickUp',
            backstory='Soy un asistente especializado en analizar y responder preguntas sobre tareas en ClickUp',
            verbose=True,
            allow_delegation=False,
            tools=[]
        )
        
        # Crear la tarea asignada al agente
        task_for_agent = Task(
            description=f"""
            Analiza la siguiente pregunta sobre la tarea de ClickUp y proporciona una respuesta útil:
            Pregunta: {pregunta}
            Contexto de la tarea: {task['name']} - {task.get('description', 'Sin descripción')}
            """,
            expected_output="Una respuesta detallada a la pregunta sobre la tarea",
            agent=agent
        )
        
        # Crear el crew con el agente y la tarea
        crew = Crew(
            agents=[agent],
            tasks=[task_for_agent]
        )
        
        try:
            # Ejecutar el crew y obtener el resultado
            result = crew.kickoff()
            # Convertir el resultado a string
            if hasattr(result, 'raw_output'):
                return str(result.raw_output)
            return str(result)
        except Exception as e:
            logger.error(f"Error al procesar la respuesta: {str(e)}")
            return "Lo siento, hubo un error al procesar la pregunta. Por favor, intenta de nuevo."