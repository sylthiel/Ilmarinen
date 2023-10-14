import os
from itertools import product

import chess
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtWidgets import QGridLayout, QPushButton, QHBoxLayout, QSizePolicy, QSpacerItem

from Ilmarinen.custom_widget import CustomWidget
from Ilmarinen.game_state import GameState


class ChessBoardWidget(CustomWidget):
    def __init__(self):
        super().__init__()
        self.board = [[None] * 8 for _ in range(8)]  # Nested list to store all buttons
        self.game_state = None
        self.initUI()
        self.selected_button = None


    def buttonClicked(self):
        sender = self.sender()  # Get the button that was clicked
        print('I am being pressed')
        # print(sender.square_name)
        if self.selected_button is None:
            # No piece currently selected, so select this button
            if sender.text() != "":
                self.selected_button = sender
        else:
            # Move the piece from the selected button to this button
            from_square = chess.parse_square(self.selected_button.square_name)  # assuming buttons have names set as square names
            to_square = chess.parse_square(sender.square_name)
            move = chess.Move(from_square, to_square)
            if move in self.game_state.get_legal_moves():
                piece = self.selected_button.text()
                # sender.setText(piece)
                self.game_state.board.push(move)
                # self.selected_button.setText("")
                self.selected_button = None
                self.refreshBoard()

            else:
                print(f"{self.selected_button.square_name} to {sender.square_name} is an illegal move ")
                self.selected_button = None

    def initUI(self):
        grid = QGridLayout()
        grid.setSpacing(0)  # Remove gaps between buttons
        grid.setContentsMargins(0, 0, 0, 0)
        self.setLayout(grid)
        chessboardSize = self.size().height()  # assume square chessboard
        buttonFixedSize = chessboardSize // 8  # assuming 8x8 grid
        dir_path = os.path.dirname(os.path.realpath(__file__))
        font_path = os.path.join(dir_path, "chess-regular.TTF")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            font = QFont(font_families[0], 35)
            self.used_font = 'custom'
        else:
            font = self.font()  # Get the default font
            font.setPointSize(40)  # Increase font size
            self.used_font = 'default'
        if self.used_font is None or self.used_font != 'custom':
            self.piece_map = {
                "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟",
                "r": "♖", "n": "♘", "b": "♗", "q": "♕", "k": "♔", "p": "♙"
            }
        else:
            # see chess-regular.ttf character mappings for more idea of wtf is going on
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
        # font.setWeight(QFont.Bold)
        for row, col in product(range(8), repeat=2):
            button = QPushButton(self)
            sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
            button.setSizePolicy(sizePolicy)
            button.setMinimumSize(20, 20)
            # button.setFixedSize(buttonFixedSize, buttonFixedSize)
            if (row + col) % 2 == 0:
                # button.setStyleSheet("background-color: white; color: black; border:1px solid black;")
                button.setStyleSheet("background-color: white; color: black;")
            else:
                button.setStyleSheet("background-color: lightblue; color: black;")
                # button.setStyleSheet("background-color: lightblue; color: black; border:1px solid black;")
            # button.setFixedSize(50, 50)  # Make buttons square
            # print(font)
            button.setFont(font)  # Set the font
            grid.addWidget(button, row, col)
            self.board[row][col] = button
            button.square_name = chr(ord('a') + col) + str(8 - row)
            button.coordinates = (row, col)
            button.clicked.connect(self.buttonClicked)

        reset_button = QPushButton("Reset Board")
        reset_button.clicked.connect(self.resetBoard)
        flip_button = QPushButton("Flip Board")
        flip_button.clicked.connect(self.flipBoard)

        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout = QHBoxLayout()
        # layout.addStretch()
        layout.addWidget(reset_button)
        # layout.addStretch()
        layout.addWidget(flip_button)
        layout.addSpacerItem(spacer)
        # layout.addStretch()

        grid.addLayout(layout, 8, 0, 1, 8)

        self.setWindowTitle("Chess Board")
        self.resetBoard()


    def refreshBoard(self):
        for row, col in product(range(8), repeat=2):
            button = self.board[row][col]
            button.setText(self.piece_map.get(self.getPieceAtPosition(row, col), ""))
    def flipBoard(self):
        # self.game_state.flip()
        self.board = [list(reversed(row)) for row in reversed(self.board)]
        for row, col in product(range(8), repeat=2):
            button = self.board[row][col]
            old_name = button.square_name
            new_name = chr(ord('h') - ord(old_name[0]) + ord('a')) + str(8 - int(old_name[1]) + 1)
            button.square_name = new_name
        self.refreshBoard()

    def resetBoard(self):
        self.game_state = GameState()
        self.refreshBoard()

    def resizeEvent(self, event):
        print("chessboardwidget reisize event has been triggered")
        side = min(self.width(), self.height())
        buttonSize = side // 8

        for row in self.board:
            for button in row:
                button.setFixedSize(buttonSize, buttonSize)
                pos = button.pos()
                print(f"Button '{button.square_name}' has top-left corner at ({pos.x()}, {pos.y()})")

    def getPieceAtPosition(self, row, col):
        square = chess.square(col, 7 - row)  # python-chess treats rows from bottom to top
        piece = self.game_state.board.piece_at(square)
        if piece is None:  # if the square is empty
            return ""
        # Use .symbol() to get the piece's letter name
        return piece.symbol()
