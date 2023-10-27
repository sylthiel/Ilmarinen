import asyncio

import chess
import chess.engine
from PyQt6.QtCore import QTimer, QSizeF, QSize
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit, QLabel, QMessageBox, QInputDialog, QFileDialog, \
    QGridLayout, QSizePolicy, QHBoxLayout
from qasync import asyncSlot

from Ilmarinen.chess_board_widget import ChessBoardWithControls
from Ilmarinen.custom_widget import CustomWidget


class CustomTextEdit(QTextEdit):
    def sizeHint(self):
        return QSize(30, 100)

class ChessEngineWidget(CustomWidget):
    def __init__(self, main_window, hub):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.hub = hub
        self.main_window = main_window

        self.layout = QGridLayout(self)
        self.init_buttons()
        self.best_moves_text = QTextEdit()
        self.analysis_text = QLabel()
        self.num_lines = 1
        self.file_label = QLabel('No file selected.')
        self.engine = None
        self.analysis_result = None
        self.should_stop_analysis = asyncio.Event()
        self.analysis_running = asyncio.Event()
        self.layout.addWidget(self.analysis_text, 1, 0, 1, 1)
        self.layout.addWidget(self.best_moves_text, 2, 0, 1, 1)


        # Set layout
        self.setLayout(self.layout)

        # Initially, no engine is selected
        self.engine_path = None
        self.analysis_button.setEnabled(False)
        self.deploy_default_engine()

    def init_buttons(self):
        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.browse_file)
        self.remove_line_button = QPushButton("-", self)
        self.remove_line_button.clicked.connect(self.remove_line)
        self.analysis_button = QPushButton('Start')
        self.analysis_button.clicked.connect(self.toggle_analysis)
        self.add_line_button = QPushButton("+", self)
        self.add_line_button.clicked.connect(self.add_line)
        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout, 0, 0)
        self.button_layout.addWidget(self.browse_button)
        self.button_layout.addWidget(self.analysis_button)
        self.button_layout.addWidget(self.add_line_button)
        self.button_layout.addWidget(self.remove_line_button)
    @asyncSlot()
    async def board_changed(self, **kwargs):
        # No need to call asyncio.run
        self.linked_board_widget = kwargs.get('board')
        if self.analysis_running.is_set():
            self.should_stop_analysis.set()
            while self.analysis_running.is_set():
                await asyncio.sleep(0.1)  # microseconds to wait, you can adjust this as needed
            # asyncio.create_task(self.start_analysis_async())  # start the analysis
            await self.start_analysis_async()

    @asyncSlot()
    async def start_analysis_async(self):
        # print("Start analysis async")
        self.should_stop_analysis = asyncio.Event()
        self.analysis_running.set()
        try:
            try:
                transport, engine = await chess.engine.popen_uci(self.engine_path)
            except Exception as e:
                print(f"Failed to load engine. {str(e)}")
            number_of_lines = self.num_lines
            with await engine.analysis(self.linked_board_widget, multipv=self.num_lines) as analysis:
                i = 0
                async for info in analysis:
                    if number_of_lines != self.num_lines:
                        self.should_stop_analysis.set()
                    if self.should_stop_analysis.is_set():
                        break
                    score, pv = info.get("score"), info.get("pv")
                    if score and pv:
                        self.update_results(info)
                    i += 1
                    if i > 1e5:
                        break
            await engine.quit()
            if number_of_lines != self.num_lines:
                await self.start_analysis_async()
        except Exception as e:
            print(f"Error in start_analysis_async: {str(e)}")
        finally:
            self.analysis_running.clear()

    @asyncSlot()
    async def toggle_analysis(self):
        try:
            if not self.engine_path:
                return

            if self.analysis_button.text() == "Start":
                self.analysis_button.setText("Stop")
                if not hasattr(self, 'linked_board_widget'):
                    QMessageBox.critical(self, "Error", "No board linked to this engine", QMessageBox.Ok)
                    return
                await self.start_analysis_async()
            else:
                self.analysis_button.setText("Start")
                self.should_stop_analysis.set()
        except Exception as e:
            print(f"Error in toggle_analysis: {str(e)}")  # If any exceptions occur, print them

    def board_created_event(self, **kwargs):
        self.linked_board_widget = kwargs.get('board').game_state.board

    def parse_info(self, info):
        try:
            # Create a copy of the board to safely simulate the moves
            board = self.linked_board_widget.copy()

            # Parse each move into SAN notation, simulating the moves on the board copy
            pv = info["pv"]
            san_moves = []

            for move_num, move in enumerate(pv, start=1):
                san_move = board.san(move)
                fullmove_number = board.fullmove_number
                if (move_num == 1) and (board.turn == chess.BLACK):
                    san_move = f"{fullmove_number}...{san_move}"
                elif (board.turn == chess.BLACK) and (move_num != 1):
                    san_move = f"{san_move}"
                else:
                    san_move = f"{fullmove_number}.{san_move}"

                san_moves.append(san_move)
                # Apply the move on a copy of the board, not the original
                board.push(move)

            lines = " ".join(san_moves)
            depth, seldepth = info.get("depth", None), info.get("seldepth", None)
            score = info.get("score", None)
            multipv = info.get("multipv", None)
            return {"depth": f"{depth}/{seldepth}", "score": score, "lines": lines, "multipv": multipv}
        except Exception as e:
            print(str(e))

    def deploy_default_engine(self):
        self.engine_path = 'stockfish'
        self.analysis_button.setEnabled(True)
    def parse_evaluation(self, score):
        centipawn_value = int(str(score))
        printable = round(centipawn_value / 100, 2)
        if -25 < centipawn_value < 25:
            return f"= ({printable})"
        elif 25 <= centipawn_value < 75:
            return f"+= ({printable})"
        elif 75 <= centipawn_value < 150:
            return f"± ({printable})"
        elif centipawn_value >= 150:
            return f"+- ({printable})"
        elif -25 >= centipawn_value > -75:
            return f"-= ({printable})"
        elif -75 >= centipawn_value > -150:
            return f"∓ ({printable})"
        else:
            return f"-+ ({printable})"

    def update_results(self, result):
        parsed_result = self.parse_info(result)
        analysis = f"Evaluation: {self.parse_evaluation(parsed_result.get('score').white())} Depth: {parsed_result.get('depth')}"
        lines = parsed_result.get("lines")
        multipv = parsed_result.get("multipv", 1)  # if multipv doesn't exist we default to 1 (first line)

        if multipv == 1:
            self.analysis_text.setText(analysis)

        # Here we check if we already have the mv line already in our QTextEdit
        # If we have we just update that line, if not we append a new line
        current_best_moves = self.best_moves_text.toPlainText().split('\n')
        if multipv <= len(current_best_moves):
            current_best_moves[
                multipv - 1] = f" {multipv}. {self.parse_evaluation(parsed_result.get('score').white())} {lines}"
            # Remember that multipv is 1-indexed but Python lists are 0-indexed
        else:
            current_best_moves.append(f"{multipv}. {lines}")
        self.best_moves_text.setText("\n".join(current_best_moves))

    def analysis_finished(self):
        # self.results_text.append("\nAnalysis finished!")
        self.analysis_button.setText('Start')

    def add_line(self):
        self.num_lines += 1

    def remove_line(self):
        if self.num_lines > 1:
            self.num_lines -= 1
            current_best_moves = self.best_moves_text.toPlainText().split('\n')
            current_best_moves = current_best_moves[0:self.num_lines]
            self.best_moves_text.setText("\n".join(current_best_moves))

    def browse_file(self):
        file_dialog = QFileDialog()
        filename, _ = file_dialog.getOpenFileName()
        if filename:
            # Successfully selected a file.
            # Update the label and keep track of the file's path
            # print(filename)
            self.engine_path = filename
            self.analysis_button.setEnabled(True)


    def get_main_window(self):
        return self.main_window

    def available_boards(self):
        # print(f'Getting main window widget dict')
        # # print(f'{self.get_main_window().widgetDict}')
        # print(f'{self.get_main_window().widgetDict[ChessBoardWithControls].keys()}')
        return list(self.get_main_window().widgetDict[ChessBoardWithControls].keys())
