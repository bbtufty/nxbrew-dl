import sys
from importlib.metadata import version

from PySide6.QtWidgets import QApplication

from .gui import MainWindow


def run_CartDL_gui():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()

# Get the version
__version__ = version(__name__)

__all__ = [
    "MainWindow",
    "run_CartDL_gui",
]

if __name__ == "__main__":
    run_CartDL_gui()
