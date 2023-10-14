from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QGridLayout, QMenu, QMenuBar, \
    QMessageBox, QSizePolicy, QInputDialog, QDialogButtonBox, QSpinBox, QFormLayout, QDialog, QStyleOption, QStyle
from PyQt6.QtGui import QAction, QPen, QColor, QPainter, QPaintEvent
from PyQt6.QtCore import Qt, QPoint, QRect, QEvent, QTimer
# from Ilmarinen.chess_board_widget import ChessBoardWidget
from Ilmarinen.chess_board import ChessBoardWidget
class Gridling(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event: QPaintEvent):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)

class MultiInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = QFormLayout(self)
        self.row_spinbox = QSpinBox()
        self.row_spinbox.setRange(0, 100)
        self.row_spinbox.setValue(1)
        self.column_spinbox = QSpinBox()
        self.column_spinbox.setRange(0, 100)
        self.column_spinbox.setValue(1)
        self.replace_row_spinbox = QSpinBox()
        self.replace_row_spinbox.setRange(0, 100)
        self.replace_row_spinbox.setValue(1)
        self.replace_column_spinbox = QSpinBox()
        self.replace_column_spinbox.setRange(0, 100)
        self.replace_column_spinbox.setValue(1)

        self.form.addRow("Replace row:", self.replace_row_spinbox)
        self.form.addRow("Replace column:", self.replace_column_spinbox)
        self.form.addRow("Row size:", self.row_spinbox)
        self.form.addRow("Column size:", self.column_spinbox)
        self.buttons = QDialogButtonBox()
        self.buttons.setStandardButtons(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.form.addRow(self.buttons)

class OverlayWidget(QWidget):
    def __init__(self, parent, rows, columns):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.columns = rows
        self.rows = columns

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(0, 0, 0, 64), 1, Qt.PenStyle.DashLine))
        w = self.width() / self.columns
        h = self.height() / self.rows
        for i in range(self.columns + 1):
            painter.drawLine(QPoint(int(i * w), 0), QPoint(int(i * w), self.height()))
        for i in range(self.rows + 1):
            painter.drawLine(QPoint(0, int(i * h)), QPoint(self.width(), int(i * h)))


