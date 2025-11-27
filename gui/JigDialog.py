import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QDateEdit,
    QTextEdit,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtSql import QSqlRecord
from custom_utils.PydanticFormWidget import PydanticFormWidget, py_date

from Model import Jig

# 配置日志
logger = logging.getLogger(__name__)


class JigDialog(QDialog):
    def __init__(self, parent=None, proxy_model=None, proxy_row_index=None, datas=None):
        super().__init__(parent)
        logger.info("初始化JigDialog对话框")
        self.setWindowTitle("添加治具")
        self.setBaseSize(400, 300)
        # self.setWindowModality(Qt.ApplicationModal)

        self.mainlayout = QVBoxLayout()
        self.setLayout(self.mainlayout)

        self.form = PydanticFormWidget(
            Jig, parent=self, proxy_model=proxy_model, proxy_row_index=proxy_row_index
        )
        self.mainlayout.addWidget(self.form)
