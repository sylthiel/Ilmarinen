import asyncio

from PyQt6.QtWidgets import QWidget, QGridLayout, QApplication, QTabWidget, QMainWindow
from qasync import QEventLoop

from Ilmarinen.chess_board_widget import ChessBoardWithControls
from Ilmarinen.chess_engine_widget import ChessEngineWidget
from Ilmarinen.database_widget import DatabaseWidget
from Ilmarinen.notation_widget import NotationWidget
from Ilmarinen.widgethub import WidgetHub, Event


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tabWidget = QTabWidget(self)  # create QTabWidget

        self.hub = WidgetHub()
        self.chess_engine = ChessEngineWidget(self, self.hub)
        self.hub.register_listener(self.chess_engine, {
            Event.BoardChange: self.chess_engine.board_changed,
            Event.BoardCreated: self.chess_engine.board_created_event
        })
        self.chess_board = ChessBoardWithControls(self.hub)


        self.notation_widget = NotationWidget(self.chess_board.chessboard)

        self.hub.register_listener(self.chess_board.chessboard,{
            Event.BoardChange: self.chess_board.chessboard.refresh_board,
            Event.GameLoad: self.chess_board.chessboard.handle_game_load
        })

        self.hub.register_listener(self.notation_widget,{
            Event.GameMove: self.notation_widget.handle_move,
            Event.GameLoaded: self.notation_widget.handle_game_loaded
        })

        self.create_first_tab()
        self.create_second_tab()

        self.setCentralWidget(self.tabWidget)  # set QTabWidget as the central widget

    def create_first_tab(self):
        tab1 = QWidget()
        layout1 = QGridLayout(tab1)
        layout1.addWidget(self.chess_board, 0, 0)
        layout1.setRowStretch(0, 2)
        layout1.addWidget(self.chess_engine, 1, 0, 1, 1)
        layout1.setRowStretch(1, 1)
        self.chess_board.chessboard.set_child_notation(self.notation_widget)
        layout1.addWidget(self.notation_widget, 0, 1)
        self.tabWidget.addTab(tab1, "First Tab")

    def create_second_tab(self):
        tab2 = QWidget()
        layout2 = QGridLayout(tab2)
        self.database_widget = DatabaseWidget(self.hub)
        layout2.addWidget(self.database_widget)
        self.tabWidget.addTab(tab2, "Second Tab")


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
