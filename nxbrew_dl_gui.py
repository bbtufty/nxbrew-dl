import sys

from PySide6.QtWidgets import QApplication

from nxbrew_dl import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
