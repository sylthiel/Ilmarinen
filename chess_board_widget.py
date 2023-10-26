from itertools import product
from typing import Optional

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGridLayout, QWidget, \
    QPushButton, QGraphicsPixmapItem, QGraphicsItem, QHBoxLayout, QDialog, QSizePolicy
from PyQt6.QtGui import QColor, QPen, QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt, QRectF, QSize, pyqtSignal
import sys, os
import chess, chess.pgn
from uuid import uuid4
# from Ilmarinen.widgethub import Event, WidgetHub
import Ilmarinen.widgethub


# from Ilmarinen.database_widget import DatabaseWidget

def load_piece_assets():
    cbp = os.path.join(os.getcwd(), 'resources', 'chessboard' + os.sep)
    return {
        'R': cbp + 'white-rook.png',
        'N': cbp + 'white-knight.png',
        'B': cbp + 'white-bishop.png',
        'Q': cbp + 'white-queen.png',
        'K': cbp + 'white-king.png',
        'P': cbp + 'white-pawn.png',
        'r': cbp + 'black-rook.png',
        'n': cbp + 'black-knight.png',
        'b': cbp + 'black-bishop.png',
        'q': cbp + 'black-queen.png',
        'k': cbp + 'black-king.png',
        'p': cbp + 'black-pawn.png'
    }


class PieceRibbon(QDialog):
    piece_selected = pyqtSignal(str)
    def __init__(self, color="white", display_pieces=None):
        super().__init__()
        self.color = color
        ribbon_height = 100  # height of the QDialog
        self.setFixedHeight(ribbon_height)
        self.display_pieces = ['N', 'B', 'R', 'Q'] if display_pieces is None else display_pieces
        if self.color == "black":
            self.display_pieces = [piece.lower() for piece in self.display_pieces]
        self.piece_translation = load_piece_assets()
        self.selected_piece = None
        layout = QHBoxLayout()
        self.setLayout(layout)
        for piece in self.display_pieces:
            image = QImage(self.piece_translation[piece])
            scaled_image = image.scaled(
                int(0.8 * ribbon_height), int(0.8 * ribbon_height),  # Scale the image based on 80% of the QDialog height
                Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation  # High quality filter
            )
            pixmap = QPixmap.fromImage(scaled_image)
            button = QPushButton()
            button.setIcon(QIcon(pixmap))
            button.setIconSize(QSize(int(0.8 * ribbon_height), int(0.8 * ribbon_height)))  # Set the icon size as 80% of the QDialog height
            button.setStyleSheet("QPushButton {background-color: none; border: none;}")  # Remove button border
            button.clicked.connect(lambda x, p=piece: self.select_piece(p))
            layout.addWidget(button)

    def select_piece(self, piece):
        self.selected_piece = piece
        self.piece_selected.emit(piece)  # Emit Signal when a piece is selected
        self.close()

class GameState:
    def __init__(self, hub: Ilmarinen.widgethub.WidgetHub):
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.hub = hub

    def move_piece(self, start_square: str, end_square: str, promotion_piece: Optional[str] = None):
        print(f"Entered move_piece with {start_square}, {end_square}, {promotion_piece}")
        start = chess.parse_square(start_square)
        end = chess.parse_square(end_square)
        promotion = None
        # Convert the promotion_piece str to a python-chess piece
        if promotion_piece is not None:
            promotion = chess.Piece.from_symbol(promotion_piece.lower()).piece_type
            move = chess.Move(start, end, promotion=promotion)
        else:
            move = chess.Move(start, end)
        if move in self.board.legal_moves:
            try:
                self.hub.produce_event(Ilmarinen.widgethub.Event.GameMove, move=move)
            except Exception as e:
                print(e)
            return True
        return False


