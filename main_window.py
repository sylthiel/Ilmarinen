from PyQt6.QtWidgets import QWidget, QMessageBox, QHBoxLayout, QPushButton

from Ilmarinen.chess_board_widget import ChessBoardWidget
from Ilmarinen.chess_engine_widget import ChessEngineWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.add_widget_message_box = QMessageBox(self)
        self.add_widget_message_box.setText("What type of widget do you want to add?")
        self.board_button = self.add_widget_message_box.addButton("Board", QMessageBox.ButtonRole.AcceptRole)
        self.engine_button = self.add_widget_message_box.addButton("Engine", QMessageBox.ButtonRole.AcceptRole)

        self.layout = QHBoxLayout(self)
        self.add_button = QPushButton('+')
        self.add_button.clicked.connect(self.add_widget_option)

        self.widgetDict = {}

        self.layout.addWidget(self.add_button)

        self.initial_widget = ChessBoardWidget()
        self.layout.addWidget(self.initial_widget)
        self.add_widget_to_dict(self.initial_widget)
        self.setLayout(self.layout)

    def add_widget_option(self):
        self.add_widget_message_box.exec()
        clicked_button = self.add_widget_message_box.clickedButton()
        if clicked_button == self.board_button:  # If the user clicked "Board"
            self.add_new_board_widget()
        elif clicked_button == self.engine_button:  # If the user clicked "Engine"
            self.add_new_engine_widget()

    def add_widget_to_dict(self, widget):
        # If this widget's class is not in the dictionary, add it
        if widget.__class__ not in self.widgetDict:
            self.widgetDict[widget.__class__] = {}

        # Add the widget to the appropriate class dictionary
        self.widgetDict[widget.__class__][widget.get_id()] = widget

    def add_new_board_widget(self):
        new_board = ChessBoardWidget()
        self.layout.addWidget(new_board)
        self.add_widget_to_dict(new_board)  # add the new board to the dict

    def add_new_engine_widget(self):
        new_engine = ChessEngineWidget(self)
        self.layout.addWidget(new_engine)
        self.add_widget_to_dict(new_engine)  # add the new engine to the dict
