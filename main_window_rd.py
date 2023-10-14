from PyQt6.QtGui import QPainter, QPaintEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QStyleOption, QStyle


class Gridling(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)

    def paintEvent(self, event: QPaintEvent):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)
        # super().paintEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gridling Demo")
        self.setGeometry(200, 200, 400, 300)

        widget = QWidget()
        self.setCentralWidget(widget)

        grid = QGridLayout()
        widget.setLayout(grid)

        qwidget = QWidget()
        gridling = Gridling()

        qwidget.setStyleSheet("background-color: red")
        gridling.setStyleSheet("background-color: red")

        grid.addWidget(qwidget, 0, 0)
        grid.addWidget(gridling, 0, 1)

app = QApplication([])
app.setStyle("Fusion")
window = MainWindow()
window.show()
app.exec()