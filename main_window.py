from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtWidgets import QWidget, QMessageBox, QHBoxLayout, QPushButton, QSplitter, QVBoxLayout, QGridLayout, \
    QToolBar

from Ilmarinen.chess_board_widget import ChessBoardWidget
from Ilmarinen.chess_engine_widget import ChessEngineWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        screen = QCoreApplication.instance().primaryScreen()  # get the primary screen
        screen_size = screen.availableSize()  # get the available size
        self.resize(screen_size * 0.9)  # set the window size to 90% of the available size
        self.setWindowTitle("Work desk")

        self.add_widget_message_box = QMessageBox(self)
        self.add_widget_message_box.setText("What type of widget do you want to add?")
        self.board_button = self.add_widget_message_box.addButton("Board", QMessageBox.ButtonRole.AcceptRole)
        self.engine_button = self.add_widget_message_box.addButton("Engine", QMessageBox.ButtonRole.AcceptRole)

        self.widgetDict = {}

        self.grid_layout = QGridLayout()

        self.initial_widget = ChessBoardWidget()
        # self.initial_widget.setFixedSize(400, 400)
        self.grid_layout.addWidget(self.initial_widget, 0, 0)
        self.add_widget_to_dict(self.initial_widget)

        self.tool_bar = QToolBar()
        self.add_button = QPushButton('+')
        self.add_button.clicked.connect(self.add_widget_option)
        self.tool_bar.addWidget(self.add_button)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addWidget(self.tool_bar)
        self.setLayout(self.main_layout)

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

    # def add_new_board_widget(self):
    #     new_board = ChessBoardWidget()
    #     # new_board.setFixedSize(400, 400)
    #     self.grid_layout.addWidget(new_board)
    #     self.add_widget_to_dict(new_board)  # add the new board to the dict
    #
    # def add_new_engine_widget(self):
    #     new_engine = ChessEngineWidget(self)
    #     # new_engine.setFixedSize(400, 400)
    #     self.grid_layout.addWidget(new_engine)
    #     self.add_widget_to_dict(new_engine)  # add the new engine to the dict
    def add_new_board_widget(self):
        new_board = ChessBoardWidget()
        position = self.get_next_position()
        self.grid_layout.addWidget(new_board, position[0], position[1])
        self.add_widget_to_dict(new_board)

    def add_new_engine_widget(self):
        new_engine = ChessEngineWidget(self)
        position = self.get_next_position()
        self.grid_layout.addWidget(new_engine, position[0], position[1])
        self.add_widget_to_dict(new_engine)

    def get_next_position(self):
        next_row = self.grid_layout.rowCount()
        next_col = 0
        if self.grid_layout.itemAtPosition(next_row - 1, 1):
            # Both column 0 and column 1 in the last row have widgets, start a new row
            next_col = 0
        elif self.grid_layout.itemAtPosition(next_row - 1, 0):
            # Only column 0 in the last row has a widget, use column 1 in the last row
            next_row -= 1
            next_col = 1
        return next_row, next_col

