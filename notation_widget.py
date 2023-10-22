from uuid import uuid4

import chess.pgn
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit, QTextBrowser

from Ilmarinen.custom_widget import CustomWidget
from Ilmarinen.widgethub import Event


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
        self.latest_node.uuid = uuid4()
        self.pgn_display = QTextBrowser()
        self.pgn_display.setReadOnly(True)
        self.pgn_display.setOpenExternalLinks(False)  # Prevent opening in a web browser
        self.pgn_display.anchorClicked.connect(self.link_clicked)
        self.layout.addWidget(self.pgn_display)
        self.layout.addWidget(self.move_back_btn)
        self.layout.addWidget(self.move_forward_btn)

        self.move_back_btn.clicked.connect(self.move_back)
        self.move_forward_btn.clicked.connect(self.move_forward)
        self.uuid_to_node = {self.latest_node.uuid: self.latest_node}
        self.update_pgn_display()

    def link_clicked(self, url):
        node_uuid = url.toString()[1:]  # Remove the '#' in the URL
        node = self.uuid_to_node.get(node_uuid)
        if node:
            self.go_to_move(node)

    def get_pgn(self):
        return str(self.board.game_state.game)

    def handle_move(self, **kwargs):
        # placeholder logic, need to add handling for vartiations, main variations etc.
        move = kwargs.get('move')
        move_node = None
        for variation in self.latest_node.variations:
            if variation.move == move:
                move_node = variation
        if move_node:
            self.latest_node = move_node
        else:
            new_node = self.latest_node.add_variation(kwargs.get("move"))
            new_node.uuid = str(uuid4())
            self.uuid_to_node[new_node.uuid] = new_node
            self.latest_node = new_node
        self.update_pgn_display()
        self.board.hub.produce_event(Event.BoardMove, move=kwargs.get("move"))
        self.board.hub.produce_event(Event.BoardChange)

    def update_pgn_display(self):
        # pgn = self.get_pgn()  # Get the PGN from your chess board object
        self.pgn_display.setHtml(self.generate_html_pgn())

    def move_back(self):
        if self.latest_node.parent is not None:
            print('Entered move back')
            self.current_move -= 1
            print(f"self.latest_node is {self.latest_node}")
            print(f"parent is {self.latest_node.parent}")
            self.go_to_move(self.latest_node.parent)  # Update your chess board object to this move
            # self.latest_node = self.latest_node.parent
            self.update_pgn_display()

    def generate_html_pgn(self, node=None):
        if node is None:
            node = self.latest_node.root()
        pgn_string = ''
        for i, variation in enumerate(node.variations):
            move_number = variation.ply()
            move = variation.san()
            color = 'white' if (move_number % 2 == 1) else 'black'
            if color == 'white':
                pgn_move_string = f'<a href="#{str(variation.uuid)}">{move_number//2+1}. {move}</a>'
            else:
                pgn_move_string = f'<a href="#{str(variation.uuid)}"> {move} </a>'

            if i == 0:  # main_variant
                pgn_string += pgn_move_string
                pgn_string += self.generate_html_pgn(variation)
            else:  # other_variations
                pgn_string += '('
                pgn_string += pgn_move_string
                pgn_string += self.generate_html_pgn(variation)
                pgn_string += ') '
            move_number += 1
        print(self.get_pgn())
        return pgn_string
    def go_to_move(self, node):
        print(f'Go to move requested to {node}, FEN:')
        print(node.board().fen())
        self.board.game_state.board.set_fen(node.board().fen())
        self.latest_node = node
        self.board.refresh_board()
        self.board.hub.produce_event(Event.BoardChange)

    def move_forward(self):
        # Comparing with the total number of moves, which should be retrieved from your chess board object
        next_move = self.latest_node.next()
        if next_move is not None:
            self.current_move += 1
            self.go_to_move(next_move)  # Update your chess board object to this move
            self.update_pgn_display()
