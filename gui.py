"""
Módulo de Interfaz Gráfica de Usuario (GUI).

Este módulo define la ventana principal de la aplicación utilizando PySide6 (Qt).
Maneja la interacción del usuario, selección de canal y activación del proceso de sincronización.
Utiliza `qasync` para integrar el bucle de eventos asyncio con el de Qt.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QStatusBar, QComboBox, QMessageBox
)
from PySide6.QtCore import Slot
import settings
import os
from worker import TelegramSyncService
import asyncio
from qasync import asyncSlot

class MainWindow(QMainWindow):
    """
    La ventana principal de la aplicación.
    
    Atributos:
        worker (TelegramSyncService): El servicio que maneja la lógica de sincronización de Telegram.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram Recover GUI")
        self.resize(800, 600)
        
        self.worker = TelegramSyncService()
        self.worker.log_signal.connect(self.log_message)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.on_sync_finished)
        self.worker.error_signal.connect(self.log_error)


        
        self.abort_batch_sync = False

        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header Info
        info_layout = QHBoxLayout()
        channel_label = QLabel("<b>Channel:</b>")
        self.channel_combo = QComboBox()
        self.load_channels()
        
        db_label = QLabel(f"<b>DB:</b> {settings.DB_NAME}")
        info_layout.addWidget(channel_label)
        info_layout.addWidget(self.channel_combo)
        info_layout.addSpacing(20)
        info_layout.addWidget(db_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Sync")
        self.start_btn.clicked.connect(self.start_sync)
        
        self.sync_all_btn = QPushButton("Sync All")
        self.sync_all_btn.clicked.connect(self.start_sync_all)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_sync)
        self.stop_btn.setEnabled(False)
        
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.sync_all_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Log Console
        layout.addWidget(QLabel("Logs:"))
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        layout.addWidget(self.log_console)
        
        # Status Bar
        self.setStatusBar(QStatusBar())
        self.update_status("Ready")
        
    def load_channels(self):
        file_path = "canalles.txt"
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                channels = [line.strip() for line in f if line.strip()]
            
            if channels:
                self.channel_combo.addItems(channels)
            else:
                 self.channel_combo.addItem(settings.CHANNEL_NAME or "")
        else:
            self.channel_combo.addItem(settings.CHANNEL_NAME or "")

    @asyncSlot()
    async def start_sync(self):
        channel_name = self.channel_combo.currentText()
        if not channel_name:
             QMessageBox.warning(self, "Error", "Please select a channel.")
             return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_message(f"Starting sync process for {channel_name}...")
        # Iniciamos la tarea asíncrona
        await self.worker.start_sync(channel_name)
        
    @asyncSlot()
    async def start_sync_all(self):
        count = self.channel_combo.count()
        if count == 0:
            QMessageBox.warning(self, "Error", "No channels to sync.")
            return

        self.start_btn.setEnabled(False)
        self.sync_all_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.abort_batch_sync = False

        self.log_message("Starting batch sync for all channels...")

        for i in range(count):
            if self.abort_batch_sync:
                self.log_message("Batch sync aborted by user.")
                break
            
            channel_name = self.channel_combo.itemText(i)
            self.channel_combo.setCurrentIndex(i) # Retroalimentación visual
            self.log_message(f"--- Processing channel {i+1}/{count}: {channel_name} ---")
            
            # ¿Esperar a que el worker termine este canal?
            # worker.start_sync es async, así que esperar (await) debería esperar a que termine
            # SI el worker fue diseñado para ser esperado correctamente.
            # Mirando worker.py: async def start_sync(self, channel_name=None):
            # Ejecuta un bucle.
            
            await self.worker.start_sync(channel_name)
            
            # Pequeña pausa entre canales
            await asyncio.sleep(1)

        self.start_btn.setEnabled(True)
        self.sync_all_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.update_status("Batch sync finished")
        self.log_message("Batch sync process completed.")

    def stop_sync(self):
        self.abort_batch_sync = True
        self.worker.stop_sync()
        self.log_message("Stopping sync...")
        self.stop_btn.setEnabled(False)
        
    @Slot(str)
    def log_message(self, message):
        self.log_console.append(message)
        
    @Slot(str)
    def log_error(self, message):
        self.log_console.append(f"<font color='red'>{message}</font>")

    @Slot(str)
    def update_status(self, status):
        self.statusBar().showMessage(status)
        
    @Slot()
    def on_sync_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.update_status("Finished")
        self.log_message("Sync process finished.")
