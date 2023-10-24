from typing import Optional

from PyQt6 import QtWidgets, QtGui, QtCore
import sys
import chess.pgn
from PyQt6.QtCore import QModelIndex
from PyQt6.QtWidgets import QFileDialog

from Ilmarinen.widgethub import Event, WidgetHub


class GameListModel(QtCore.QAbstractListModel):
    def __init__(self, db_name: Optional[str]):
        super().__init__()
        self.games = []
        self.db_name = db_name
        if db_name is None:
            self.games_generator = db_name
        else:
            self.games_generator = self.load_games()
            self.load_first_batch()


    def load_first_batch(self):
        n = 100
        for _ in range(n):
            try:
                self.games.append(next(self.games_generator))
            except StopIteration:
                break
    def load_new_db(self, db):
        self.games = []
        self.games_generator = self.load_games(db)
        self.load_first_batch()


    def load_games(self):
        with open(self.db_name) as pgn:
            while True:
                game = chess.pgn.read_game(pgn)
                if game is None:
                    break
                yield game

    def get_pgn(self, index):
        return self.games[index.row()]

    def rowCount(self, parent=None):
        return len(self.games)

    def data(self, index, role):
        if self.games_generator is not None:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                game = self.games[index.row()]
                return f"{game.headers['White']} - {game.headers['Black']} | {game.headers['Event']}"
            # elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
            #     return f"Game played at {game.headers['Date']}"

    def canFetchMore(self, index):
        if self.games_generator is not None:
            try:
                self.games.append(next(self.games_generator))
                return True
            except StopIteration:
                return False
        else:
            return False

    def fetchMore(self, index):
        self.beginResetModel()
        self.games.append(next(self.games_generator))
        self.endResetModel()


class DatabaseWidget(QtWidgets.QWidget):
    def __init__(self, hub: Optional[WidgetHub]):
        super().__init__()
        self.initUI()
        self.hub = hub

    def initUI(self):
        self.setWindowTitle("Chess Database")
        self.resize(800, 600)

        self.layout = QtWidgets.QVBoxLayout(self)

        buttons_row = QtWidgets.QHBoxLayout()
        search_button = QtWidgets.QPushButton("Search")
        new_game_button = QtWidgets.QPushButton("New game")
        open_db_button = QtWidgets.QPushButton("Open database")
        buttons_row.addWidget(search_button)
        buttons_row.addWidget(new_game_button)
        buttons_row.addWidget(open_db_button)
        open_db_button.clicked.connect(self.open_db)
        self.layout.addLayout(buttons_row)
        self.game_list = QtWidgets.QListView(self)
        self.game_list.setModel(GameListModel(None))
        self.game_list.doubleClicked.connect(self.on_double_click)
        self.layout.addWidget(self.game_list)

    def open_db(self):
        file_dialog = QFileDialog(self)
        file, _ = file_dialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                              "All Files (*);;Chess PGN Files (*.pgn)")
        if file:
            self.init_game_list(file)

    def init_game_list(self, db: str):
        new_model = GameListModel(db)
        new_model.db_name = db
        self.game_list.setModel(new_model)

    @QtCore.pyqtSlot(QModelIndex)
    def on_double_click(self, index):
        pgn = self.game_list.model().get_pgn(index)
        # print(pgn_text)
        self.hub.produce_event(Event.GameLoad, game=pgn)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = DatabaseWidget(None)
    window.show()

    sys.exit(app.exec())
