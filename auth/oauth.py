import os
import json
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de autenticación
SCOPES = ["https://www.googleapis.com/auth/drive",
          "https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = os.getenv("CREDENTIALS_PATH", "auth/credentials.json")
TOKEN_FILE = os.getenv("TOKEN_PATH", "auth/token.json")
HOST = os.getenv("HOST", "http://127.0.0.1")  # Tomar el HOST de .env
PORT = int(os.getenv("PORT", 8001))  # Tomar el PUERTO de .env
# Generamos la redirección correcta
REDIRECT_URI = f"{HOST}:{PORT}/auth/callback"


def save_token(creds):
    """Guarda el token en token.json con el formato correcto."""
    token_data = {
        "token": creds.token,
        # Preserva refresh_token
        "refresh_token": getattr(creds, "refresh_token", None),
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "universe_domain": getattr(creds, "universe_domain", "googleapis.com"),
        "account": getattr(creds, "account", ""),
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }

    with open(TOKEN_FILE, "w") as token_file:
        json.dump(token_data, token_file, indent=4)


def get_auth_url():
    """Genera la URL de autenticación de Google OAuth2 y fuerza la solicitud de refresh_token."""
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE, SCOPES
    )
    flow.redirect_uri = REDIRECT_URI  # Establecer el redirect_uri aquí
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",  # 🔥 Fuerza a Google a pedir el refresh_token
        include_granted_scopes="true"
    )
    print(f"✨ Abre la siguiente URL en tu navegador: {auth_url}")
    return auth_url


def exchange_code_for_token(auth_code):
    """Intercambia el código de autorización por un token de acceso."""
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES)
        flow.redirect_uri = REDIRECT_URI
        flow.fetch_token(code=auth_code)

        # Guardar credenciales en el archivo token.json
        save_token(flow.credentials)

        return flow.credentials.token
    except Exception as e:
        print(f"Error al intercambiar el código por un token: {e}")
        raise


def get_access_token():
    """Obtiene el token de acceso actual. Si 'expiry' no ha pasado, retorna el token guardado. Si expiró, lo refresca."""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as token_file:
                token_data = json.load(token_file)

            expiry_str = token_data.get("expiry")
            if expiry_str:
                expiry_time = datetime.datetime.fromisoformat(expiry_str)
                now = datetime.datetime.utcnow()

                if now < expiry_time:
                    print("✅ Token aún es válido. Devolviendo token actual.")
                    return token_data["token"]

            # Si el token ha expirado, refrescarlo
            print("🔄 Token expirado. Intentando refrescar...")
            return refresh_access_token()["token"]

        else:
            print(f"❌ El archivo {TOKEN_FILE} no existe.")
    except Exception as e:
        print(f"Error al obtener el token de acceso: {e}")
    return None


def refresh_access_token():
    """Refresca el token de acceso utilizando el refresh token y mantiene el formato original."""
    creds = None

    print("🔍 Intentando refrescar el token...")

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as token_file:
            existing_token_data = json.load(token_file)
            print("📂 Token actual:", json.dumps(existing_token_data, indent=4))

        creds = Credentials.from_authorized_user_info(existing_token_data)

    if creds and creds.refresh_token:
        creds.refresh(Request())  # Refrescar el token automáticamente
        # 🔹 Mantener el refresh_token existente y formatear correctamente
        updated_token_data = {
            "token": creds.token,
            "refresh_token": existing_token_data.get("refresh_token", creds.refresh_token),
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "universe_domain": existing_token_data.get("universe_domain", "googleapis.com"),
            "account": existing_token_data.get("account", ""),
            "expiry": creds.expiry.isoformat() if creds.expiry else None,  # 🔹 Mantener el formato
        }

        # 🔹 Guardar el token actualizado
        with open(TOKEN_FILE, "w") as token_file:
            json.dump(updated_token_data, token_file, indent=4)

        print("✅ Token actualizado con éxito:",
              json.dumps(updated_token_data, indent=4))

        return updated_token_data
    else:
        print("❌ Error: No se pudo refrescar el token. Se requiere nueva autenticación.")
        raise Exception(
            "No se pudo refrescar el token. Se requiere nueva autenticación.")


def get_credentials():
    """Obtiene las credenciales de Google Drive. Si no existen o expiran, las renueva."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refrescar el token automáticamente
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            flow.redirect_uri = REDIRECT_URI
            creds = flow.run_local_server(port=PORT)

        # Guardar el token
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds
