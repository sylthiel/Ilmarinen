from itertools import product

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGridLayout, QWidget, \
    QPushButton, QGraphicsPixmapItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen, QPixmap, QImage
from PyQt6.QtCore import Qt , QRectF
import sys, os
import chess, chess.pgn
from uuid import uuid4
from Ilmarinen.widgethub import Event, WidgetHub
from Ilmarinen.database_widget import DatabaseWidget

class GameState:
    def __init__(self, parent):
        self.board = chess.Board()
        self.game = chess.pgn.Game()
        self.parent = parent
        print('I am gamestate in __init__')

    def move_piece(self, start_square, end_square):
        # print(f'Attempting move {start_square+end_square}')
        try:
            move = chess.Move.from_uci(start_square + end_square)
        except chess.InvalidMoveError:
            return False
        if move in self.board.legal_moves:
            # print(f"Making move {move}")
            # self.board.push(move)
            # print(f"Currently child notation is {self.parent.child_notation}")
            try:
                self.parent.hub.produce_event(Event.GameMove, move=move)
            except Exception as e:
                print(e)
            return True
        return False


class ChessSquare(QGraphicsRectItem):
    def __init__(self, x, y, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 0, 0 by default is a8 1,0 is a7
        self.square_name = chr(ord('a')+x) + str(8-y)
        self.coordinates = (x, y)
        # self.setFlags(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)


class Chessboard(QGraphicsView):
    def __init__(self, parent, hub: WidgetHub):
        print('Board is being created')
        super().__init__()
        self.parent = parent
        self.hub = hub
        self.hub.register_listener(self, {Event.BoardMove: self.board_move_event})
        self.flipped = False
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.game_state = GameState(self)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        cbp = os.path.join(os.getcwd(), 'resources', 'chessboard' + os.sep)
        self.piece_translation = {
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

        self.selected_square = None
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        self.pieces = [[None for _ in range(8)] for _ in range(8)]
        self.draw_board()
        self.child_notation = None
        self.hub.produce_event(Event.BoardCreated, board=self)
        # self.flip_board()

    def board_move_event(self, move: chess.Move):
        self.game_state.board.push(move)

    def set_child_notation(self, notation):
        print(f"{self} had its notation child set to {notation}")
        self.child_notation = notation
    def resizeEvent(self, event):
        self.setSceneRect(QRectF(self.viewport().rect()))
        self.redraw_board()
        super().resizeEvent(event)

    def reset_board(self):
        self.game_state = GameState(self)
        self.refresh_board()


    def flip_board(self):
        self.flipped = not self.flipped
        # self.squares = [list(reversed(row)) for row in reversed(self.squares)]
        for row, col in product(range(8), repeat=2):
            square = self.squares[row][col]
            old_name = square.square_name
            square.square_name = chr(ord('h') - ord(old_name[0]) + ord('a')) + str(8 - int(old_name[1]) + 1)
        self.refresh_board()

    def handle_game_load(self, game: chess.pgn.Game):
        self.game_state.game = game
        self.game_state.board = game.board()
        self.hub.produce_event(Event.BoardChange, board=self.game_state.board)
        self.hub.produce_event(Event.GameLoaded)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, QGraphicsPixmapItem):
            square = item.square
        else:
            square = item
        if isinstance(square, ChessSquare):
            # print(f"Entered mouse press event with {square.square_name}")
            # print(f"Currently selected is {self.selected_square}")
            if self.selected_square is None:
                # piece = self.game_state.board.piece_at(chess.square(square.coordinates[0], 7 - square.coordinates[1]))
                piece = self.game_state.board.piece_at(chess.parse_square(square.square_name))
                if piece is not None:
                    self.selected_square = square
            else:
                if self.game_state.move_piece(self.selected_square.square_name, square.square_name):
                    self.refresh_board()
                    self.selected_square = None
                else:
                    self.selected_square = None
        super().mousePressEvent(event)

    def refresh_board(self, **kwargs):
        # print('-----------'*3)
        for i in range(8):
            for j in range(8):
                # remove the previous piece on this square if it exists
                if self.pieces[i][j] is not None:
                    self.scene.removeItem(self.pieces[i][j])
                    self.pieces[i][j] = None

                flip_adjusted_j = j if self.flipped else 7 - j
                flip_adjusted_i = 7-i if self.flipped else i
                piece = self.game_state.board.piece_at(chess.square(flip_adjusted_i, flip_adjusted_j))
                # print(f"I'm at {i} {j} and got piece {piece}")
                if piece is not None:
                    # print(f'At position {i} {j} there is {piece}')
                    # print(f'Trying to get piece {piece} at square {i}x{j}')
                    image = QImage(self.piece_translation[str(piece)])
                    scaled_image = image.scaled(
                        int(self.squares[i][j].rect().width()),
                        int(self.squares[i][j].rect().height()),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        QtCore.Qt.TransformationMode.SmoothTransformation  # High quality filter
                    )
                    pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(scaled_image))
                    # pixmap = QPixmap(self.piece_translation[str(piece)])
                    # pixmap_item = QGraphicsPixmapItem(pixmap.scaled(
                    #     int(self.squares[i][j].rect().width()),
                    #     int(self.squares[i][j].rect().height()),
                    #     Qt.AspectRatioMode.KeepAspectRatio
                    # ))
                    pixmap_item.square = self.squares[i][j]
                    pixmap_item.setPos(self.squares[i][j].rect().left(), self.squares[i][j].rect().top())
                    self.scene.addItem(pixmap_item)
                    self.pieces[i][j] = pixmap_item

    def draw_board(self):
        # print('Entered draw board')
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
                # rect = QGraphicsRectItem(QRectF(i * rect_width, j * rect_height, rect_width, rect_height))
                rect = ChessSquare(i, j, QRectF(i * rect_width, j * rect_height, rect_width, rect_height))
                pen = QPen()
                pen.setStyle(Qt.PenStyle.NoPen)
                rect.setPen(pen)
                rect.setBrush(colors[((i % 2) + j) % 2])
                self.scene.addItem(rect)
                self.squares[i][j] = rect
        # print("After draw_board()")
        # print(self.squares)
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
                square.setRect(row*rect_width, col*rect_height, rect_width, rect_height)
                self.scene.addItem(square)
        self.refresh_board()


class ChessBoardWithControls(QWidget):
    def __init__(self, hub):
        super().__init__()
        self.hub = hub
        self.uuid = str(uuid4())
        layout = QGridLayout()
        self.chessboard = Chessboard(parent=self, hub=self.hub)
        self.reset_button = QPushButton("Reset board")
        self.reset_button.clicked.connect(self.chessboard.reset_board)
        self.flip_button = QPushButton("Flip board")
        self.flip_button.clicked.connect(self.chessboard.flip_board)
        layout.addWidget(self.chessboard, 0, 0, 1, 2)
        # layout.setRowStretch(0, 1)
        # layout.setColumnStretch(0, 1)
        layout.addWidget(self.reset_button, 1, 0, 1, 1)
        layout.addWidget(self.flip_button, 1, 1, 1, 1)
        self.setLayout(layout)
        self.setWindowTitle('Chess Board')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    my_app = ChessBoardWithControls()
    my_app.resize(800, 800)
    my_app.show()

    sys.exit(app.exec())