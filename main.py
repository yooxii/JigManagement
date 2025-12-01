import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from gui.mainWin import QApplication, MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
