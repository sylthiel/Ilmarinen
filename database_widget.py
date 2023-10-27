import asyncio
import os
from typing import Optional

from PyQt6 import QtWidgets, QtGui, QtCore
import sys
import chess.pgn
from PyQt6.QtCore import QModelIndex, QSize
from PyQt6.QtGui import QIcon
from qasync import QEventLoop
from PyQt6.QtWidgets import QFileDialog, QDialogButtonBox, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsPixmapItem
import PyQt6
import Ilmarinen.chess_board_widget
from Ilmarinen.pyocgdb import OpenChessGameDatabase
from Ilmarinen.widgethub import Event, WidgetHub


class SearchWindowChessboardInfo:
    def __init__(self, hub):
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.hub = hub
        self.free_mode = False

    def move_piece(self, start_square: str, end_square: str):
        print(f'here')
        if not self.free_mode:
            try:
                move = chess.Move.from_uci(start_square + end_square)
                print(f"Search window chessboard -- generated move {move}")
            except chess.InvalidMoveError:
                return False
            if move in self.board.legal_moves:
                try:
                    print(f"Board before move:\n{self.board}")
                    self.board.push(move)
                    print(f"Board after move: \n {self.board}")
                except Exception as e:
                    print(e)
                return True
            return False
        else:
            return NotImplemented


class SearchWindowChessboard(Ilmarinen.chess_board_widget.Chessboard):
    def __init__(self, hub):
        super().__init__(hub=hub)
        self.hub = hub
        self.game_state = SearchWindowChessboardInfo(self.hub)
        self.selected_from_board = False
        self.selected_piece = None

    def reset_board(self):
        self.game_state = SearchWindowChessboardInfo(self.hub)
        self.refresh_board()

    def empty_board(self):
        self.game_state.board.clear()
        self.refresh_board()

    def change_free_mode(self):
        self.game_state.free_mode = not self.game_state.free_mode

    def mousePressEvent(self, event):
        if self.promotion_ribbon is not None:
            self.close_current_piece_ribbon()
        item = self.itemAt(event.pos())
        if isinstance(item, QGraphicsPixmapItem):
            square = item.square
        else:
            square = item
        if isinstance(square, Ilmarinen.chess_board_widget.ChessSquare):
            if self.selected_piece is None:
                piece = self.game_state.board.piece_at(chess.parse_square(square.square_name))
                if piece is not None:
                    print(f"picked up piece {square}")
                    self.selected_from_board = True
                    self.selected_piece = piece
            else:
                print("I'm in else")
                print(chess.parse_square(square.square_name))
                self.game_state.board.set_piece_at(chess.parse_square(square.square_name), self.selected_piece)
                self.refresh_board()
                if self.selected_from_board:
                    self.selected_from_board = False
                    self.selected_piece = None

        # super().mousePressEvent(event)


class SearchWindow(Ilmarinen.chess_board_widget.ChessBoardWithControls):
    def __init__(self, hub):
        super().__init__(hub=hub)
        # self.chessboard = self.create_chessboard()
        img_path = os.path.join(os.getcwd(), 'resources', 'chessboard', 'buttons')
        self.empty_board_button = QPushButton()
        self.empty_board_button.clicked.connect(self.chessboard.empty_board)
        self.empty_board_button.setIcon(QIcon(os.path.join(img_path, 'empty-chessboard.png')))
        self.empty_board_button.setIconSize(QSize(32, 32))  # Adjust this size if needed.
        self.empty_board_button.setFixedSize(QSize(32, 32))  # Adjust this size if needed.
        self.button_layout.addWidget(self.empty_board_button)
        self.add_ribbons()

    def add_ribbons(self):
        self.piece_ribbon_white = Ilmarinen.chess_board_widget.PieceRibbon(color="white", display_pieces=['K', 'Q', 'R', 'B', 'N', 'P'],
                                                                           layout_type=QVBoxLayout,
                                                                           promotion=False)
        self.piece_ribbon_black = Ilmarinen.chess_board_widget.PieceRibbon(color="black",
                                                                           display_pieces=['K', 'Q', 'R', 'B', 'N', 'P'],
                                                                           layout_type=QVBoxLayout,
                                                                           promotion=False)
        self.piece_layout = QHBoxLayout()
        self.piece_layout.addWidget(self.piece_ribbon_white)
        self.piece_layout.addWidget(self.piece_ribbon_black)
        self.layout.addLayout(self.piece_layout, 0, 1, 2, 1)
        self.piece_ribbon_black.piece_selected.connect(
            lambda piece: self.set_selected_piece(chess.Piece.from_symbol(piece)))
        self.piece_ribbon_white.piece_selected.connect(
            lambda piece: self.set_selected_piece(chess.Piece.from_symbol(piece)))

    def set_selected_piece(self, piece):
        self.chessboard.selected_piece = piece
        self.chessboard.selected_from_board = False
    def create_chessboard(self):
        return SearchWindowChessboard(hub=self.hub)

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


class SearchDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, hub=Ilmarinen.widgethub.WidgetHub()):
        super().__init__(parent)
        self.setWindowTitle("Search")
        self.parent = parent
        self.layout = QtWidgets.QVBoxLayout(self)
        self.search_form = SearchWindow(hub)
        self.chessboard = self.search_form.chessboard

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self.button_box.accepted.connect(self._accept)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.search_form)
        self.layout.addWidget(self.button_box)

    def _accept(self):
        print(f"Entered _accept")
        print()
        asyncio.get_event_loop().create_task(self.accept())

    async def accept(self):
        print(self.search_form.chessboard)
        await self.parent.search_database_async(self.chessboard.game_state.board.fen())
        super().accept()


class DatabaseWidget(QtWidgets.QWidget):
    def __init__(self, hub: Optional[WidgetHub]):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.init_ui()
        self.hub = hub
        self.hub.register_listener(self, {
            Event.DatabaseSearchCompleted: self.handle_search_completed
        })
        self.current_db = None
        self.db_backend = OpenChessGameDatabase(hub)
        self.search_dialog = None

    def init_ui(self):
        self.setWindowTitle("Chess Database")
        self.resize(800, 600)
        self.buttons_row = QtWidgets.QHBoxLayout()
        self.search_button = QtWidgets.QPushButton("Search")
        self.search_button.clicked.connect(self.open_search_dialog)
        self.search_button.setDisabled(True)
        new_game_button = QtWidgets.QPushButton("New game")
        open_db_button = QtWidgets.QPushButton("Open database")
        self.buttons_row.addWidget(self.search_button)
        self.buttons_row.addWidget(new_game_button)
        self.buttons_row.addWidget(open_db_button)
        open_db_button.clicked.connect(lambda: self.open_db())
        self.layout.addLayout(self.buttons_row)
        self.game_list = QtWidgets.QListView(self)
        self.game_list.setModel(GameListModel(None))
        self.game_list.doubleClicked.connect(self.on_double_click)
        self.layout.addWidget(self.game_list)

    def handle_search_completed(self, **kwargs):
        if 'file_name' in kwargs:
            self.open_db(file=kwargs.get('file_name'))

    async def search_database_async(self, fen: str):
        '''
        :param fen:
        :return:
        Search functin parameters:
        fen: str, db: str, destination: str = 'ocgdb_query_dump.pgn',
                                    asynchronous=True, return_pgn_object=False
        '''
        print(f"Search requested with fen\n {fen}")
        status_check = chess.Board(fen).status()
        if status_check == chess.STATUS_VALID:
            await self.hub.produce_event_async(Event.DatabaseSearch, fen=fen, db=self.current_db, asynchronous=True)
        else:
            print(f"Provided FEN is not valid!")
            print(status_check)


    @QtCore.pyqtSlot()
    def open_search_dialog(self):
        if self.search_dialog is None:
            self.search_dialog = SearchDialog(self, self.hub)
            self.search_dialog.show()
        else:
            self.search_dialog.chessboard.reset_board()
            print(f'{self.search_dialog.chessboard.game_state.board}')
            self.search_dialog.show()


    def open_db(self, file=None):
        if file is None:
            file_dialog = QFileDialog(self)
            file, _ = file_dialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Chess PGN Files (*.pgn)")
        if file:
            self.current_db = file
            self.search_button.setEnabled(True)
            self.init_game_list(file)

    def init_game_list(self, db: str):
        new_model = GameListModel(db)
        new_model.db_name = db
        self.game_list.setModel(new_model)

    @QtCore.pyqtSlot(QModelIndex)
    def on_double_click(self, index):
        pgn = self.game_list.model().get_pgn(index)
        print(pgn)
        self.hub.produce_event(Event.GameLoad, game=pgn)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    hub = Ilmarinen.widgethub.WidgetHub()
    window = DatabaseWidget(hub)
    window.resize(1000, 1000)
    window.show()
    # async magic that fixes the backend process stopping UI interaction
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_forever()
    app.exec()