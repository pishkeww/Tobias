import sys
from PyQt5.QtWidgets import QApplication
from app.gui.main_window import mainwindow
from app.gui.style import dark_stylesheet


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(dark_stylesheet)
    window = mainwindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
