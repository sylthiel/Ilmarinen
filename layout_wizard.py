from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QDialog, QHBoxLayout, QGridLayout, QApplication, QLabel, \
    QMessageBox
from aenum import Enum

class Item(Enum):
    Existing = "Existing"
    ToBeDeleted = "ToBeDeleted"
    CreateNew = "CreateNew"

class PlaceWidgetDialog(QDialog):
    def __init__(self, parent=None,
                 active_widgets=None, widget_to_be_removed=None, widget_classes=None, position=-1):
        self.examples = None
        self.position = position
        if widget_classes is not None:
            self.examples = {cls: cls(*param) for cls, param in widget_classes.items()}
            self.class_name_to_class = {str(cls): cls for cls in widget_classes}
        super().__init__(parent)
        # Create a layout for this dialog
        self.layout = QGridLayout(self)
        print(active_widgets)
        self.active_widgets = active_widgets
        self.widgets_to_be_removed = widget_to_be_removed or []
        self.widget_classes = widget_classes
        # Active widgets selection box
        self.active_widgets_box = QtWidgets.QListWidget(self)
        self.active_widgets_box.addItems([str(widget) for widget in (active_widgets or [])])
        self.layout.addWidget(self.active_widgets_box, 0, 0)
        self.active_widgets_box.itemClicked.connect(self.on_active_widget_selected)
        self.active_widgets_box.itemDoubleClicked.connect(
            lambda item: self.place_widget(self.active_widgets[int(item.text())], int(item.text()), Item.Existing)
        )
        # Widgets to be removed selection box
        self.widgets_to_be_removed_box = QtWidgets.QListWidget(self)
        self.widgets_to_be_removed_box.addItems([str(widget) for widget in (widget_to_be_removed or [])])
        self.layout.addWidget(self.widgets_to_be_removed_box, 0, 1)

        # Widget classes selection box
        self.widget_classes_box = QtWidgets.QListWidget(self)
        self.widget_classes_box.addItems([str(widget) for widget in (widget_classes or [])])
        self.widget_classes_box.itemClicked.connect(self.on_widget_class_selected)
        self.layout.addWidget(self.widget_classes_box, 0, 2)

        # Empty space for pixmap
        self.pixmap_placeholder = QLabel(self)
        self.layout.addWidget(self.pixmap_placeholder, 0, 3)

    def update_pixmap(self, widget):
        # Grab the widget's current rendering into a QPixmap
        pixmap = widget.grab()
        self.pixmap_placeholder.setPixmap(pixmap)

    def on_active_widget_selected(self, item):
        widget_name = item.text()
        selected_widget = self.active_widgets[int(widget_name)]
        self.update_pixmap(selected_widget)

    def place_widget(self, item, selected_position, item_type):
        for i in range(self.parent().parent_layout.count()):
            print(f"{i} : {self.parent().parent_layout.itemAt(i).widget()}")
        if self.position != -1:
            if item_type == Item.Existing:
                current_item = self.parent().parent_layout.itemAt(self.position)
                if type(current_item) is QtWidgets.QWidgetItem:
                    current_item = current_item.widget()
                    self.widgets_to_be_removed.append(self.parent().parent_layout.takeAt(self.position))
                    print(self.widgets_to_be_removed)
                    self.parent().parent_layout.addWidget(
                        self.parent().parent_layout.takeAt(selected_position).widget()
                    )
                    for i in range(self.parent().parent_layout.count()):
                        print(f"{i} : {self.parent().parent_layout.itemAt(i).widget()}")

    def on_widget_class_selected(self, item):
        widget_class_name = item.text()
        widget_class = self.class_name_to_class.get(widget_class_name)
        try:
            selected_widget = self.examples[widget_class]
        except KeyError:
            QMessageBox.warning(self, "KeyError", f"No class named '{widget_class_name}' found in examples.")
            return
        self.update_pixmap(selected_widget)


class LayoutWizard(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.widgets_in_layout = {}
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.parent_layout = parent.layout
        try:
            print(parent.layout.__class__)
            self.layout = (parent.layout.__class__(self))
            print(self.layout)
        except AttributeError:
            self.layout = QHBoxLayout(self)

        for i in range(parent.layout.count()):
            item = parent.layout.itemAt(i)
            if item.__class__ == QtWidgets.QWidgetItem:
                self.widgets_in_layout[i] = item.widget()
        print(self.widgets_in_layout)
        if self.layout.__class__ == QGridLayout:
            for i in range(parent.layout.rowCount()):
                for j in range(parent.layout.columnCount()):
                    # Create a button and add it to the layout
                    self.layout.addWidget(LayoutWizardButton(
                        text='Row %d Col %d' % (i + 1, j + 1),
                        parent=self,
                        row=i,
                        col=j,
                        number=i*parent.layout.columnCount()+j
                    ), i, j)


class LayoutWizardButton(QPushButton):
    def __init__(self, text="", parent: LayoutWizard=None, row=-1, col=-1, number=-1):
        super().__init__(text, parent)
        self.clicked.connect(self.widget_menu)
        self.row = row
        self.col = col
        self.number = number
    def widget_menu(self):
        layout_wizard = self.parent()  # retrieve the QMainWindow instance
        layout_wizard.widget_dialog = PlaceWidgetDialog(
            parent=self.parent(),
            active_widgets={k: v for k, v in layout_wizard.widgets_in_layout.items() if k != self.number},
            widget_classes={QPushButton: ['A']},
            position=self.number
        )
        layout_wizard.widget_dialog.show()