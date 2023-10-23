from typing import Optional

from PyQt6 import QtWidgets, QtGui, QtCore
import sys
import chess.pgn
from PyQt6.QtCore import QModelIndex

from Ilmarinen.widgethub import Event, WidgetHub

def load_games():
    with open('tal.pgn') as pgn:
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            yield game


class GameListModel(QtCore.QAbstractListModel):
    def __init__(self, games=None):
        super().__init__()
        self.games = []
        self.games_generator = load_games()

        # preload the first n games
        n = 100
        for _ in range(n):
            try:
                self.games.append(next(self.games_generator))
            except StopIteration:
                break

    def getPgnText(self, index):
        return self.games[index.row()]

    def rowCount(self, parent=None):
        return len(self.games)

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            game = self.games[index.row()]
            return f"{game.headers['White']} - {game.headers['Black']} | {game.headers['Event']}"
        # elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
        #     return f"Game played at {game.headers['Date']}"

    def canFetchMore(self, index):
        try:
            self.games.append(next(self.games_generator))
            return True
        except StopIteration:
            return False

    def fetchMore(self, index):
        self.beginResetModel()
        self.games.append(next(self.games_generator))
        self.endResetModel()


class DatabaseWidget(QtWidgets.QWidget):
    def __init__(self, hub: Optional[WidgetHub]):
        super().__init__()
        self.games = load_games()
        self.initUI()
        self.hub = hub

    def initUI(self):
        self.setWindowTitle("Chess Database")
        self.resize(800, 600)

        layout = QtWidgets.QVBoxLayout(self)

        buttons_row = QtWidgets.QHBoxLayout()
        search_button = QtWidgets.QPushButton("Search")
        new_game_button = QtWidgets.QPushButton("New game")

        buttons_row.addWidget(search_button)
        buttons_row.addWidget(new_game_button)

        layout.addLayout(buttons_row)

        self.game_list = QtWidgets.QListView(self)
        self.game_list.setModel(GameListModel())
        self.game_list.doubleClicked.connect(self.on_double_click)
        layout.addWidget(self.game_list)

    @QtCore.pyqtSlot(QModelIndex)
    def on_double_click(self, index):
        pgn = self.game_list.model().getPgnText(index)
        # print(pgn_text)
        self.hub.produce_event(Event.GameLoad, game=pgn)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = DatabaseWidget(None)
    window.show()

    sys.exit(app.exec())
