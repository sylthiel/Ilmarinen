from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton, QMenuBar, QMenu, QInputDialog
from PyQt6.QtGui import QAction
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Customizable Workspace")
        self.setMinimumSize(1024, 768)

        self.mainWidget = QWidget(self)
        self.setCentralWidget(self.mainWidget)

        self.layout = QGridLayout(self.mainWidget)

        self.menuBar = QMenuBar(self)
        self.setMenuBar(self.menuBar)

        self.widgetMenu = QMenu("Widget", self)
        self.menuBar.addMenu(self.widgetMenu)

        self.addWidgetAction = QAction("Add Widget", self)
        self.addWidgetAction.triggered.connect(self.add_widget)
        self.widgetMenu.addAction(self.addWidgetAction)

    def add_widget(self):
        row, okRow = QInputDialog.getInt(self, 'Row Input', 'Row:')
        col, okCol = QInputDialog.getInt(self, 'Column Input', 'Column:')
        if okRow and okCol:
            self.layout.addWidget(QPushButton("Button"), row, col)

app = QApplication([])
window = MainWindow()
window.show()
app.exec()