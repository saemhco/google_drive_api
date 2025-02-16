import os
from celery import Celery
from services.drive_service import download_folder, compress_folder, upload_to_drive, cleanup

# Configuración de Celery
celery_app = Celery(
    "tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)


@celery_app.task(bind=True, name="tasks.download_and_upload_task")
def download_and_upload_task(self, folder_id=None, destination_folder_id=None):
    """Tarea asíncrona que descarga, comprime y sube archivos de Google Drive."""
    try:
        print("🚀 Iniciando proceso de descarga y subida en Celery...")

        # Si los valores no se pasan, usaremos los de .env
        folder_id = folder_id or os.getenv("SOURCE_FOLDER_ID")
        destination_folder_id = destination_folder_id or os.getenv(
            "DESTINATION_FOLDER_ID")

        if not folder_id or not destination_folder_id:
            raise ValueError("No se han definido los IDs de las carpetas.")

        # Ejecutar el flujo de trabajo
        download_folder(folder_id)
        zip_file = compress_folder()
        uploaded_file_id = upload_to_drive(zip_file, destination_folder_id)
        cleanup()

        print("✅ Proceso finalizado con éxito")
        return {"success": True, "uploaded_file_id": uploaded_file_id}

    except Exception as e:
        print(f"❌ Error en Celery: {e}")
        return {"success": False, "error": str(e)}