class ChessSquare(QGraphicsRectItem):
    def __init__(self, x, y, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 0, 0 by default is a8 1,0 is a7
        self.square_name = chr(ord('a') + x) + str(8 - y)
        self.coordinates = (x, y)


class Chessboard(QGraphicsView):

    def __init__(self, hub: Optional[Ilmarinen.widgethub.WidgetHub]):
        super().__init__()
        self.hub = hub
        self.selected_promotion_piece = None
        self.promotion_ribbon = None
        self.uuid = str(uuid4())
        self.flipped = False
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.game_state = GameState(hub=hub)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.piece_translation = load_piece_assets()
        self.selected_square = None
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        self.pieces = [[None for _ in range(8)] for _ in range(8)]
        self.draw_board()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

    def refresh_board(self, **kwargs):
        # **kwargs is needed because this method is designed to subscribe to certain events, some of which
        # may need to pass arguemnts to *other* subscribers to this event

        for i in range(8):
            for j in range(8):
                if self.pieces[i][j] is not None:
                    self.scene.removeItem(self.pieces[i][j])
                    self.pieces[i][j] = None

                flip_adjusted_j = j if self.flipped else 7 - j
                flip_adjusted_i = 7 - i if self.flipped else i
                piece = self.game_state.board.piece_at(chess.square(flip_adjusted_i, flip_adjusted_j))
                if piece is not None:
                    image = QImage(self.piece_translation[str(piece)])
                    scaled_image = image.scaled(
                        int(self.squares[i][j].rect().width()),
                        int(self.squares[i][j].rect().height()),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        QtCore.Qt.TransformationMode.SmoothTransformation  # High quality filter
                    )
                    pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(scaled_image))
                    pixmap_item.square = self.squares[i][j]
                    pixmap_item.setPos(self.squares[i][j].rect().left(), self.squares[i][j].rect().top())
                    self.scene.addItem(pixmap_item)
                    self.pieces[i][j] = pixmap_item

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                if square is not None:
                    self.scene.removeItem(square)
                    self.squares[row][col] = None

        self.squares = [[None for _ in range(8)] for _ in range(8)]

        rect_width = self.width() // 8
        rect_height = self.height() // 8
        colors = [QColor('white'), QColor('gray')]

        for i in range(8):
            for j in range(8):
                rect = ChessSquare(i, j, QRectF(i * rect_width, j * rect_height, rect_width, rect_height))
                pen = QPen()
                pen.setStyle(Qt.PenStyle.NoPen)
                rect.setPen(pen)
                rect.setBrush(colors[((i % 2) + j) % 2])
                self.scene.addItem(rect)
                self.squares[i][j] = rect
        self.refresh_board()

    def redraw_board(self):
        rect_width = self.width() // 8
        rect_height = self.height() // 8
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                self.scene.removeItem(square)
        for row in range(8):
            for col in range(8):
                square = self.squares[row][col]
                square.setRect(row * rect_width, col * rect_height, rect_width, rect_height)
                self.scene.addItem(square)
        self.refresh_board()

    def register_board(self):
        self.hub.produce_event(Ilmarinen.widgethub.Event.BoardCreated, board=self)

    def register_default_listeners(self):
        self.hub.register_listener(self, {
            Ilmarinen.widgethub.Event.BoardMove: self.board_move_event,
            Ilmarinen.widgethub.Event.GameTraversal: self.handle_game_traversal
        })

    def register_bypass_listeners(self):
        self.hub.register_listener(self, {
            Ilmarinen.widgethub.Event.GameMove: self.board_move_event
        })
        self.hub.register_listener(self, {
            Ilmarinen.widgethub.Event.GameMove: self.refresh_board
        })

    def board_move_event(self, move: chess.Move):
        self.game_state.board.push(move)

    def resizeEvent(self, event):
        self.setSceneRect(QRectF(self.viewport().rect()))
        self.redraw_board()
        super().resizeEvent(event)

    def reset_board(self):
        self.game_state = GameState(self.hub)
        self.refresh_board()

    def flip_board(self):
        self.flipped = not self.flipped
        for row, col in product(range(8), repeat=2):
            square = self.squares[row][col]
            old_name = square.square_name
            square.square_name = (chr(ord('h') - ord(old_name[0]) + ord('a')) +
                                  str(8 - int(old_name[1]) + 1))
        self.refresh_board()

    def handle_game_load(self, game: chess.pgn.Game):
        self.game_state.game = game
        self.game_state.board = game.board()
        self.hub.produce_event(Ilmarinen.widgethub.Event.BoardChange, board=self.game_state.board)
        self.hub.produce_event(Ilmarinen.widgethub.Event.GameLoaded)

    def handle_game_traversal(self, board: chess.Board):
        self.game_state.board.set_fen(board.fen())

    def close_current_piece_ribbon(self):
        if self.promotion_ribbon is not None:
            self.promotion_ribbon.close()
            self.promotion_ribbon = None

    def mousePressEvent(self, event):
        if self.promotion_ribbon is not None:
            self.close_current_piece_ribbon()
        item = self.itemAt(event.pos())
        if isinstance(item, QGraphicsPixmapItem):
            square = item.square
        else:
            square = item
        if isinstance(square, ChessSquare):
            if self.selected_square is None:
                piece = self.game_state.board.piece_at(chess.parse_square(square.square_name))
                if piece is not None:
                    print(f"picked up piece {square}")
                    self.selected_square = square
            else:
                start = self.selected_square.square_name
                end = square.square_name
                promotion_piece = None
                piece = self.game_state.board.piece_at(chess.parse_square(start))
                if piece.piece_type == chess.PAWN and (
                        (piece.color == chess.WHITE and end[1] == '8') or
                        (piece.color == chess.BLACK and end[1] == '1')
                ):
                    color = "white" if piece.color == chess.WHITE else "black"
                    piece_ribbon = PieceRibbon(color)
                    piece_ribbon.piece_selected.connect(lambda piece: self.handle_piece_selected(start, end, piece))
                    self.promotion_ribbon = piece_ribbon
                    self.selected_square = None
                    piece_ribbon.show()
                    return
                if promotion_piece is not None:
                    move_result = self.game_state.move_piece(start, end, promotion_piece)
                else:
                    move_result = self.game_state.move_piece(start, end)
                if move_result:
                    self.refresh_board()
                    self.selected_square = None
                else:
                    self.selected_square = None
        super().mousePressEvent(event)

    def handle_piece_selected(self, start, end, promotion_piece):
        move_result = self.game_state.move_piece(start, end, promotion_piece)
        if move_result:
            self.refresh_board()

