from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit

from Ilmarinen.custom_widget import CustomWidget


class NotationWidget(CustomWidget):
    def __init__(self, parent_board):
        super().__init__()
        self.board = parent_board
        self.current_move = 0  # Keeps track of the current move number to show
        self.layout = QVBoxLayout(self)
        self.board.set_child_notation(self)
        self.move_back_btn = QPushButton('<')
        self.move_forward_btn = QPushButton('>')
        self.latest_node = self.board.game_state.game
        self.pgn_display = QTextEdit()
        self.pgn_display.setReadOnly(True)

        self.layout.addWidget(self.pgn_display)
        self.layout.addWidget(self.move_back_btn)
        self.layout.addWidget(self.move_forward_btn)

        self.move_back_btn.clicked.connect(self.move_back)
        self.move_forward_btn.clicked.connect(self.move_forward)

        self.update_pgn_display()

    def get_pgn(self):
        return str(self.board.game_state.game)


    def set_latest_node(self, node):
        self.latest_node = node
    def update_pgn_display(self):
        pgn = self.get_pgn()  # Get the PGN from your chess board object
        self.pgn_display.setPlainText(pgn)

    def move_back(self):
        if self.latest_node.parent is not None:
            print('Entered move back')
            self.current_move -= 1
            print(f"self.latest_node is {self.latest_node}")
            print(f"parent is {self.latest_node.parent}")

            self.go_to_move(self.latest_node.parent)  # Update your chess board object to this move
            # self.latest_node = self.latest_node.parent
            self.update_pgn_display()

    def go_to_move(self, node):
        print(f'Go to move requested to {node}, FEN:')
        print(node.board().fen())
        self.board.game_state.board.set_fen(node.board().fen())
        self.latest_node = node
        self.board.refresh_board()
    def move_forward(self):
        # Comparing with the total number of moves, which should be retrieved from your chess board object
        next_move = self.latest_node.next()
        if next_move is not None:
            self.current_move += 1
            self.go_to_move(next_move)  # Update your chess board object to this move
            self.update_pgn_display()

