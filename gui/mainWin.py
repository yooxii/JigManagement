from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
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
    QDialog,
    QSpacerItem,
    QSizePolicy,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtSql import QSqlDatabase, QSqlTableModel


from .JigDialog import JigDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("治具管理系统"))
        self.resize(800, 600)

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("test.db")
        if not self.db.open():
            err = "Error: ", self.db.lastError().text()
            raise Exception(err)

        self.setMainMenu()
        self.setMainWidget()
        self.setTable()

        self.setConnect()

    def setConnect(self):
        self.searchBtn.clicked.connect(self.searchTable)
        self.action_add.triggered.connect(self.JigAdd)
        self.action_alter.triggered.connect(self.JigAlter)
        self.action_delete.triggered.connect(self.JigDelete)
        self.action_exit.triggered.connect(self.close)

    def setMainWidget(self):
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QVBoxLayout()
        self.centralWidget.setLayout(self.mainLayout)

        self.group_filter = QGroupBox(self.tr("筛选"))
        self.mainLayout.addWidget(self.group_filter)
        self.layout_filter = QGridLayout(self.group_filter)

        hSpacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        layout_makedate = QHBoxLayout()
        self.check_makedate = QCheckBox()
        label_makedate = QLabel(self.tr("制作日期："))
        self.edit_makedate_st = QDateEdit()
        self.edit_makedate_ed = QDateEdit()
        layout_makedate.addWidget(self.check_makedate)
        layout_makedate.addWidget(label_makedate)
        layout_makedate.addWidget(self.edit_makedate_st)
        layout_makedate.addWidget(QLabel(self.tr("~")))
        layout_makedate.addWidget(self.edit_makedate_ed)
        self.layout_filter.addLayout(
            layout_makedate, 0, 0, 1, 2, Qt.AlignmentFlag.AlignLeft
        )

        layout_checkdate = QHBoxLayout()
        self.check_checkdate = QCheckBox()
        label_checkdate = QLabel(self.tr("效验日期："))
        self.edit_checkdate_st = QDateEdit()
        self.edit_checkdate_ed = QDateEdit()
        layout_checkdate.addItem(hSpacer)
        layout_checkdate.addWidget(self.check_checkdate)
        layout_checkdate.addWidget(label_checkdate)
        layout_checkdate.addWidget(self.edit_checkdate_st)
        layout_checkdate.addWidget(QLabel(self.tr("~")))
        layout_checkdate.addWidget(self.edit_checkdate_ed)
        self.layout_filter.addLayout(
            layout_checkdate, 0, 2, 1, 2, Qt.AlignmentFlag.AlignLeft
        )

        layout_usestatus = QHBoxLayout()
        self.check_usestatus = QCheckBox()
        self.label_usestatus = QLabel(self.tr("使用状态："))
        self.Combo_usestatus = QComboBox()
        self.Combo_usestatus.addItems(["-", "使用中", "未使用", "异常"])
        layout_checkdate.addItem(hSpacer)
        layout_usestatus.addWidget(self.check_usestatus)
        layout_usestatus.addWidget(self.label_usestatus)
        layout_usestatus.addWidget(self.Combo_usestatus)
        self.layout_filter.addLayout(layout_usestatus, 0, 4, Qt.AlignmentFlag.AlignLeft)

        self.layout_search = QHBoxLayout()
        self.searchInput = QLineEdit()
        self.searchBtn = QPushButton(self.tr("搜索"))
        self.layout_search.addWidget(self.searchInput)
        self.layout_search.addWidget(self.searchBtn)
        self.mainLayout.addLayout(self.layout_search)

    def setMainMenu(self):
        self.menu = self.menuBar()

        self.menu_file = self.menu.addMenu(self.tr("文件"))
        self.action_import = QAction(self.tr("从文件中批量导入"))
        self.action_export = QAction(self.tr("将选择的数据导出"))
        self.action_exit = QAction(self.tr("退出"))

        self.menu_operation = self.menu.addMenu(self.tr("操作"))
        self.action_add = QAction(self.tr("新增"))
        self.action_add.setShortcut("Ctrl+N")
        self.action_alter = QAction(self.tr("修改"))
        self.action_alter.setShortcut("Ctrl+M")
        self.action_delete = QAction(self.tr("删除"))
        self.action_delete.setShortcut("Ctrl+D")

        self.action_settings = QAction(self.tr("设置"))
        self.menu.addAction(self.action_settings)

        self.action_about = QAction(self.tr("关于"))
        self.menu.addAction(self.action_about)

        self.menu_file.addAction(self.action_import)
        self.menu_file.addAction(self.action_export)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)
        self.menu_operation.addAction(self.action_add)
        self.menu_operation.addAction(self.action_alter)
        self.menu_operation.addAction(self.action_delete)
        self.setMenuWidget(self.menu)

    def setTable(self):
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

    def searchTable(self):
        self.agent.setFilterRegularExpression(self.searchInput.text())

    def JigAdd(self):
        self.addDialog = JigDialog(self)
        self.addDialog.show()

    def JigAlter(self):
        self.alertDialog = JigDialog(self)
        if self.table.selectedIndexes():
            self.alertDialog.setDatas(
                self.model.record(
                    self.agent.mapToSource(self.table.selectedIndexes()[0]).row()
                )
            )
        self.alertDialog.show()

    def JigDelete(self):
        pass
