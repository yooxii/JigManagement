import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtSql import QSqlRecord
from custom_utils.PydanticFormWidget import PydanticFormWidget

from Model import JigDynamic

# 配置日志
logger = logging.getLogger(__name__)


class JigDialog(QDialog):
    JigUpdate = Signal(int)

    def __init__(self, parent=None, proxy_model=None, proxy_row_index=None, datas=None):
        super().__init__(parent)
        logger.info("初始化JigDialog对话框")
        self.setWindowTitle("添加治具")
        self.setBaseSize(400, 300)
        # self.setWindowModality(Qt.ApplicationModal)

        self.mainlayout = QVBoxLayout()
        self.setLayout(self.mainlayout)
        self.proxy_row_index = proxy_row_index

        self.form = PydanticFormWidget(
            JigDynamic,
            parent=self,
            proxy_model=proxy_model,
            proxy_row_index=proxy_row_index,
        )
        self.mainlayout.addWidget(self.form)

    def closeEvent(self, arg__1):
        self.JigUpdate.emit(self.proxy_row_index)
        logger.info("关闭JigDialog对话框")
        return super().closeEvent(arg__1)
