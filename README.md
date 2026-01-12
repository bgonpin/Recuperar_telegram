# Recuperación y Archivado de Canales de Telegram

Este proyecto permite archivar mensajes y recuperar archivos multimedia (imágenes, vídeos) de canales de Telegram, almacenándolos en una base de datos MongoDB. Soporta tanto una Interfaz de Línea de Comandos (CLI) como una Interfaz Gráfica de Usuario (GUI).

## Características
- **Sincronización Parcial**: Recuerda el ID del último mensaje sincronizado y solo descarga los nuevos.
- **Descarga de Multimedia**: Descarga automáticamente imágenes y vídeos de los mensajes.
- **Almacenamiento en MongoDB**: Guarda los metadatos de los mensajes y las rutas de los archivos multimedia en MongoDB.
- **Procesamiento por Lotes**: (GUI) Soporte para sincronizar múltiples canales secuencialmente.

## Requisitos Previos
- Python 3.10+
- MongoDB instalado y ejecutándose localmente (por defecto: `localhost:27017`)
- Un API ID y Hash de Telegram (obtenlo en [my.telegram.org](https://my.telegram.org))

## Instalación

1.  **Clonar el repositorio**:
    ```bash
    git clone <url_del_repositorio>
    cd <nombre_del_repositorio>
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuración del Entorno**:
    - Renombra `.env.example` a `.env`.
    - Edita `.env` y rellena tus datos:
        ```bash
        API_ID=tu_api_id
        API_HASH=tu_api_hash
        PHONE_NUMBER=+34600000000
        CHANNEL_NAME=@canal_objetivo
        ```

## Uso

### Opción 1: Interfaz de Línea de Comandos (CLI)
Ejecuta el script para sincronizar el canal único definido en `.env`:
```bash
python main.py
```
O usa el script de conveniencia:
```bash
./start.sh
```

### Opción 2: Interfaz Gráfica de Usuario (GUI)
Ejecuta la aplicación gráfica:
```bash
python main_gui.py
```
O usa el script de conveniencia:
```bash
./start_gui.sh
```

- **Seleccionar Canal**: Elige un canal del desplegable (cargados desde `canalles.txt` o `.env`).
- **Start Sync**: Sincroniza el canal seleccionado.
- **Sync All**: Procesa por lotes todos los canales de la lista.

## Descripción de la Estructura de Archivos

- **`main.py`**: Punto de entrada CLI. Inicializa el cliente de Telegram, conecta a la BD y ejecuta el bucle de sincronización.
- **`main_gui.py`**: Punto de entrada GUI. Configura la aplicación Qt y el bucle asyncio.
- **`gui.py`**: Define la clase `MainWindow` y el diseño de la interfaz (PySide6).
- **`worker.py`**: Contiene `TelegramSyncService`, manejando la lógica central (descarga/fetch) en un hilo aparte para no congelar la GUI.
- **`db.py`**: Maneja las conexiones a MongoDB, búsqueda del último ID y la inserción de documentos.
- **`settings.py`**: Carga las variables de entorno desde `.env`.
