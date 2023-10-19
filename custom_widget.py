from uuid import uuid4

from PyQt6.QtWidgets import QWidget


class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.uuid = str(uuid4())
