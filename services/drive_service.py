import os
import shutil
import zipfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from dotenv import load_dotenv
from auth.oauth import get_credentials
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

# Cargar variables de entorno
load_dotenv()
SOURCE_FOLDER_ID = os.getenv("SOURCE_FOLDER_ID")
DESTINATION_FOLDER_ID = os.getenv("DESTINATION_FOLDER_ID")

# Ruta temporal para almacenar archivos descargados
TEMP_DOWNLOAD_PATH = "downloads"


def create_drive_service():
    """Crea el servicio de Google Drive."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def list_files_in_folder(service, folder_id):
    """Lista los archivos en una carpeta de Google Drive."""
    files = {}
    page_token = None
    while True:
        response = service.files().list(q=f"'{folder_id}' in parents",
                                        spaces='drive',
                                        fields='nextPageToken, files(id, name, mimeType)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            files[file['name']] = {'id': file['id'],
                                   'mimeType': file['mimeType']}
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files


def download_file(service, file_id, file_name, destination):
    """Descarga un archivo de Google Drive."""
    request = service.files().get_media(fileId=file_id)
    file_path = os.path.join(destination, file_name)
    try:
        with open(file_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(
                    f"Descargando {file_name}: {int(status.progress() * 100)}% completado.")
        print(f"Archivo descargado: {file_path}")
    except HttpError as error:
        print(f"Error al descargar el archivo {file_name}: {error}")


def download_folder_contents(service, folder_id, local_path):
    """Descarga el contenido de una carpeta de Google Drive de manera recursiva."""
    os.makedirs(local_path, exist_ok=True)
    files = list_files_in_folder(service, folder_id)

    for file_name, file_info in files.items():
        if file_info['mimeType'] == 'application/vnd.google-apps.folder':
            # Llamada recursiva para subcarpetas
            subfolder_path = os.path.join(local_path, file_name)
            download_folder_contents(service, file_info['id'], subfolder_path)
        else:
            download_file(service, file_info['id'], file_name, local_path)


def download_folder(folder_id=None):
    """Descarga una carpeta de Google Drive."""
    folder_id = folder_id or SOURCE_FOLDER_ID
    if not folder_id:
        raise ValueError("No se especificó un ID de carpeta para descargar.")

    service = create_drive_service()
    download_folder_contents(service, folder_id, TEMP_DOWNLOAD_PATH)

    return TEMP_DOWNLOAD_PATH


def compress_folder():
    """Comprime la carpeta descargada en un archivo ZIP."""
    zip_filename = "data.zip"
    shutil.make_archive(zip_filename.replace(
        ".zip", ""), 'zip', TEMP_DOWNLOAD_PATH)
    print(f"✅ Carpeta comprimida: {zip_filename}")
    return zip_filename


def upload_to_drive(zip_file_path, destination_folder_id=None):
    """Sube el archivo ZIP a Google Drive en la carpeta destino."""
    destination_folder_id = destination_folder_id or DESTINATION_FOLDER_ID
    if not destination_folder_id:
        raise ValueError(
            "No se ha configurado un DESTINATION_FOLDER_ID en .env.")

    service = create_drive_service()
    file_metadata = {
        "name": os.path.basename(zip_file_path),
        "parents": [destination_folder_id]
    }
    media = MediaFileUpload(zip_file_path, mimetype="application/zip")

    uploaded_file = service.files().create(
        body=file_metadata, media_body=media, fields="id"
    ).execute()
    print(f"✅ Archivo ZIP subido a Drive con ID: {uploaded_file.get('id')}")

    return uploaded_file.get("id")


def cleanup():
    """Elimina los archivos temporales y la carpeta de descargas."""
    if os.path.exists(TEMP_DOWNLOAD_PATH):
        shutil.rmtree(TEMP_DOWNLOAD_PATH)
        print("🗑 Carpeta de descargas eliminada.")

    zip_file_path = "data.zip"
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)
        print("🗑 Archivo ZIP eliminado.")
