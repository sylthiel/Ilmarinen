from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout, QPushButton, QHBoxLayout, QVBoxLayout, QLabel,
                             QFileDialog, QMessageBox, QTextEdit, QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from itertools import product
import chess
import chess.engine
from uuid import uuid4
from multiprocessing import Process, Queue
import asyncio
from qasync import QEventLoop, asyncSlot

class GameState:
    def __init__(self, fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
        # self.fen = fen
        self.board = chess.Board(fen)

    def get_legal_moves(self):
        return self.board.legal_moves


class AnalysisThread(QThread):
    analysis_done = pyqtSignal(object)
    stop_signal = pyqtSignal()

    def __init__(self, engine, board):
        super().__init__()
        self.engine = engine
        self.board = board
        self.stop_signal.connect(self.stop)
        self.running = True

    def run(self):
        while self.running:
            # Adjust the multipv parameter to the number of lines to output
            info = self.engine.analyse(self.board, chess.engine.Limit(time=1.0), multipv=self.num_lines)
            self.analysis_done.emit(info)
            QThread.msleep(500)  # Optional: put some interval between updates

    def stop(self):
        self.running = False


class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id = uuid4()

    def get_id(self):
        return str(self.id)


class ChessBoardWidget(CustomWidget):
    def __init__(self):
        super().__init__()
        self.board = [[None] * 8 for _ in range(8)]  # Nested list to store all buttons
        self.game_state = None
        self.initUI()
        self.selected_button = None


    def buttonClicked(self):
        sender = self.sender()  # Get the button that was clicked
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
                sender.setText(piece)
                self.game_state.board.push(move)
                self.selected_button.setText("")
                self.selected_button = None
            else:
                print(f"{self.selected_button.square_name} to {sender.square_name} is an illegal move ")
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
            if (row + col) % 2 == 0:
                button.setStyleSheet("background-color: white; color: black; border:1px solid black;")
            else:
                button.setStyleSheet("background-color: lightblue; color: black; border:1px solid black;")
            button.setFixedSize(50, 50)  # Make buttons square
            button.setFont(font)  # Set the font
            grid.addWidget(button, row, col)
            self.board[row][col] = button
            button.square_name = chr(ord('a') + col) + str(8 - row)
            button.clicked.connect(self.buttonClicked)

        reset_button = QPushButton("Reset Board")
        reset_button.clicked.connect(self.resetBoard)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(reset_button)
        layout.addStretch()

        grid.addLayout(layout, 8, 0, 1, 8)

        self.setWindowTitle("Chess Board")
        self.resetBoard()
        self.getBoardState()

    def getBoardState(self):
        fen_arr = []  # Initialize an empty list to store the FEN strings
        for row in range(8):
            empty_spaces = 0
            for col in range(8):
                button = self.board[row][col]  # Get the button at the (row, col) position
                piece = button.text()  # Get the text of the button, which represents the piece
                if piece:  # If there is a piece on the button
                    if empty_spaces > 0:
                        fen_arr.append(str(empty_spaces))
                        empty_spaces = 0
                    fen_arr.append(self.pieceToFEN(piece))
                else:
                    empty_spaces += 1
            if empty_spaces > 0:
                fen_arr.append(str(empty_spaces))
            fen_arr.append("/")  # insert a line break for each row
        fen_string = "".join(fen_arr[:-1]) # Convert the list to a string, but excluding the last "/"
        print(fen_string)
        return fen_string  # Return the FEN string

    def pieceToFEN(self, piece):
        piece_map = {
            "♜": "r", "♞": "n", "♝": "b", "♛": "q", "♚": "k", "♟": "p",
            "♖": "R", "♘": "N", "♗": "B", "♕": "Q", "♔": "K", "♙": "P"
        }
        return piece_map.get(piece, "")

    def resetBoard(self):
        piece_map = {
            "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟",
            "r": "♖", "n": "♘", "b": "♗", "q": "♕", "k": "♔", "p": "♙"
        }
        self.game_state = GameState()
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


class ChessEngineWidget(CustomWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a QVBoxLayout instance
        self.layout = QVBoxLayout(self)
        self.link_board_button = QPushButton('Link board')
        self.link_board_button.clicked.connect(self.link_board)
        # Create QPushButton for browsing file
        self.browse_button = QPushButton('Browse UCI engine...')
        self.browse_button.clicked.connect(self.browse_file)
        self.best_moves_text = QTextEdit()
        self.analysis_text = QTextEdit()
        # Create QPushButton for adding more best lines
        self.add_line_button = QPushButton("More lines", self)
        self.add_line_button.clicked.connect(self.add_line)
        self.num_lines = 1
        # Create QPushButton for removing best lines
        self.remove_line_button = QPushButton("Less lines", self)
        self.remove_line_button.clicked.connect(self.remove_line)
        # Create QLabel for showing the selected file
        self.file_label = QLabel('No file selected.')
        self.analysis_update_timer = QTimer()
        self.analysis_update_timer.timeout.connect(self.update_results)
        # Create QPushButton for starting analysis
        self.analysis_button = QPushButton('Start analysis')
        self.analysis_button.clicked.connect(self.toggle_analysis)
        self.engine = None
        self.analysis_result = None
        # Create QTextEdit for showing the analysis results
        self.results_text = QTextEdit()
        self.should_stop_analysis = False

        # Add all widgets to the layout
        self.layout.addWidget(self.browse_button)
        self.layout.addWidget(self.file_label)
        self.layout.addWidget(self.analysis_button)
        self.layout.addWidget(self.results_text)
        self.layout.addWidget(self.link_board_button)
        self.layout.addWidget(self.analysis_text)
        self.layout.addWidget(self.best_moves_text)
        self.layout.addWidget(self.add_line_button)
        self.layout.addWidget(self.remove_line_button)
        # Set layout
        self.setLayout(self.layout)

        # Initially, no engine is selected
        self.engine_path = None
        self.analysis_button.setEnabled(False)

    @asyncSlot()
    async def start_analysis_async(self):
        print("Start analysis async")
        self.should_stop_analysis = False
        try:
            transport, engine = await chess.engine.popen_uci(self.engine_path)
            self.board = self.linked_board_widget.game_state.board
            starting_analysis_board = self.board.fen()
            with await engine.analysis(self.board, multipv=self.num_lines) as analysis:
                i = 0
                async for info in analysis:
                    # Check if board state has changed
                    print(self.linked_board_widget.game_state.board.fen())
                    print(self.board.fen())
                    if starting_analysis_board != self.linked_board_widget.game_state.board.fen():
                        print("board has changed")
                        # If it has, stop the analysis
                        self.should_stop_analysis = True
                        # self.board = self.linked_board_widget.game_state.board
                    if self.should_stop_analysis:
                        break
                    score, pv = info.get("score"), info.get("pv")
                    if score and pv:
                        self.update_results(info)
                    i += 1
                    if i > 1e5:
                        break
            await engine.quit()
        except Exception as e:
            print(f"Error in start_analysis_async: {str(e)}")

        # If the board state changed and analysis was stopped, restart with the new board state
        if self.should_stop_analysis and starting_analysis_board != self.linked_board_widget.game_state.board.fen():
            self.board = self.linked_board_widget.game_state.board
            await self.start_analysis_async()

    def toggle_analysis(self):
        print("Toggle analysis")  # Start of the method debug output
        try:
            if not self.engine_path:
                self.file_label.setText('No engine file selected.')
                return

            if self.analysis_button.text() == "Start analysis":
                self.analysis_button.setText("Stop analysis")
                if not hasattr(self, 'linked_board_widget'):
                    QMessageBox.critical(self, "Error", "No board linked to this engine", QMessageBox.Ok)
                    return

                asyncio.run(self.start_analysis_async())  # Debug message surrounding the call in question
                print("Start analysis call completed")  # Completion of the call debug output
            else:
                self.analysis_button.setText("Start analysis")
                self.should_stop_analysis = True
        except Exception as e:
            pass
            # print(f"Error in toggle_analysis: {str(e)}")  # If any exceptions occur, print them

    def parse_info(self, info):
        try:
            pv = [str(move) for move in info["pv"]]
            lines = " ".join(map(str, pv))
            # get values from info or default to None if they are not existent
            depth, seldepth = info.get("depth", None), info.get("seldepth", None)
            score = info.get("score", None)
            multipv = info.get("multipv", None)
            return {"depth": f"{depth}/{seldepth}", "score": score, "lines": lines, "multipv": multipv}
        except Exception as e:
            print(str(e))

    def update_results(self, result):
        parsed_result = self.parse_info(result)
        analysis = f"Evaluation: {parsed_result.get('score')} Depth: {parsed_result.get('depth')}"
        lines = parsed_result.get("lines")
        multipv = parsed_result.get("multipv", 1)  # if multipv doesn't exist we default to 1 (first line)

        self.analysis_text.setText(analysis)

        # Here we check if we already have the mv line already in our QTextEdit
        # If we have we just update that line, if not we append a new line
        current_best_moves = self.best_moves_text.toPlainText().split('\n')
        if multipv <= len(current_best_moves):
            current_best_moves[
                multipv - 1] = f"{multipv}. {lines}"  # Remember that multipv is 1-indexed but Python lists are 0-indexed
        else:
            current_best_moves.append(f"{multipv}. {lines}")
        self.best_moves_text.setText("\n".join(current_best_moves))

    def analysis_finished(self):
        self.results_text.append("\nAnalysis finished!")
        self.analysis_button.setText('Start analysis')

    def add_line(self):
        self.num_lines += 1

    def remove_line(self):
        if self.num_lines > 1:
            self.num_lines -= 1

    def browse_file(self):
        file_dialog = QFileDialog()
        filename, _ = file_dialog.getOpenFileName()
        if filename:
            # Successfully selected a file.
            # Update the label and keep track of the file's path
            self.file_label.setText(f'Selected engine: {filename}')
            # print(filename)
            self.engine_path = filename
            self.analysis_button.setEnabled(True)

    def start_analysis(self):
        print("Entered start_analysis")
        if self.engine_path:
            print("Engine path is:")
            print(self.engine_path)
            # Check if a board has been linked to the engine
            if not hasattr(self, 'linked_board_widget'):
                QMessageBox.critical(self, "Error", "No board linked to this engine", QMessageBox.Ok)
                return

            # Prevent engine re-selection during analysis
            self.browse_button.setEnabled(False)
            self.analysis_button.setEnabled(False)

            # Set up the engine
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            print(self.engine)
            try:
                # Start async engine analysis
                self.board = self.linked_board_widget.game_state.board  # You will get board from main app
                self.info = self.engine.analyse(self.board, chess.engine.Limit(time=1.0))

                # Update the QTextEdit with analysis results
                self.results_text.setText(str(self.info))
            except Exception as e:
                print('Error during analysis:', str(e))
            finally:
                self.browse_button.setEnabled(True)
                self.analysis_button.setEnabled(True)
        else:
            # No file has been selected
            self.file_label.setText('No engine file selected.')
    def link_board(self):
        items, ok = QInputDialog.getItem(
            self, "Select target board", "Please select the board to link this engine to",
            self.available_boards(), editable=False)
        # print(items, ok)
        if ok and items:
            item_uuid = items.split(":")[-1]  # assuming uuid at the end
            linked_board_widget = self.get_main_window().widgetDict[ChessBoardWidget].get(item_uuid)
            if linked_board_widget:
                self.linked_board_widget = linked_board_widget
                self.link_board_button.setText("Linked to Board " + str(items))
            else:
                QMessageBox.critical(self, "Error",
                                     "Failed to link the selected board",
                                     QMessageBox.Ok)

    def get_main_window(self):
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, MainWindow):
                return parent
            parent = parent.parent()
        return None  # Can't find MainWindow instance, something went wrong

    def available_boards(self):
        return list(self.get_main_window().widgetDict[ChessBoardWidget].keys())

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
        new_engine = ChessEngineWidget()
        self.layout.addWidget(new_engine)
        self.add_widget_to_dict(new_engine)  # add the new engine to the dict


if __name__ == "__main__":
    app = QApplication([])
    mainWindow = MainWindow()
    mainWindow.show()
    #async magic that fixes the backend process stopping UI interaction
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    with loop:
        loop.run_forever()
    app.exec()

