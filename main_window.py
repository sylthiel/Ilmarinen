import asyncio

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtWidgets import QWidget, QGridLayout, QApplication, QTabWidget, QMainWindow, QSplitter, QTextEdit
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
        self.notation_widget = NotationWidget(self.chess_board.chessboard, self.hub)
        self.chess_board.board_registration()
        self.hub.register_listener(self.chess_board.chessboard,{
            Event.BoardChange: self.chess_board.chessboard.refresh_board,
            Event.GameLoad: self.chess_board.chessboard.handle_game_load
        })

        self.hub.register_listener(self.notation_widget,{
            Event.GameMove: self.notation_widget.handle_move,
            Event.GameLoaded: self.notation_widget.handle_game_loaded,
            Event.ArrowLeft: self.notation_widget.move_back,
            Event.ArrowRight: self.notation_widget.move_forward
        })

        self.hub.register_listener(self, {
            Event.GameLoad: self.switch_tab_on_load
        })

        self.create_first_tab()
        self.create_second_tab()

        self.setCentralWidget(self.tabWidget)  # set QTabWidget as the central widget

    def switch_tab_on_load(self, **kwargs):
        self.tabWidget.setCurrentIndex(0)

    def eventFilter(self, obj, event):
        key_to_event = {
            Qt.Key.Key_Left: Event.ArrowLeft,
            Qt.Key.Key_Right: Event.ArrowRight
         }
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in key_to_event:
                self.hub.produce_event(key_to_event[event.key()])
            return True
        else:
            return super().eventFilter(obj, event)

    def create_first_tab(self):
        tab1 = QWidget()
        layout1 = QGridLayout(tab1)
        layout1.setContentsMargins(0, 0, 0, 0)  # Add this line
        layout1.setSpacing(0)
        # The splitter between NotationWidget and ChessEngineWidget.
        splitter_notation_engine = QSplitter(Qt.Orientation.Vertical)
        splitter_notation_engine.addWidget(self.notation_widget)
        splitter_notation_engine.addWidget(self.chess_engine)
        # The main splitter between the ChessBoardWithControls and the other widgets
        splitter_main = QSplitter(Qt.Orientation.Horizontal)
        splitter_main.addWidget(self.chess_board)
        splitter_main.addWidget(splitter_notation_engine)

        layout1.addWidget(splitter_main, 0, 0)

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
    mainWindow.resize(1280, 800)
    mainWindow.show()
    app.installEventFilter(mainWindow)
    # async magic that fixes the backend process stopping UI interaction
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_forever()
    app.exec()