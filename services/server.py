import os
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from auth.oauth import get_auth_url, exchange_code_for_token, get_credentials, refresh_access_token
from services.queue_manager import get_task_status
from services.celery_tasks import download_and_upload_task, upload_task
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cargar valores por defecto desde .env
DEFAULT_SOURCE_FOLDER_ID = os.getenv("SOURCE_FOLDER_ID")
DEFAULT_DESTINATION_FOLDER_ID = os.getenv("DESTINATION_FOLDER_ID")


@app.get("/", response_class=HTMLResponse)
def read_root():
    """🔹 Sirve el archivo index.html en la ruta principal."""
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/auth/url")
def oauth_url():
    """🔹 Retorna la URL de autenticación de Google OAuth2."""
    return {"auth_url": get_auth_url()}


@app.get("/auth/callback")
def oauth_callback(code: str = Query(..., description="Código de autorización de Google")):
    """
    🔹 Maneja el callback de OAuth2 e intercambia el código por un token.
    """
    token = exchange_code_for_token(code)
    return {"message": "✅ Token obtenido con éxito", "access_token": token}


@app.get("/auth/token")
def get_token():
    """
    🔹 Endpoint para obtener el token de autenticación de Google Drive.
    - Si el token es válido, se devuelve.
    - Si está expirado, se refresca automáticamente.
    """
    creds = get_credentials()
    return {
        "message": "🔑 Token actual obtenido con éxito.",
        "access_token": creds.token,
        "expiry": creds.expiry.isoformat() if creds.expiry else None
    }


@app.get("/auth/refresh")
def refresh_token():
    """
    🔹 Refresca el token de autenticación si es posible y devuelve el token actualizado.
    """
    try:
        new_token_data = refresh_access_token()
        return {
            "message": "✅ Token actualizado con éxito",
            "token_data": new_token_data,
        }
    except Exception as e:
        return {"error": f"❌ No se pudo actualizar el token. {str(e)}"}


@app.get("/drive/download-upload")
def start_download_and_upload(
    folder_id: str = Query(None, description="ID de la carpeta fuente"),
    destination_folder_id: str = Query(
        None, description="ID de la carpeta destino"),
):
    """
    Inicia la descarga, compresión y subida en segundo plano.
    Si no se proporcionan los IDs en la URL, se usarán los valores del .env.
    """

    # Usar valores predeterminados si los parámetros no se envían
    folder_id = folder_id or DEFAULT_SOURCE_FOLDER_ID
    destination_folder_id = destination_folder_id or DEFAULT_DESTINATION_FOLDER_ID

    if not folder_id or not destination_folder_id:
        return {
            "error": "❌ No se proporcionó un folder_id o destination_folder_id y no existen valores predeterminados."
        }

    task = download_and_upload_task.apply_async(
        args=[folder_id, destination_folder_id])
    return {"message": "📌 Tarea en cola", "task_id": task.id}


@app.get("/drive/upload")
def start_upload_task(destination_folder_id: str = Query(None, description="ID de la carpeta destino")):
    """Inicia la compresión y subida de archivos en segundo plano."""
    destination_folder_id = destination_folder_id or DEFAULT_DESTINATION_FOLDER_ID

    if not destination_folder_id:
        return {
            "error": "❌ No se proporcionó un destination_folder_id y no existen valores predeterminados."
        }

    task = upload_task.apply_async(args=[destination_folder_id])
    return {"message": "📌 Tarea en cola", "task_id": task.id}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    """Consulta el estado de una tarea en Celery."""
    return get_task_status(task_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
