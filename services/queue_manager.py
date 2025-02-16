from services.celery_tasks import celery_app


def get_task_status(task_id):
    """Obtiene el estado de una tarea en Celery."""
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }
