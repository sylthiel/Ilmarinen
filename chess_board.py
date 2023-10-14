import os
from itertools import product

import chess
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtWidgets import QGridLayout, QPushButton, QSizePolicy, QHBoxLayout, QApplication

from Ilmarinen.custom_widget import CustomWidget
from Ilmarinen.game_state import GameState


class ChessBoardWidget(CustomWidget):
    def __init__(self):
        super().__init__()
        self.grid = QGridLayout()
        self.grid.setSpacing(0)  # Remove gaps between buttons
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.grid)
        self.board = [[None] * 8 for _ in range(8)]
        self.game_state = GameState()
        self.selected_square = None
        self.custom_configuration = self.load_custom_configuration()

        # service objects
        # translate pieces from Standard FEN to either emoji or chess font
        # pieces will be stored in piece_map
        # selected_button is a servie object for handling moves on the board, it stores the "picked up" piece
        # when clicking on a button with a piece on it
        self.piece_map = None
        self.selected_button = None
        self.chess_font = self.load_chess_font()

        self.initialize_ui()
        self.refresh_board()

    def button_clicked(self):
        sender = self.sender()  # Get the button that was clicked
        print(f'{sender.square_name} I am being pressed')
        # print(sender.square_name)
        if self.selected_button is None:
            # No piece currently selected, so select this button
            if sender.text() != "":
                self.selected_button = sender
        else:
            # Move the piece from the selected button to this button
            from_square = chess.parse_square(
                self.selected_button.square_name)  # assuming buttons have names set as square names
            to_square = chess.parse_square(sender.square_name)
            move = chess.Move(from_square, to_square)
            if move in self.game_state.get_legal_moves():
                piece = self.selected_button.text()
                # sender.setText(piece)
                self.game_state.board.push(move)
                # self.selected_button.setText("")
                self.selected_button = None
                self.refresh_board()
            else:
                print(f"{self.selected_button.square_name} to {sender.square_name} is an illegal move ")
                self.selected_button = None

    def initialize_ui(self):

        for row, col in product(range(8), repeat=2):
            button = QPushButton(self)
            sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            button.setSizePolicy(sizePolicy)
            # self.grid.setRowStretch(row, 2)
            # self.grid.setColumnStretch(col, 2)
            # button.setMinimumSize(20, 20)
            if (row + col) % 2 == 0:
                # button.setStyleSheet("background-color: white; color: black; border:1px solid black;")
                button.setStyleSheet("background-color: white; color: black;")
            else:
                button.setStyleSheet("background-color: lightblue; color: black;")
            button.setFont(self.chess_font)
            self.grid.addWidget(button, row, col)
            self.board[row][col] = button
            button.square_name = chr(ord('a') + col) + str(8 - row)
            button.coordinates = (row, col)
            button.clicked.connect(self.button_clicked)
        service_row = 8
        # self.grid.setRowStretch(service_row, 1)
        reset_button = QPushButton("Reset Board")
        reset_button.clicked.connect(self.reset_board)
        flip_button = QPushButton("Flip Board")
        flip_button.clicked.connect(self.flip_board)
        # self.grid.addWidget(reset_button, service_row, 3)
        # self.grid.addWidget(flip_button, service_row, 4)

    def reset_board(self):
        self.game_state = GameState()
        self.refresh_board()

    def flip_board(self):
        self.board = [list(reversed(row)) for row in reversed(self.board)]
        for row, col in product(range(8), repeat=2):
            button = self.board[row][col]
            old_name = button.square_name
            new_name = chr(ord('h') - ord(old_name[0]) + ord('a')) + str(8 - int(old_name[1]) + 1)
            button.square_name = new_name
        self.refresh_board()

    def refresh_board(self):
        for row, col in product(range(8), repeat=2):
            button = self.board[row][col]
            button.setText(self.piece_map.get(self.get_piece_at_position(row, col), ""))

    def get_piece_at_position(self, row, col):
        square = chess.square(col, 7 - row)  # python-chess treats rows from bottom to top
        piece = self.game_state.board.piece_at(square)
        if piece is None:  # if the square is empty
            return ""
        # Use .symbol() to get the piece's letter name
        return piece.symbol()

    def load_chess_font(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        font_path = os.path.join(dir_path, self.custom_configuration.get("chess-font-name"))
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            chess_font = QFont(font_families[0], 35)
        else:
            chess_font = self.font()  # Get the default font
        if font_id != -1:
            self.piece_map = {
                "R": "r",
                "N": "h",
                "B": "b",
                "K": "k",
                "P": "p",
                "Q": "q",
                "r": "t",
                "n": "j",
                "b": "n",
                "k": "l",
                "q": "w",
                "p": "o"
            }
        else:
            self.piece_map = {
                "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟",
                "r": "♖", "n": "♘", "b": "♗", "q": "♕", "k": "♔", "p": "♙"
            }
        return chess_font

    def load_custom_configuration(self):
        # placeholder
        return {"chess-font-name": "chess-regular.ttf"}

    def resizeEvent(self, event):
        print("chessboardwidget reisize event has been triggered")
        side = min(self.width(), self.height())
        buttonSize = side // 8
        for row in self.board:
            for button in row:
                button.setFixedSize(buttonSize, buttonSize)
                pos = button.pos()
                print(f"Button '{button.square_name}' has top-left corner at ({pos.x()}, {pos.y()})")

if __name__ == '__main__':
    app = QApplication([])
    widget = ChessBoardWidget()
    widget.show()
    app.exec()