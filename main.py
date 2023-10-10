from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from itertools import product

class ChessBoardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_button = None

    def buttonClicked(self):
        sender = self.sender()  # Get the button that was clicked

        if self.selected_button is None:
            # No piece currently selected, so select this button
            self.selected_button = sender
        else:
            # Move the piece from the selected button to this button
            piece = self.selected_button.text()
            sender.setText(piece)
            self.selected_button.setText("")
            self.selected_button = None

    def initUI(self):
        grid = QGridLayout()
        grid.setSpacing(0)  # Remove gaps between buttons
        self.setLayout(grid)

        font = self.font()  # Get the default font
        font.setPointSize(40)  # Increase font size
        # font.setWeight(QFont.Bold)
        for row, col in product(range(8), repeat=2):
            button = QPushButton(self)
            # button.setStyleSheet("background-color: white;")
            # button.setStyleSheet("background-color: white; border:1px solid black;")
            if (row + col) % 2 == 0:
                button.setStyleSheet("background-color: white; color: black; border:1px solid black;font-weight: bold")
            else:
                button.setStyleSheet("background-color: lightblue; color: black; border:1px solid black;font-weight: bold")
            button.setFixedSize(50, 50)  # Make buttons square
            button.setFont(font)  # Set the font
            grid.addWidget(button, row, col)

        reset_button = QPushButton("Reset Board")
        reset_button.clicked.connect(self.resetBoard)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(reset_button)
        layout.addStretch()

        grid.addLayout(layout, 8, 0, 1, 8)

        self.setWindowTitle("Chess Board")

    def resetBoard(self):
        piece_map = {
            "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟",
            "r": "♖", "n": "♘", "b": "♗", "q": "♕", "k": "♔", "p": "♙"
        }

        for row, col in product(range(8), repeat=2):
            button = self.layout().itemAtPosition(row, col).widget()
            button.setText(piece_map.get(self.getPieceAtPosition(row, col), ""))

    def getPieceAtPosition(self, row, col):
        starting_positions = {
            (0, 0): "R", (0, 1): "N", (0, 2): "B", (0, 3): "Q", (0, 4): "K", (0, 5): "B", (0, 6): "N", (0, 7): "R",
            (1, 0): "P", (1, 1): "P", (1, 2): "P", (1, 3): "P", (1, 4): "P", (1, 5): "P", (1, 6): "P", (1, 7): "P",
            (6, 0): "p", (6, 1): "p", (6, 2): "p", (6, 3): "p", (6, 4): "p", (6, 5): "p", (6, 6): "p", (6, 7): "p",
            (7, 0): "r", (7, 1): "n", (7, 2): "b", (7, 3): "q", (7, 4): "k", (7, 5): "b", (7, 6): "n", (7, 7): "r"
        }

        return starting_positions.get((row, col), "")


if __name__ == "__main__":
    app = QApplication([])
    widget = ChessBoardWidget()

    # Connect the buttonClicked slot to each button's clicked signal
    for row, col in product(range(8), repeat=2):
        button = widget.layout().itemAtPosition(row, col).widget()
        button.clicked.connect(widget.buttonClicked)

    widget.show()
    app.exec()
