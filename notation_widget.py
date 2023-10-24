from uuid import uuid4

import chess.pgn
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit, QTextBrowser, QApplication, QLabel, QHBoxLayout

from Ilmarinen.custom_widget import CustomWidget
from Ilmarinen.widgethub import Event


class NotationWidget(CustomWidget):
    def __init__(self, parent_board):
        super().__init__()
        self.board = parent_board
        self.current_move = 0  # Keeps track of the current move number to show
        self.layout = QVBoxLayout(self)
        self.headers_layout = QHBoxLayout()

        self.white_label = QLabel()
        self.black_label = QLabel()
        self.event_label = QLabel()
        self.site_label = QLabel()
        self.date_label = QLabel()
        self.result_label = QLabel()
        self.headers_layout.addWidget(self.white_label)
        self.headers_layout.addWidget(self.black_label)
        self.headers_layout.addStretch()
        self.headers_layout.addWidget(self.event_label)
        self.headers_layout.addWidget(self.site_label)
        self.headers_layout.addWidget(self.date_label)
        self.headers_layout.addWidget(self.result_label)
        self.layout.addLayout(self.headers_layout)


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

    def update_header_display(self):
        headers = self.board.game_state.game.headers

        # updating labels with header values or 'Unknown' if not provided
        self.white_label.setText(headers.get('White', 'Unknown') + " - " + headers.get('Black', 'Unknown'))
        self.event_label.setText(headers.get('Event', 'Unknown'))
        self.site_label.setText(headers.get('Site', 'Unknown'))
        self.date_label.setText(headers.get('Date', 'Unknown'))
        self.result_label.setText(headers.get('Result', 'Unknown'))

    def link_clicked(self, url):
        node_uuid = url.toString()[1:]  # Remove the '#' in the URL
        node = self.uuid_to_node.get(node_uuid)
        print(f"Clicking on {node_uuid}, going to {node}")
        print(f"{self.uuid_to_node}")
        if node:
            self.go_to_move(node)


    def handle_game_loaded(self):
        self.latest_node = self.board.game_state.game
        self.latest_node.uuid = uuid4()
        # self.uuid_to_node = {self.latest_node.uuid: self.latest_node}
        self.uuid_to_node = {}
        self.traverse_and_generate_uuid()
        self.update_pgn_display()
        self.update_header_display()

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
        self.board.hub.produce_event(Event.BoardChange, board=self.latest_node.board())

    def update_pgn_display(self):
        # pgn = self.get_pgn()  # Get the PGN from your chess board object
        self.pgn_display.setHtml(self.generate_html_pgn())

    def move_back(self):
        if self.latest_node.parent is not None:
            print('Entered move back')
            self.current_move -= 1
            # print(f"self.latest_node is {self.latest_node}")
            # print(f"parent is {self.latest_node.parent}")
            self.go_to_move(self.latest_node.parent)  # Update your chess board object to this move
            # self.latest_node = self.latest_node.parent
            self.update_pgn_display()

    def traverse_and_generate_uuid(self):
        stack = [self.latest_node]
        while stack:
            node = stack.pop()
            node.uuid = str(uuid4())
            self.uuid_to_node[node.uuid] = node
            stack.extend(child for child in node.variations)
        # print("Finished traversing")
        # print(self.uuid_to_node)

    def generate_html_pgn(self, node=None):
        if node is None:
            node = self.latest_node.root()
        current_uuid = None if not self.latest_node else str(self.latest_node.uuid)
        current_move_css = '<span style="background-color:lightblue;color:black;">'
        end_current_move_css = "</span>"
        pgn_string = ''

        if node.variations:
            main_variation = node.variations[0]
            move_number = main_variation.ply()
            move = main_variation.san()
            color = 'white' if (move_number % 2 == 1) else 'black'
            if color == 'white':
                pgn_move_string = f'{move_number // 2 + 1}. {move}'
            else:
                pgn_move_string = f' {move} '

            if str(main_variation.uuid) == current_uuid:
                pgn_move_string = current_move_css + pgn_move_string + end_current_move_css

            pgn_string += (f'<a href="#{str(main_variation.uuid)}" style="color:darkgray;text-decoration:none;outline: '
                           f'none">{pgn_move_string}</a>')
            # print(pgn_string)
            for i, variation in enumerate(node.variations[1:], start=1):
                move_number = variation.ply()
                move = variation.san()
                color = 'white' if (move_number % 2 == 1) else 'black'
                if color == 'white':
                    pgn_move_string = f'{move_number // 2 + 1}. {move}'
                else:
                    pgn_move_string = f' {move} '

                if str(variation.uuid) == current_uuid:
                    pgn_move_string = current_move_css + pgn_move_string + end_current_move_css

                pgn_string += (f'(<a href="#{str(variation.uuid)}" style="color:black;text-decoration:none;outline: '
                               f'none">{pgn_move_string}</a>')
                pgn_string += self.generate_html_pgn(variation) + ') '

            pgn_string += self.generate_html_pgn(main_variation)
        return pgn_string
    def go_to_move(self, node):
        print(f'Go to move requested to {node}, FEN:')
        print(node.board().fen())
        self.board.game_state.board.set_fen(node.board().fen())
        self.latest_node = node
        self.board.refresh_board()
        self.board.hub.produce_event(Event.BoardChange, board=node.board())

    def move_forward(self):
        # Comparing with the total number of moves, which should be retrieved from your chess board object
        next_move = self.latest_node.next()
        if next_move is not None:
            self.current_move += 1
            self.go_to_move(next_move)  # Update your chess board object to this move
            self.update_pgn_display()
