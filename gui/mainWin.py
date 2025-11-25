from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtSql import QSqlDatabase, QSqlTableModel


from .JigAddDlg import JigAddDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("治具管理系统"))
        self.resize(800, 600)

        self.setMainMenu()
        self.setMainWidget()
        self.setTable()

        self.setConnect()

    def setMainWidget(self):
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QVBoxLayout()
        self.centralWidget.setLayout(self.mainLayout)

        self.searchLayout = QHBoxLayout()
        self.searchInput = QLineEdit()
        self.searchBtn = QPushButton(self.tr("搜索"))
        self.searchLayout.addWidget(self.searchInput)
        self.searchLayout.addWidget(self.searchBtn)
        self.mainLayout.addLayout(self.searchLayout)

    def setMainMenu(self):
        self.menu = self.menuBar()
        self.action_add = QAction(self.tr("新增"))
        self.action_add.setShortcut("Ctrl+N")
        self.menu.addAction(self.action_add)
        self.action_alter = QAction(self.tr("修改"))
        self.action_alter.setShortcut("Ctrl+M")
        self.menu.addAction(self.action_alter)
        self.action_delete = QAction(self.tr("删除"))
        self.action_delete.setShortcut("Ctrl+D")
        self.menu.addAction(self.action_delete)
        self.setMenuWidget(self.menu)

    def setTable(self):
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("test.db")
        if not self.db.open():
            err = "Error: ", self.db.lastError().text()
            raise Exception(err)

        # 数据模型
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable("Jig")
        self.model.select()

        # 代理模型
        self.agent = QSortFilterProxyModel()
        self.agent.setSourceModel(self.model)
        self.agent.setFilterKeyColumn(-1)

        # 表格视图
        self.table = QTableView()
        self.table.setModel(self.agent)
        self.table.setSortingEnabled(True)

        self.mainLayout.addWidget(self.table)

    def setConnect(self):
        self.searchBtn.clicked.connect(self.searchTable)
        self.action_add.triggered.connect(self.JigAdd)

    def searchTable(self):
        self.agent.setFilterRegularExpression(self.searchInput.text())

    def JigAdd(self):
        self.addDialog = JigAddDialog(self)
        self.addDialog.show()
