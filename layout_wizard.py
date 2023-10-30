from typing import Optional

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


class LayoutWizard(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.index_to_widget = {}
        self.target_layout = self.parent().layout()
        assert self.target_layout
        self.wizard_layout = self.target_layout.__class__(self)
        self.refresh_layout_dict()
        self.populate_wizard_layout()
        if self.wizard_layout.__class__ == QGridLayout:
            for i in range(parent.layout.rowCount()):
                for j in range(parent.layout.columnCount()):
                    self.wizard_layout.addWidget(LayoutWizardButton(
                        text='Row %d Col %d' % (i + 1, j + 1),
                        parent=self,
                        row=i,
                        col=j,
                        number=i * parent.layout.columnCount() + j
                    ), i, j)

    def populate_wizard_layout(self):
        if isinstance(self.wizard_layout, QGridLayout):
            assert isinstance(self.target_layout, QGridLayout)
            # TODO this is not going work in the actual implementation
            # rowCount() does not get reduced even when you remove all widgets from the layout
            for i in range(self.target_layout.rowCount()):
                for j in range(self.target_layout.columnCount()):
                    item = self.wizard_layout.itemAtPosition(i, j)
                    if item is not None:
                        self.wizard_layout.removeItem(item)
            for i in range(self.target_layout.rowCount()):
                for j in range(self.target_layout.columnCount()):
                    self.wizard_layout.addWidget(LayoutWizardButton(
                        text='Row %d Col %d' % (i + 1, j + 1),
                        parent=self,
                        row=i,
                        col=j,
                        number=i * self.target_layout.columnCount() + j
                    ), i, j)

    def refresh_layout_dict(self):
        self.index_to_widget = {}
        for index in range(self.target_layout.count()):
            item = self.target_layout.itemAt(index)
            if item.__class__ == QtWidgets.QWidgetItem:
                self.index_to_widget[index] = item.widget()

    def move_widget_on_grid(self,
                    existing_widget_index: Optional[tuple[int, int]] = None,
                    target_coordinates: tuple[int, int] = (-1, -1),
                    swap: bool = False,
                    ):
        row, col = target_coordinates[0], target_coordinates[1]
        if existing_widget_index is not None:
            if not swap:
                old_widget = self.target_layout.itemAtPosition(row, col)
                placeholder_widget = QWidget()
                x, y = existing_widget_index[0], existing_widget_index[1]
                self.target_layout.addWidget(placeholder_widget, x, y)
                self.target_layout.addWidget(self.target_layout.itemAtPosition(x, y), row, col)
                self.target_layout.removeWidget(old_widget)


class PlaceWidgetDialog(QDialog):
    def __init__(self, parent: LayoutWizard,
                 active_widgets=None, widgets_to_be_removed=None, widget_classes=None, row=None, col=None):
        self.wizard = self.parent()
        self.examples = None
        self.row = row
        self.col = col
        if widget_classes is not None:
            self.examples = {cls: cls(*param) for cls, param in widget_classes.items()}
            self.class_name_to_class = {str(cls): cls for cls in widget_classes}
        super().__init__(parent)
        # Create a layout for this dialog
        self.layout = QGridLayout(self)
        self.target_layout = self.parent().parent_layout
        self.active_widgets = active_widgets
        self.active_widgets_box = QtWidgets.QListWidget(self)
        self.layout.addWidget(self.active_widgets_box, 0, 0)
        self.widgets_to_be_removed_box = QtWidgets.QListWidget(self)
        self.layout.addWidget(self.widgets_to_be_removed_box, 0, 1)
        self.widget_classes_box = QtWidgets.QListWidget(self)
        self.layout.addWidget(self.widget_classes_box, 0, 2)
        self.widget_classes_box.itemClicked.connect(self.on_widget_class_selected)
        self.active_widgets_box.itemClicked.connect(self.on_active_widget_selected)
        self.active_widgets_box.itemDoubleClicked.connect(
            lambda item: self.place_existing_widget(int(item.text()))
        )
        self.widgets_to_be_removed = widgets_to_be_removed or []
        self.widget_classes = widget_classes
        self.setup_boxes()

        # Empty space for pixmap
        self.pixmap_placeholder = QLabel(self)
        self.layout.addWidget(self.pixmap_placeholder, 0, 3)

    def setup_boxes(self):
        self.active_widgets_box.addItems([str(widget) for widget in (self.active_widgets or [])])
        self.widgets_to_be_removed_box.addItems([str(widget) for widget in (self.widgets_to_be_removed or [])])
        self.widget_classes_box.addItems([str(widget) for widget in (self.widget_classes or [])])

    def update_pixmap(self, widget):
        # Grab the widget's current rendering into a QPixmap
        pixmap = widget.grab()
        self.pixmap_placeholder.setPixmap(pixmap)

    def on_active_widget_selected(self, item):
        widget_name = item.text()
        selected_widget = self.active_widgets[int(widget_name)]
        self.update_pixmap(selected_widget)

    def place_existing_widget(self, replace_with_index):
        # add handling for swap instead of delete previous inhabitant
        self.wizard.move_widget(
            existing_widget_index=replace_with_index,
            target_coordinates=(self.row, self.col),
            swap=False
        )

    def on_widget_class_selected(self, item):
        widget_class_name = item.text()
        widget_class = self.class_name_to_class.get(widget_class_name)
        try:
            selected_widget = self.examples[widget_class]
        except KeyError:
            QMessageBox.warning(self, "KeyError", f"No class named '{widget_class_name}' found in examples.")
            return
        self.update_pixmap(selected_widget)


class LayoutWizardButton(QPushButton):
    def __init__(self, parent: LayoutWizard, text="", row=-1, col=-1, number=-1, ):
        super().__init__(text=text, parent=parent)
        self.clicked.connect(self.widget_menu)
        self.row = row
        self.col = col
        self.number = number

    def widget_menu(self):
        layout_wizard = self.parent()
        layout_wizard.widget_dialog = PlaceWidgetDialog(
            parent=self.parent(),
            active_widgets={k: v for k, v in layout_wizard.index_to_widget.items() if k != self.number},
            widget_classes={QPushButton: ['A']},
            position=self.number
        )
        layout_wizard.widget_dialog.show()
