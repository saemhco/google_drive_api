import os
import shutil
import zipfile

DOWNLOAD_FOLDER = "downloads"
ZIP_FOLDER = "zipped"


def compress_folder(folder_path):
    """Comprime una carpeta en un archivo ZIP."""
    zip_name = os.path.basename(folder_path) + ".zip"
    zip_path = os.path.join(ZIP_FOLDER, zip_name)

    if not os.path.exists(ZIP_FOLDER):
        os.makedirs(ZIP_FOLDER)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file), folder_path))
    print(f"✅ Carpeta comprimida en: {zip_path}")
    return zip_path


def clean_up(folder_path):
    """Elimina una carpeta y su contenido."""
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"🧹 Carpeta eliminada: {folder_path}")
