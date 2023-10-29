from PyQt6.QtWidgets import QMainWindow, QApplication, QPushButton, QGridLayout, QLabel, QWidget
from PyQt6.QtCore import Qt

from layout_wizard import LayoutWizard

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Define a QWidget as the central widget of the main window
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Define a QGridLayout for your central widget
        self.layout = QGridLayout(central_widget)

        # Add QPushButton instances into the grid layout
        for i in range(2):
            for j in range(3):
                button = QPushButton(f"Button {i+1}-{j+1}")
                self.layout.addWidget(button, i, j)

        # Add QLabel into the grid layout
        label = QLabel("Label")
        self.layout.addWidget(label, 2, 0, 1, 2)

        # Add QPushButton that opens a LayoutWizard
        self.open_layout_wizard_button = QPushButton("Open LayoutWizard")
        self.open_layout_wizard_button.clicked.connect(self.open_layout_wizard)
        self.layout.addWidget(self.open_layout_wizard_button, 2, 2)
        self.layout_wizard = LayoutWizard(self)

    def open_layout_wizard(self):
        self.layout_wizard.setWindowTitle("Layout Wizard")
        self.layout_wizard.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.layout_wizard.show()


def main():
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    return app.exec()


if __name__ == "__main__":
    main()