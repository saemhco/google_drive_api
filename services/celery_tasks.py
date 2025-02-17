import os
import zipfile
from celery import Celery
from services.drive_service import download_folder, compress_folder, upload_to_drive, cleanup, create_drive_service, upload_file_in_chunks

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)


@celery_app.task(bind=True)
def download_and_upload_task(self, folder_id, destination_folder_id):
    """Tarea asíncrona que descarga, comprime y sube archivos de Google Drive."""
    try:
        print("🚀 Iniciando proceso de descarga y subida en Celery...")
        download_folder(folder_id)
        zip_file = compress_folder()
        uploaded_file_id = upload_to_drive(zip_file, destination_folder_id)
        # cleanup()

        return {"success": True, "uploaded_file_id": uploaded_file_id}
    except Exception as e:
        print(f"❌ Error en Celery: {e}")
        return {"success": False, "error": str(e)}


@celery_app.task(bind=True)
def upload_task(self, destination_folder_id):
    """Tarea asíncrona que comprime y sube archivos de la carpeta downloads a Google Drive."""
    try:
        print("🚀 Iniciando proceso de compresión y subida en Celery...")

        # Comprimir los archivos en la carpeta downloads
        zip_file_path = "downloads.zip"
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk("downloads"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, "downloads")
                    zipf.write(file_path, arcname)
        print(f"📦 Archivos comprimidos en: {zip_file_path}")

        # Subir el archivo comprimido a Google Drive en fragmentos
        service = create_drive_service()
        uploaded_file_id = upload_file_in_chunks(
            service, zip_file_path, destination_folder_id)

        # Eliminar el archivo comprimido
        os.remove(zip_file_path)
        print(f"🗑️ Archivo comprimido eliminado: {zip_file_path}")

        return {"success": True, "file_id": uploaded_file_id}
    except Exception as e:
        print(f"❌ Error en Celery: {e}")
        return {"success": False, "error": str(e)}
