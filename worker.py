import asyncio
import os
from PySide6.QtCore import QObject, Signal
from telethon import TelegramClient
from telethon.tl.types import Message
"""
Módulo de Hilo de Trabajo (Worker) para la GUI.

Este módulo contiene el `TelegramSyncService`, un QObject diseñado para ejecutarse en un hilo separado
para evitar congelar la GUI durante el proceso de sincronización de larga duración.
Comunica el progreso de vuelta a la GUI usando señales Qt.
"""
import settings
import db

class TelegramSyncService(QObject):
    """
    Maneja el proceso de sincronización de manera asíncrona.
    
    Señales:
        log_signal (str): Emite mensajes de registro para mostrar en la consola de la GUI.
        status_signal (str): Emite actualizaciones breves de estado para la barra de estado.
        finished_signal (): Emitida cuando el proceso de sincronización finaliza.
        error_signal (str): Emitida cuando ocurre un error crítico.
    """
    log_signal = Signal(str)
    status_signal = Signal(str)
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.client = TelegramClient('telegram_session', settings.API_ID, settings.API_HASH)
        self.is_running = False

    async def start_sync(self, channel_name=None):
        self.is_running = True
        try:
            if not channel_name:
                channel_name = settings.CHANNEL_NAME
            
            if not channel_name:
                self.error_signal.emit("Error: No channel selected or CHANNEL_NAME not set")
                return

            # Sanitizar el nombre de la colección
            collection_name = channel_name.strip().split('/')[-1]
            
            self.log_signal.emit(f"Checking database for existing messages in collection '{collection_name}'...")
            min_id = db.get_latest_message_id(collection_name)
            self.log_signal.emit(f"Last synced message ID: {min_id}")

            self.status_signal.emit("Connecting to Telegram...")
            await self.client.start(phone=settings.PHONE_NUMBER)
            
            self.log_signal.emit(f"Fetching messages from {channel_name} starting from ID {min_id}...")
            self.status_signal.emit("Syncing messages...")

            messages_to_insert = []
            count = 0
            
            # Obtener historial
            async for message in self.client.iter_messages(channel_name, min_id=min_id, reverse=True):
                if not self.is_running:
                     self.log_signal.emit("Sync stopped by user.")
                     break

                    if isinstance(message, Message):
                        msg_dict = message.to_dict()

                        # Manejar Descarga de Multimedia
                        if message.media:
                            try:
                                # Crear estructura de directorios: downloads/{channel}-{msg_id}/
                                # Usar ruta absoluta para asegurar que sabemos dónde está
                                # worker está en PROPIOS/RECUPERAR_TELEGRAM_GUI, así que downloads estará allí también por defecto
                            base_downloads_path = os.path.abspath(settings.DOWNLOADS_DIR)
                            folder_name = f"{collection_name}-{message.id}"
                            download_path = os.path.join(base_downloads_path, folder_name)
                            
                            os.makedirs(download_path, exist_ok=True)
                            
                            self.log_signal.emit(f"Downloading media for message {message.id}...")
                            # download_media returns the path to the file
                            saved_path = await message.download_media(file=download_path)
                            
                            if saved_path:
                                # Inicio del cálculo de ruta relativa
                                # almacenamiento raíz es /mnt/local/datos/MENSAJES_RECUPERADOS_TELEGRAM
                                # saved_path es /mnt/local/datos/MENSAJES_RECUPERADOS_TELEGRAM/downloads/...
                                try:
                                    # Queremos relativo a /mnt/local/datos/MENSAJES_RECUPERADOS_TELEGRAM
                                    # Así que si el archivo es /mnt/local/datos/MENSAJES_RECUPERADOS_TELEGRAM/downloads/chn-123/img.jpg
                                    # el relativo debería ser downloads/chn-123/img.jpg
                                    storage_root = settings.STORAGE_ROOT
                                    # Asegurar que estamos realmente dentro de esa raíz (solo una comprobación de seguridad, aunque lo forzamos vía settings)
                                    # Por robustez, si por alguna razón no es relativo, recurrimos a saved_path
                                    relative_path = os.path.relpath(saved_path, storage_root)
                                    msg_dict['saved_media_path'] = relative_path
                                except ValueError:
                                     # En Windows problemas de división de disco o fallback válido
                                     msg_dict['saved_media_path'] = saved_path
                                
                                self.log_signal.emit(f"Media saved to: {saved_path}")
                                
                        except Exception as e:
                             self.log_signal.emit(f"Failed to download media for message {message.id}: {e}")
                             # Continuamos incluso si la descarga falla, registrando el error

                    messages_to_insert.append(msg_dict)
                    
                    if len(messages_to_insert) >= 100:
                        db.insert_messages(collection_name, messages_to_insert)
                        count += len(messages_to_insert)
                        self.log_signal.emit(f"Synced {count} messages so far...")
                        messages_to_insert = []

            # Insertar restantes
            if messages_to_insert:
                db.insert_messages(collection_name, messages_to_insert)
                count += len(messages_to_insert)

            if self.is_running:
                self.log_signal.emit(f"Sync completed. Total new messages: {count}")
                self.status_signal.emit("Done.")
            
        except Exception as e:
            self.error_signal.emit(f"An error occurred: {e}")
            self.log_signal.emit(f"Error: {e}")
        finally:
            self.is_running = False
            self.finished_signal.emit()

    def stop_sync(self):
        self.is_running = False
