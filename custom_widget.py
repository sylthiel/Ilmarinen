from uuid import uuid4

from PyQt6.QtWidgets import QWidget


class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.id = uuid4()

    def get_id(self):
        return str(self.id)
