import chess
from PyQt6.QtCore import QThread, pyqtSignal


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
