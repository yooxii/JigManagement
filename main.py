import os
import sys


sys.path.append(os.path.join(os.path.dirname(__file__), "."))
from gui.startWin import QApplication, StartWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartWindow()
    window.show()
    sys.exit(app.exec())
