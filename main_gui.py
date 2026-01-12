import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from gui import MainWindow
import settings

def main():
    app = QApplication(sys.argv)
    
    # We use qasync to integrate asyncio with Qt's event loop
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = MainWindow()
    window.show()
    
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