class MainWindow(QMainWindow):
    def __init__(self, rows, columns):
        super().__init__()
        self.setWindowTitle("Customizable Workspace")
        self.setMinimumSize(1000, 1000)
        self.mainWidget = Gridling()
        self.layout = QGridLayout(self.mainWidget)
        self.setCentralWidget(self.mainWidget)
        self.overlay = OverlayWidget(self.mainWidget, rows, columns)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.grid_rows, self.grid_columns = rows, columns

        self.tile_main_window(0, 0, self.grid_rows, self.grid_columns)
        self.create_menu_bar()


    def tile_main_window(self, start_row, start_col, end_row, end_col):
        print(f'Received tiling request from {start_row} {start_col} until {end_row} {end_col}')
        for row in range(start_row, end_row):
            self.layout.setRowStretch(row, 1)
            for col in range(start_col, end_col):
                self.layout.setColumnStretch(col, 1)
                widget = Gridling()
                # to add individual gridling visibility
                # if (row + col) % 2 == 0:
                #     widget.setStyleSheet("background-color: brown")
                # else:
                #     widget.setStyleSheet("background-color: beige")
                self.layout.addWidget(widget, row, col)

    def create_menu_bar(self):
        menubar = self.menuBar()
        widgetMenu = QMenu("Widgets", self)
        replaceAction = QAction("Replace widget", self)
        replaceAction.triggered.connect(lambda: self.replace_widget(ChessBoardWidget))
        widgetMenu.addAction(replaceAction)
        menubar.addMenu(widgetMenu)
        deleteAction = QAction("Delete widget", self)
        deleteAction.triggered.connect(lambda: self.replace_widget(Gridling))
        widgetMenu.addAction(deleteAction)
        resizeAction = QAction("Resize widget", self)
        resizeAction.triggered.connect(self.resize_widget)
        widgetMenu.addAction(resizeAction)

    def check_new_widget_space(self, row, col, h, w, previous_inhabitor=None):
        print(f"Received request to check space: {row} {col} to {row+h} {col+w}")
        if row+h > self.grid_rows or col+w > self.grid_columns:
            print("Biting off to much")
            return False
        for i in range(row, min(row + h, self.grid_rows)):
            for j in range(col, min(col + w, self.grid_columns)):

                try:
                    widget = self.layout.itemAtPosition(i, j).widget()
                except AttributeError:
                    widget = None
                # print(f"{i} {j} is {type(widget)}")
                if not self.is_gridling_or_none(widget):
                    if previous_inhabitor is not None and widget == previous_inhabitor:
                        continue
                    return False
        return True

    def is_gridling_or_none(self, obj):
        return obj is None or type(obj) is Gridling

    def replace_widget(self, widget_type, widget_parameters=None, rr=None, rc=None, h=None, w=None, widget=None):
        if any(val is None for val in (rr, rc, h, w)):
            coord_call = self.get_coords()
            if not coord_call:
                print('Coordinates not provided')
                return
            else:
                replace_row, replace_col, row, col = coord_call
        else:
            replace_row, replace_col, row, col = rr, rc, h, w
        print(f'Received parameters {replace_col} {replace_row} {row} {col}')
        # add code to check for widget intersection later
        try:
            old_widget = self.layout.itemAtPosition(replace_row, replace_col).widget()
        except AttributeError:
            old_widget = None
        if self.is_gridling_or_none(old_widget) or widget_type is not Gridling:
            # add widget_parameters handling later
            space_available = self.check_new_widget_space(replace_row, replace_col, row, col, widget)
            if not space_available:
                print(f"Unable to replace widget at {replace_row} {replace_col} with size {row} {col} due to"
                      f" non-Gridling widget in the way")
                return
            if widget_parameters is not None and widget is None:
                widget_to_insert = widget_type(widget_parameters)
            elif widget_parameters is None and widget is None:
                widget_to_insert = widget_type()
            else:
                widget_to_insert = widget
            widget_to_insert.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            for i in range(replace_row, min(replace_row + row, self.grid_rows)):
                for j in range(replace_col, min(replace_col + col, self.grid_columns)):
                    try:
                        old_widget = self.layout.itemAtPosition(i, j).widget()
                        if self.is_gridling_or_none(old_widget):
                            self.layout.removeWidget(old_widget)
                            old_widget.deleteLater()
                    except AttributeError:
                        continue
            self.layout.addWidget(widget_to_insert, replace_row, replace_col, row, col)
            self.show()
        elif type(old_widget) is not Gridling and widget_type is Gridling:
            self.layout.removeWidget(old_widget)
            old_widget.deleteLater()
            self.tile_main_window(replace_row, replace_col, replace_row + row, replace_col + col)

        elif type(old_widget) is not Gridling and widget_type is not Gridling:
            print(f"Unable to replace widget at {replace_row} {replace_col} with size {row} {col} due to"
                  f" non-Gridling widget in the way")


    def place_widget(self, widget_type=None, widget=None, row=None, col=None, h=None, w=None):
        if any(val is None for val in (row, col, h, w)):
            coord_call = self.get_coords()
            if not coord_call:
                print('Coordinates not provided')
                return
            else:
                replace_row, replace_col, row, col = coord_call
    def get_coords(self):
        dialog = MultiInputDialog(self)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            replace_row = dialog.replace_row_spinbox.value()
            replace_col = dialog.replace_column_spinbox.value()
            row = dialog.row_spinbox.value()
            col = dialog.column_spinbox.value()
            return replace_row, replace_col, row, col
        else:
            return None

    def resize_widget(self, rr=None, rc=None, h=None, w=None):
        if any(val is None for val in (rr, rc, h, w)):
            coord_call = self.get_coords()
            if not coord_call:
                print('Coordinates not provided')
                return
            else:
                replace_row, replace_col, row, col = coord_call
        else:
            replace_row, replace_col, row, col = rr, rc, h, w
        print(f'Entered resize_widget at {replace_row}x{replace_col} with size {row}x{col}')
        print(f'Received parameters {replace_col} {replace_row} {row} {col}')
        # add code to check for widget intersection later
        old_widget = self.layout.itemAtPosition(replace_row, replace_col).widget()
        if type(old_widget) is Gridling:
            print("Should not resize gridling")
            return
        else:
            if not self.check_new_widget_space(replace_row, replace_col, row, col, old_widget):
                print("Failed to resize, space not availble")
                return
            else:
                # old_widget.hide()
                self.layout.removeWidget(old_widget)
                self.tile_main_window(replace_row, replace_col, row, col)
                # self.layout.addWidget(old_widget, replace_row, replace_col, row, col)
                self.replace_widget(None, None, replace_row, replace_col, row, col, old_widget)
                # old_widget.show()

    def resizeEvent(self, event):
        self.overlay.resize(event.size())
        event.accept()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow(100, 100)
    window.show()
    window.replace_widget(ChessBoardWidget, None,1, 1, 40, 40)
    cbw = window.layout.itemAtPosition(1,1).widget()
    window.layout.removeWidget(cbw)
    for row in range(1, 72):
        for col in range(1, 72):
            try:
                old_widget = window.layout.itemAtPosition(row, col).widget()
                window.layout.removeWidget(old_widget)
                old_widget.deleteLater()
            except AttributeError:
                pass
    window.layout.addWidget(cbw, 1, 1, 70, 70)
    #
    # def performActions():
    #     window.resize_widget(1, 1, 70, 70)
    #     board_widget = window.layout.itemAtPosition(1, 1).widget()
    #     for row in board_widget.board:
    #         for square in row:
    #             QTest.mouseClick(square, Qt.MouseButton.LeftButton)
    #
    #
    # # Use QTimer.singleShot to schedule the performActions function to be
    # # called after the event loop starts running.
    # QTimer.singleShot(2000, performActions)
    app.exec()