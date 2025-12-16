import sys
import os
import logging
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTableView,
    QHeaderView,
    QListView,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDateEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QAbstractItemView,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal
from PySide6.QtSql import QSqlQuery, QSqlDatabase
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from Model import JigDynamic, JigType, JigUseStatus
from custom_utils import Model2SQL
from custom_utils.ColorModel import ColoredSqlProxyModel


# 配置日志
logger = logging.getLogger(__name__)

# 获取正确的基础路径
if getattr(sys, "frozen", False):  # 检查是否为PyInstaller打包环境
    # 如果是打包后的exe文件运行
    data_path = os.path.dirname(sys.executable)
else:
    # 如果是普通Python脚本运行
    data_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(data_path, "..")
data_path = os.path.join(data_path, "datas")


class EnumManageWin(QDialog):
    DataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("初始化管理窗口")
        self.setBaseSize(400, 300)
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.setWindowTitle(self.tr("可选择项管理"))

        Layout_editList = QHBoxLayout()
        self.mainLayout.addLayout(Layout_editList)

        self.btn_add = QPushButton(self.tr("添加"))
        self.btn_del = QPushButton(self.tr("删除"))
        self.btn_up = QPushButton(self.tr("上移"))
        self.btn_down = QPushButton(self.tr("下移"))
        Layout_editList.addWidget(self.btn_add)
        Layout_editList.addWidget(self.btn_del)
        Layout_editList.addWidget(self.btn_up)
        Layout_editList.addWidget(self.btn_down)

        self.listWidget = QListWidget()
        self.mainLayout.addWidget(self.listWidget)

        Layou_dlgbtns = QHBoxLayout()
        self.mainLayout.addLayout(Layou_dlgbtns)

        self.btn_save = QPushButton(self.tr("保存"))
        self.btn_reset = QPushButton(self.tr("重置"))
        self.btn_cancel = QPushButton(self.tr("取消"))
        Layou_dlgbtns.addWidget(self.btn_save)
        Layou_dlgbtns.addWidget(self.btn_reset)
        Layou_dlgbtns.addWidget(self.btn_cancel)

        self.btn_add.clicked.connect(self.addItem)
        self.btn_del.clicked.connect(self.delItem)
        self.btn_up.clicked.connect(self.upItem)
        self.btn_down.clicked.connect(self.downItem)
        self.btn_save.clicked.connect(self.save_enum_to_db)
        self.btn_reset.clicked.connect(self.resetList)
        self.btn_cancel.clicked.connect(self.close)

        self.setDataBase()

    def setDataBase(self):
        db = QSqlDatabase("QSQLITE")
        db_path = os.path.join(data_path, "enum.db")
        db.setDatabaseName(db_path)
        if not db.open():
            QMessageBox(title="错误", text=f"数据库连接失败: {db.lastError().text()}")
            logger.error(f"数据库连接失败: {db.lastError().text()}")
        logger.debug(f"数据库连接成功: {db.databaseName()}")
        self.db = db

    def setTablename(self, tablename: str):
        self.tableName = tablename

    def load_from_db_to_listwidget(self):
        # 清空现有项
        self.listWidget.clear()
        self.saveToreset = []

        # 执行查询
        query = QSqlQuery(self.db)
        if not query.exec(f"SELECT {self.tableName} FROM {self.tableName}"):
            print("Query failed:", query.lastError().text())
            logger.error(f"数据库查询失败: {query.lastError().text()}")
            return

        # 遍历结果并添加到 QListWidget
        while query.next():
            text = query.value(0)
            item = QListWidgetItem(str(text))
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.listWidget.addItem(item)
            self.saveToreset.append(text)

    def resetList(self):
        self.listWidget.clear()
        for text in self.saveToreset:
            item = QListWidgetItem(str(text))
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.listWidget.addItem(item)
        logger.info("已重置列表")

    def save_enum_to_db(self):
        changed = False
        for i in range(self.listWidget.count()):
            text = self.listWidget.item(i).text()
            if text != self.saveToreset[i]:
                changed = True
                break
        if changed:
            comfirm = QMessageBox.question(
                self,
                "注意",
                "是否重启以应用更改？",
                buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if comfirm == QMessageBox.StandardButton.No:
                return
        try:
            query = QSqlQuery(self.db)
            query.exec(f"DELETE FROM {self.tableName}")
            query.prepare(f"INSERT INTO {self.tableName} ({self.tableName}) VALUES (?)")

            for i in range(self.listWidget.count()):
                text = self.listWidget.item(i).text()
                query.addBindValue(text)
                query.exec()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"{e}")
            logger.error(f"保存失败: {e}")
            return
        self.DataChanged.emit()
        logger.info("已修改列表")
        self.close()

    def closeEvent(self, arg__1):
        self.db.close()
        logger.debug(f"数据库已关闭: {self.db.databaseName()}")
        logger.info("关闭窗口")
        return super().closeEvent(arg__1)

    def addItem(self):
        item = QListWidgetItem(self.tr("请输入"))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.listWidget.addItem(item)
        self.listWidget.setCurrentRow(self.listWidget.count() - 1)
        self.listWidget.editItem(self.listWidget.currentItem())

    def delItem(self):
        self.listWidget.takeItem(self.listWidget.currentRow())
        self.listWidget.setCurrentRow(self.listWidget.currentRow())

    def upItem(self):
        row = self.listWidget.currentRow()
        if row > 0:
            item = self.listWidget.takeItem(row)
            self.listWidget.insertItem(row - 1, item)
            self.listWidget.setCurrentRow(row - 1)

    def downItem(self):
        row = self.listWidget.currentRow()
        if row < self.listWidget.count() - 1:
            item = self.listWidget.takeItem(row)
            self.listWidget.insertItem(row + 1, item)
            self.listWidget.setCurrentRow(row + 1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = EnumManageWin()
    win.setTablename("JigType")
    win.load_from_db_to_listwidget()
    win.show()
    sys.exit(app.exec())
