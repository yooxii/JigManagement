# test_layouts.py
import sys
import os
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pydantic import BaseModel, Field
from enum import Enum
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from custom_utils.PydanticFormWidget import PydanticFormWidget, py_date

from Model import Jig


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        central = QWidget()
        layout = QVBoxLayout()

        form2 = PydanticFormWidget(
            Jig,
            layout_mode="grid",
            buttons=[{"name": "submit", "text": "提交"}],
        )

        layout.addWidget(form2)

        btn = QPushButton("验证第一个表单")
        btn.clicked.connect(lambda: print(form2.validate_and_get_model()))
        layout.addWidget(btn)

        central.setLayout(layout)
        self.setCentralWidget(central)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    app.exec()
