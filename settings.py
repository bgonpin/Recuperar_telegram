"""
Módulo de Configuración.

Este módulo es responsable de cargar las variables de entorno desde el archivo .env
y proporcionarlas como constantes al resto de la aplicación.
Utiliza python-dotenv para cargar los valores.
"""
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
CHANNEL_NAME = os.getenv("CHANNEL_NAME")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "telegram")
DOWNLOADS_DIR = os.getenv("DOWNLOADS_DIR", os.path.join(os.getcwd(), "downloads"))
STORAGE_ROOT = os.getenv("STORAGE_ROOT", os.getcwd())

if not API_ID or not API_HASH:
    raise ValueError("API_ID and API_HASH must be set in the .env file")
