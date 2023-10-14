from PyQt6 import QtWidgets, uic

class ChessWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('board_attempt1.ui', self)
        self.resize(800, 800)  # example starting size

    def resizeEvent(self, event):
        size = min(self.width(), self.height())
        self.square_frame.resize(size, size)
        super().resizeEvent(event)

app = QtWidgets.QApplication([])
window = ChessWidget()
window.show()
app.exec()