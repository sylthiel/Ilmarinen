import asyncio

import chess
import chess.engine
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QTextEdit, QLabel, QMessageBox, QInputDialog, QFileDialog, \
    QGridLayout
from qasync import asyncSlot

from Ilmarinen.chess_board_widget import ChessBoardWithControls
from Ilmarinen.custom_widget import CustomWidget


class ChessEngineWidget(CustomWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.analysis_running = False
        # Create a QVBoxLayout instance
        self.layout = QGridLayout(self)
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
        self.layout.addWidget(self.browse_button, 0, 0)
        # self.layout.addWidget(self.file_label)
        self.layout.addWidget(self.analysis_button, 0, 1)
        # self.layout.addWidget(self.results_text, 1, 0)
        self.layout.addWidget(self.link_board_button, 0, 2)
        self.layout.addWidget(self.analysis_text, 2, 0, 1, 5)
        self.layout.addWidget(self.best_moves_text, 3, 0, 1, 5)
        self.layout.addWidget(self.add_line_button, 0, 3)
        self.layout.addWidget(self.remove_line_button, 0, 4)
        self.layout.setRowStretch(0, 1)
        self.layout.setRowStretch(1, 5)
        # self.layout.setRowStretch(2, 5)

        # Set layout
        self.setLayout(self.layout)

        # Initially, no engine is selected
        self.engine_path = None
        self.analysis_button.setEnabled(False)

    def board_changed(self, **kwargs):
        self.should_stop_analysis = True
        if self.analysis_running:
            asyncio.run(self.start_analysis_async())

    @asyncSlot()
    async def start_analysis_async(self):
        print("Start analysis async")
        self.should_stop_analysis = False
        self.analysis_running = True
        try:
            transport, engine = await chess.engine.popen_uci(self.engine_path)
            self.board = self.linked_board_widget.game_state.board
            number_of_lines = self.num_lines
            with await engine.analysis(self.board, multipv=self.num_lines) as analysis:
                i = 0
                async for info in analysis:
                    if number_of_lines != self.num_lines:
                        self.should_stop_analysis = True
                        self.analysis_running = False
                    if self.should_stop_analysis:
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

        if multipv == 1:
            self.analysis_text.setText(analysis)

        # Here we check if we already have the mv line already in our QTextEdit
        # If we have we just update that line, if not we append a new line
        current_best_moves = self.best_moves_text.toPlainText().split('\n')
        if multipv <= len(current_best_moves):
            current_best_moves[
                multipv - 1] = f"{parsed_result.get('score').white()} {multipv}. {lines}"  # Remember that multipv is 1-indexed but Python lists are 0-indexed
        else:
            current_best_moves.append(f"{multipv}. {lines}")
        self.best_moves_text.setText("\n".join(current_best_moves))

    def analysis_finished(self):
        # self.results_text.append("\nAnalysis finished!")
        self.analysis_button.setText('Start analysis')

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
            self.file_label.setText(f'Selected engine: {filename}')
            # print(filename)
            self.engine_path = filename
            self.analysis_button.setEnabled(True)

    def link_board(self):
        items, ok = QInputDialog.getItem(
            self, "Select target board", "Please select the board to link this engine to",
            self.available_boards(), editable=False)
        # print(items, ok)
        if ok and items:
            item_uuid = items.split(":")[-1]  # assuming uuid at the end
            linked_board_widget = self.get_main_window().widgetDict[ChessBoardWithControls].get(item_uuid)
            if linked_board_widget:
                self.linked_board_widget = linked_board_widget.chessboard
                self.link_board_button.setText("Linked to Board " + str(items))
            else:
                QMessageBox.critical(self, "Error",
                                     "Failed to link the selected board",
                                     QMessageBox.Ok)

    def get_main_window(self):
        return self.main_window

    def available_boards(self):
        # print(f'Getting main window widget dict')
        # # print(f'{self.get_main_window().widgetDict}')
        # print(f'{self.get_main_window().widgetDict[ChessBoardWithControls].keys()}')
        return list(self.get_main_window().widgetDict[ChessBoardWithControls].keys())
