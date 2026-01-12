"""
Punto de Entrada Principal de la Aplicación CLI.

Este script ejecuta el proceso de recuperación de mensajes de Telegram a través de la línea de comandos.
Realiza los siguientes pasos:
1.  Conecta a la base de datos MongoDB para encontrar el último ID de mensaje sincronizado.
2.  Conecta al Cliente de Telegram usando Telethon.
3.  Itera a través del historial del canal comenzando desde el último ID sincronizado.
4.  Descarga multimedia (imágenes/videos) y los guarda localmente.
5.  Almacena los metadatos del mensaje y las rutas multimedia en MongoDB.
"""
import asyncio
import os
from telethon import TelegramClient
from telethon.tl.types import Message
import settings
import db
import sys

# Initialize Telegram Client
client = TelegramClient('telegram_session', settings.API_ID, settings.API_HASH)

async def main():
    channel_name = settings.CHANNEL_NAME
    if not channel_name:
        print("Error: CHANNEL_NAME not set in settings or .env")
        return

    # 1. Conectar a la BD y obtener el último ID sincronizado
    # Usar el nombre del canal como nombre de la colección
    # Sanitizar el nombre del canal para el nombre de la colección si es un enlace
    collection_name = channel_name.strip().split('/')[-1]
    
    print(f"Checking database for existing messages in collection '{collection_name}'...")
    min_id = db.get_latest_message_id(collection_name)
    print(f"Last synced message ID: {min_id}")

    # 2. Iniciar el cliente
    await client.start(phone=settings.PHONE_NUMBER)
    
    print(f"Fetching messages from {channel_name} starting from ID {min_id}...")

    messages_to_insert = []
    
    # 3. Obtener historial
    # reverse=True obtiene de viejo a nuevo (útil si quisiéramos procesar en orden),
    # pero iter_messages por defecto (reverse=False) es de nuevo a viejo.
    # Si usamos min_id, obtenemos mensajes MÁS NUEVOS que min_id.
    # Documentación de Telethon: min_id devuelve mensajes con ID > min_id.
    
    # Obtendremos todos los mensajes nuevos.
    async for message in client.iter_messages(channel_name, min_id=min_id, reverse=True):
        if isinstance(message, Message):
            # Serializar el objeto mensaje a un diccionario
            # message.to_dict() da una representación dict serializable en JSON completa
            msg_dict = message.to_dict()
            
            # Manejar Descarga de Multimedia
            if message.media:
                try:
                    # Crear estructura de directorios: downloads/{channel}-{msg_id}/
                    base_downloads_path = os.path.abspath(settings.DOWNLOADS_DIR)
                    folder_name = f"{collection_name}-{message.id}"
                    download_path = os.path.join(base_downloads_path, folder_name)
                    
                    os.makedirs(download_path, exist_ok=True)
                    
                    print(f"Downloading media for message {message.id}...")
                    saved_path = await message.download_media(file=download_path)
                    
                    if saved_path:
                         # Inicio del cálculo de ruta relativa
                        try:
                            storage_root = settings.STORAGE_ROOT
                            relative_path = os.path.relpath(saved_path, storage_root)
                            msg_dict['saved_media_path'] = relative_path
                        except ValueError:
                             msg_dict['saved_media_path'] = saved_path

                        print(f"Media saved to: {saved_path}")
                        
                except Exception as e:
                     print(f"Failed to download media for message {message.id}: {e}")

            # Asegurar que el campo 'date' se maneja correctamente si es necesario,
            # usualmente mongo maneja objetos datetime bien.
            # Los objetos Telethon a menudo tienen objetos datetime que PyMongo acepta.
            
            messages_to_insert.append(msg_dict)
            
            # Inserción por lotes para evitar saturación de memoria si hay millones,
            # aunque para un volcado típico de canal, 1000 a la vez está bien.
            if len(messages_to_insert) >= 100:
                db.insert_messages(collection_name, messages_to_insert)
                messages_to_insert = []

    # Insertar restantes
    if messages_to_insert:
        db.insert_messages(collection_name, messages_to_insert)

    print("Sync completed.")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