class ChessBoardWithControls(QWidget):
    def __init__(self, hub):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.hub = hub
        self.uuid = str(uuid4())
        self.layout = QGridLayout()
        self.chessboard = self.create_chessboard()
        # self.layout.addWidget(self.chessboard, 0, 0, 1, 2)
        self.put_board_on_layout(self.chessboard)
        self.init_buttons()
        self.setLayout(self.layout)
        self.setWindowTitle('Chess Board')

    def put_board_on_layout(self, board):
        self.layout.addWidget(board, 0, 0, 1, 2)

    def init_buttons(self):
        self.reset_button = QPushButton("Reset board")
        self.reset_button.clicked.connect(self.chessboard.reset_board)
        self.flip_button = QPushButton("Flip board")
        self.flip_button.clicked.connect(self.chessboard.flip_board)
        self.layout.addWidget(self.reset_button, 1, 0, 1, 1)
        self.layout.addWidget(self.flip_button, 1, 1, 1, 1)

    def create_chessboard(self):
        return Chessboard(hub=self.hub)

    def board_registration(self):
        self.chessboard.register_board()
        self.chessboard.register_default_listeners()


def cb():
    app = QApplication(sys.argv)
    hub = Ilmarinen.widgethub.WidgetHub()
    my_app = ChessBoardWithControls(hub)
    my_app.board_registration()
    my_app.chessboard.register_bypass_listeners()
    my_app.resize(800, 800)
    my_app.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    cb()
