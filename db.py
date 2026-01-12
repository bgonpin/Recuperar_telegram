"""
Módulo de Interacción con Base de Datos.

Este módulo maneja todas las interacciones con la base de datos MongoDB.
Proporciona funciones para conectar a la BD, recuperar el último ID de mensaje sincronizado
e insertar nuevos mensajes.
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
import settings

def get_db():
    client = MongoClient(settings.MONGO_URI)
    return client[settings.DB_NAME]

def get_latest_message_id(collection_name):
    """
    Recupera el ID del mensaje más reciente almacenado en la colección.
    Devuelve 0 si la colección está vacía.
    """
    db = get_db()
    collection = db[collection_name]
    # Asumiendo que almacenamos el id del mensaje en un campo llamado 'id' o 'message_id'
    # Los IDs de mensajes de Telegram son incrementales.
    latest = collection.find_one(sort=[("id", DESCENDING)])
    
    if latest:
        return latest.get("id", 0)
    return 0

def insert_messages(collection_name, messages):
    """
    Inserta una lista de mensajes en la colección.
    Espera que los mensajes sean una lista de diccionarios.
    """
    if not messages:
        return

    db = get_db()
    collection = db[collection_name]
    
    # Asegurar unicidad estricta por si acaso, aunque min_id debería manejarlo
    # creando un índice si no existe
    collection.create_index([("id", ASCENDING)], unique=True)

    try:
        # ordered=False permite continuar la inserción incluso si algunos documentos fallan (ej. duplicados)
        # Sin embargo, como obtenemos con min_id, no deberíamos tener muchos duplicados a menos que haya una condición de carrera o solapamiento.
        # Nos quedaremos con insert_many simple por ahora o manejaremos uno por uno si se necesita deduplicación robusta.
        # Dado que el prompt pide un mecanismo para prevenir procesar mensajes ya insertados,
        # usar 'id' como índice único es la aplicación a nivel de base de datos.
        
        # Necesitamos convertir objetos Telethon a dicts si no lo son ya.
        # Asumiendo que el llamador pasa dicts o los convertimos aquí.
        # Por simplicidad, asumamos que el llamador pasa dicts.
        
        for msg in messages:
            msg['_id'] = msg['id']
        
        collection.insert_many(messages, ordered=False)
        print(f"Inserted {len(messages)} messages into {collection_name}")
    except Exception as e:
        print(f"Error inserting messages (some might be duplicates): {e}")

