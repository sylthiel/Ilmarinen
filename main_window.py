import asyncio

from PyQt6.QtWidgets import QWidget, QGridLayout, QApplication
from qasync import QEventLoop

from Ilmarinen.chess_board_widget import ChessBoardWithControls
from Ilmarinen.chess_engine_widget import ChessEngineWidget
from Ilmarinen.notation_widget import NotationWidget
from Ilmarinen.widgethub import WidgetHub, Event


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout(self)
        self.chess_board = ChessBoardWithControls()
        self.chess_engine = ChessEngineWidget(self)
        self.widgetDict = {}
        self.addWidget(self.chess_board, 0, 0)
        self.layout.setRowStretch(0, 2)
        self.layout.setColumnStretch(0, 2)
        self.addWidget(ChessEngineWidget(self),1, 0, 1, 1)
        self.layout.setRowStretch(1, 1)
        self.layout.setColumnStretch(1, 1)
        self.notation_widget = NotationWidget(self.chess_board.chessboard)
        self.layout.addWidget(self.notation_widget, 0, 1, 1, 1)
        self.hub = WidgetHub()
        self.hub.register_listener(self.chess_board.chessboard,
                                   {Event.BoardChange: self.chess_board.chessboard.refresh_board})
        self.hub.register_listener(self.chess_engine,{Event.BoardChange: self.chess_engine.board_changed})
        # self.chess_board.chessboard.set_child_notation(self.notation_widget)
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