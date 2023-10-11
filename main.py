from PyQt6.QtWidgets import QApplication
import asyncio
from qasync import QEventLoop, asyncSlot

from Ilmarinen.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication([])
    mainWindow = MainWindow()
    mainWindow.show()
    #async magic that fixes the backend process stopping UI interaction
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_forever()
    app.exec()

