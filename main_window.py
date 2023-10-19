import asyncio

from PyQt6.QtWidgets import QWidget, QGridLayout, QApplication
from qasync import QEventLoop

from Ilmarinen.chess_board_widget import ChessBoardWithControls
from Ilmarinen.chess_engine_widget import ChessEngineWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout(self)
        self.chess_board = ChessBoardWithControls()
        self.chess_engine = ChessEngineWidget(self)
        self.widgetDict = {}
        self.addWidget(ChessBoardWithControls(), 0, 0)
        self.layout.setRowStretch(0, 2)
        self.layout.setColumnStretch(0, 2)
        self.addWidget(ChessEngineWidget(self),1, 0, 1, 1)
        self.layout.setRowStretch(1, 1)
        self.layout.setColumnStretch(1, 1)

        # print(self.widgetDict)


    def addWidget(self, widget, row, col, h=1, w=1):
        self.layout.addWidget(widget, row, col, h, w)
        if widget.__class__ not in self.widgetDict:
            self.widgetDict[widget.__class__] = {}
        self.widgetDict[widget.__class__][widget.uuid] = widget


if __name__ == '__main__':
    app = QApplication([])
    mainWindow = MainWindow()
    mainWindow.resize(1000, 1000)
    mainWindow.show()
    # async magic that fixes the backend process stopping UI interaction
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_forever()
    app.exec()