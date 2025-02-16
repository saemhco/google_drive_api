import os
import uvicorn
from services.server import app
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
