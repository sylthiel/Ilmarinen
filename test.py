import os
import site
from PyQt6 import QtWidgets

designer_path = os.path.join(site.getsitepackages()[1], "pyqt6_tools", "QtDesigner")

print(designer_path)