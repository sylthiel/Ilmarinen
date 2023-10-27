import asyncio
import os
import pickle
from typing import Optional
from collections import deque
from PyQt6 import QtWidgets, QtGui, QtCore
import sys
import chess.pgn
from PyQt6.QtCore import QModelIndex, QSize
from PyQt6.QtGui import QIcon
from qasync import QEventLoop
from PyQt6.QtWidgets import QFileDialog, QDialogButtonBox, QPushButton, QVBoxLayout, QHBoxLayout, QGraphicsPixmapItem, \
    QCheckBox, QGridLayout, QLabel, QLineEdit, QComboBox
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
                    self.selected_square = square
            else:
                print("I'm in else")
                print(chess.parse_square(square.square_name))
                self.game_state.board.set_piece_at(chess.parse_square(square.square_name), self.selected_piece)
                if self.selected_from_board:
                    self.selected_from_board = False
                    self.selected_piece = None
                    if self.selected_square is not None:
                        print(f'I should delete {self.selected_square.square_name}')
                        self.game_state.board.set_piece_at(chess.parse_square(self.selected_square.square_name),
                                                           None)
                self.refresh_board()

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
        self.add_configuration_controls()

    def add_configuration_controls(self):
        self.configs_layout = QGridLayout()
        self.configs_layout.setContentsMargins(1,1,1,1)
        self.configs_layout.setSpacing(0)
        # Configure Whose Move
        self.move_label = QLabel("Player Move")
        self.move_combobox = QComboBox()
        self.move_combobox.addItems(["White", "Black"])
        self.configs_layout.addWidget(self.move_label, 0, 0)
        self.configs_layout.addWidget(self.move_combobox, 0, 1)

        # Configure Turn Number
        self.turn_label = QLabel("Turn Number")
        self.turn_input = QLineEdit()
        self.configs_layout.addWidget(self.turn_label, 1, 0)
        self.configs_layout.addWidget(self.turn_input, 1, 1)

        self.castles_layout = QGridLayout()
        self.castle_WK = QCheckBox("White King-side")
        self.castle_WQ = QCheckBox("White Queen-Side")
        self.castle_BK = QCheckBox("Black King-side")
        self.castle_BQ = QCheckBox("Black Queen-Side")
        self.ignore_castling = QCheckBox("Ignore castling")
        self.castles_layout.addWidget(self.castle_WK, 1, 0)
        self.castles_layout.addWidget(self.castle_WQ, 1, 1)
        self.castles_layout.addWidget(self.castle_BK, 2, 0)
        self.castles_layout.addWidget(self.castle_BQ, 2, 1)
        # self.castles_layout.addWidget(self.ignore_castling) -- doesn't actually work. FEN requires castling
        self.castles_label = QLabel("Castling Rights")

        self.configs_layout.addWidget(self.castles_label, 3, 0)
        self.configs_layout.addLayout(self.castles_layout,3, 1)

        self.layout.addLayout(self.configs_layout, 0, 2)

    def get_fen_additional_parameters(self):
        fen_param_string = " "
        fen_param_string += 'w ' if self.move_combobox.currentText() == 'White' else 'b '
        fen_param_string += 'K' if self.castle_WK.isChecked() else ""
        fen_param_string += 'Q' if self.castle_WQ.isChecked() else ""
        fen_param_string += 'k' if self.castle_BK.isChecked() else ""
        fen_param_string += 'q' if self.castle_BQ.isChecked() else ""
        if len(fen_param_string) == 2:
            fen_param_string += '-'
        fen_param_string += ' - 0' #  I need if ocgdb treats the en-passant square as mandatory for position search
        try:
            turn = int(self.turn_input.text())
            if turn > 0:
                fen_param_string += f' {turn}'
        except ValueError:
            pass
        print('Fen params')
        print(fen_param_string)
        return fen_param_string

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
        fen_string = (self.chessboard.game_state.board.fen().split(' ')[0] +
                      self.search_form.get_fen_additional_parameters())

        await self.parent.search_database_async(fen_string)
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

        self.database_history = deque()
        self.history_index = -1


    def init_ui(self):
        self.setWindowTitle("Chess Database")
        self.resize(800, 600)
        self.buttons_row = QtWidgets.QHBoxLayout()
        self.search_button = QtWidgets.QPushButton("Search")
        self.search_button.clicked.connect(self.open_search_dialog)
        self.search_button.setDisabled(True)
        new_game_button = QtWidgets.QPushButton("New game")
        open_db_button = QtWidgets.QPushButton("Open database")
        self.db_forward_button = QPushButton('->')
        self.db_back_button = QPushButton('<-')
        self.db_forward_button.clicked.connect(self.go_to_next_db)
        self.db_back_button.clicked.connect(self.go_to_previous_db)
        self.buttons_row.addWidget(self.db_back_button)
        self.buttons_row.addWidget(self.db_forward_button)
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

        temp_board = chess.Board(fen)
        status_check = temp_board.status()

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

    def open_db(self, file=None, no_history=False):
        if file is None:
            file_dialog = QFileDialog(self)
            file, _ = file_dialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Chess PGN Files (*.pgn)")
        if file:
            if not no_history:
                self.database_history.append(file)
                self.history_index = len(self.database_history) - 1
            self.current_db = file
            self.search_button.setEnabled(True)
            self.init_game_list(file)
            self.save_database_history()

    def save_database_history(self):
        with open('database_history.pickle', 'wb') as f:
            pickle.dump(list(self.database_history), f)

    def load_database_history(self):
        if os.path.isfile('database_history.pickle'):
            with open('database_history.pickle', 'rb') as f:
                self.database_history = deque(pickle.load(f))
            if self.database_history:  # Check if deque is not empty
                self.open_db(self.database_history[-1])

    def go_to_previous_db(self):
        if self.history_index > 0:
            self.history_index -= 1
            previous_db = self.database_history[self.history_index]
            print(f"Going to {previous_db}")
            self.open_db(previous_db, no_history=True)

    def go_to_next_db(self):
        print(self.database_history)
        if self.history_index < len(self.database_history) - 1:
            self.history_index += 1
            next_db = self.database_history[self.history_index]
            print(f"Going to {next_db}")
            self.open_db(next_db, no_history=True)

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