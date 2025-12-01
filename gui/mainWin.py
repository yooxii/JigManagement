import sys
import os
import logging
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTableView,
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
    QButtonGroup,
    QDialog,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QAbstractItemView,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSortFilterProxyModel, QDate
from PySide6.QtSql import QSqlDatabase, QSqlTableModel

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from .JigDialog import JigDialog
from Model import JigDynamic, JigType, JigUseStatus
from custom_utils import Model2SQL
from custom_utils.ColorModel import ColoredSqlProxyModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("开始初始化主窗口")
        self.setWindowTitle(self.tr("治具管理系统"))
        self.resize(800, 600)

        self.db_name = os.path.join(os.path.dirname(__file__), "..", "datas", "jig.db")

        self.setSQLite()

        self.setMainMenu()
        self.setMainWidget()
        self.setTable()

        self.setConnect()
        logger.info("主窗口初始化完成")

    def setConnect(self):
        self.searchBtn.clicked.connect(self.searchTable)
        self.action_add.triggered.connect(self.JigAdd)
        self.action_alter.triggered.connect(self.JigAlter)
        self.action_delete.triggered.connect(self.JigDelete)
        self.action_exit.triggered.connect(self.close)
        self.edit_makedate_st.dateChanged.connect(self.updataFilterDate)
        self.edit_makedate_ed.dateChanged.connect(self.updataFilterDate)
        self.edit_checkdate_st.dateChanged.connect(self.updataFilterDate)
        self.edit_checkdate_ed.dateChanged.connect(self.updataFilterDate)
        self.Combo_usestatus.currentTextChanged.connect(self.applyAllFilters)
        self.Combo_jigtype.currentTextChanged.connect(self.applyAllFilters)
        self.checkbox_group.buttonClicked.connect(self.applyAllFilters)

    def setSQLite(self):
        if not os.path.exists(self.db_name):
            db_dir = os.path.dirname(self.db_name)
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"创建数据库目录: {db_dir}")
            Model2SQL.create_table_from_pydantic_model(
                JigDynamic,
                db_path=self.db_name,
                table_name="jig",
                recreate=True,
            )

        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(self.db_name)
        logger.info(f"设置数据库连接: {self.db_name}")
        if not self.db.open():
            err = "Error: ", self.db.lastError().text()
            logger.error(f"数据库连接失败: {err}")
            raise Exception(err)
        logger.info("数据库连接成功")

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

        self.checkbox_group = QButtonGroup()
        self.checkbox_group.setExclusive(False)

        layout_makedate = QHBoxLayout()
        self.check_makedate = QCheckBox()
        label_makedate = QLabel(self.tr("制作日期："))
        self.edit_makedate_st = QDateEdit()
        self.edit_makedate_st.setDisplayFormat("yyyy-MM-dd")
        self.edit_makedate_st.setDate(QDate.currentDate().addDays(-1))
        self.edit_makedate_ed = QDateEdit()
        self.edit_makedate_ed.setDisplayFormat("yyyy-MM-dd")
        self.edit_makedate_ed.setDate(QDate.currentDate())
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
        label_checkdate = QLabel(self.tr("校验日期："))
        self.edit_checkdate_st = QDateEdit()
        self.edit_checkdate_st.setDisplayFormat("yyyy-MM-dd")
        self.edit_checkdate_st.setDate(QDate.currentDate().addDays(-1))
        self.edit_checkdate_ed = QDateEdit()
        self.edit_checkdate_ed.setDisplayFormat("yyyy-MM-dd")
        self.edit_checkdate_ed.setDate(QDate.currentDate())
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
        self.Combo_usestatus.addItems([i.value for i in list(JigUseStatus)])
        layout_checkdate.addItem(hSpacer)
        layout_usestatus.addWidget(self.check_usestatus)
        layout_usestatus.addWidget(self.label_usestatus)
        layout_usestatus.addWidget(self.Combo_usestatus)
        self.layout_filter.addLayout(layout_usestatus, 0, 4, Qt.AlignmentFlag.AlignLeft)

        layout_jigtype = QHBoxLayout()
        self.check_jigtype = QCheckBox()
        self.label_jigtype = QLabel(self.tr("治具类型："))
        self.Combo_jigtype = QComboBox()
        self.Combo_jigtype.addItems([i.value for i in list(JigType)])
        layout_jigtype.addItem(hSpacer)
        layout_jigtype.addWidget(self.check_jigtype)
        layout_jigtype.addWidget(self.label_jigtype)
        layout_jigtype.addWidget(self.Combo_jigtype)
        self.layout_filter.addLayout(layout_jigtype, 0, 6, Qt.AlignmentFlag.AlignLeft)

        self.checkbox_group.addButton(self.check_makedate)
        self.checkbox_group.addButton(self.check_checkdate)
        self.checkbox_group.addButton(self.check_usestatus)
        self.checkbox_group.addButton(self.check_jigtype)

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

        self.menu_option = self.menu.addMenu(self.tr("选项"))
        self.action_jigtype = QAction(self.tr("治具类型管理"))
        self.action_settings = QAction(self.tr("设置"))

        self.action_about = QAction(self.tr("关于"))
        self.menu.addAction(self.action_about)

        self.menu_file.addAction(self.action_import)
        self.menu_file.addAction(self.action_export)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)
        self.menu_operation.addAction(self.action_add)
        self.menu_operation.addAction(self.action_alter)
        self.menu_operation.addAction(self.action_delete)
        self.menu_option.addAction(self.action_jigtype)
        self.menu_option.addAction(self.action_settings)
        self.setMenuWidget(self.menu)

    def setTable(self):
        # 数据模型
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable("Jig")
        self.model.select()

        # 设置表头显示名称为Pydantic模型中的title
        for i, field_name in enumerate(JigDynamic.model_fields.keys()):
            field_info = JigDynamic.model_fields[field_name]
            # 设置表头显示名称为Pydantic模型中的title
            field_title = field_info.title or field_name
            self.model.setHeaderData(i, Qt.Orientation.Horizontal, field_title)

        # 颜色模型
        self.color_model = ColoredSqlProxyModel()
        self.color_model.setSourceModel(self.model)
        self.color_model.get_column_indices()

        # 代理模型
        self.agent = QSortFilterProxyModel()
        self.agent.setSourceModel(self.color_model)
        self.agent.setFilterKeyColumn(-1)

        # 表格视图
        self.table = QTableView()
        self.table.setModel(self.agent)
        self.table.setSortingEnabled(True)
        # 禁止在表格中修改
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置表格拉伸
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        self.mainLayout.addWidget(self.table)

    def searchTable(self):
        self.agent.setFilterRegularExpression(self.searchInput.text())

    def updataFilterDate(self):
        # TODO: 跟随最大或最小日期变化
        self.edit_checkdate_ed.setMinimumDate(self.edit_checkdate_st.date())
        self.edit_checkdate_st.setMaximumDate(self.edit_checkdate_ed.date())
        self.edit_makedate_ed.setMinimumDate(self.edit_makedate_st.date())
        self.edit_makedate_st.setMaximumDate(self.edit_makedate_ed.date())

    def applyAllFilters(self):
        # 收集所有激活的过滤条件
        filters = []

        # 制作日期过滤
        if self.check_makedate.isChecked():
            start_date = self.edit_makedate_st.date().toString("yyyy-MM-dd")
            end_date = self.edit_makedate_ed.date().toString("yyyy-MM-dd")
            filters.append(f"Makedate BETWEEN '{start_date}' AND '{end_date}'")

        # 效验日期过滤
        if self.check_checkdate.isChecked():
            start_date = self.edit_checkdate_st.date().toString("yyyy-MM-dd")
            end_date = self.edit_checkdate_ed.date().toString("yyyy-MM-dd")
            filters.append(f"Checkdate BETWEEN '{start_date}' AND '{end_date}'")

        # 使用状态过滤
        if self.check_usestatus.isChecked():
            selected_status = self.Combo_usestatus.currentText()
            if selected_status != "-":
                filters.append(f"UseStatus = '{selected_status}'")

        # 治具类型过滤
        if self.check_jigtype.isChecked():
            selected_type = self.Combo_jigtype.currentText()
            if selected_type != "-":
                filters.append(f"Type = '{selected_type}'")

        # 应用组合过滤条件
        if filters:
            combined_filter = " AND ".join(filters)
            self.model.setFilter(combined_filter)
        else:
            self.model.setFilter("")

        self.model.select()

    def JigAdd(self):
        self.addDialog = JigDialog(self, self.agent)
        self.addDialog.JigUpdate.connect(self.JigUpdate)
        self.addDialog.show()

    def JigAlter(self):
        if self.table.selectionModel().selectedIndexes() == []:
            # TODO: 弹出选择行数窗口
            return

        proxy_row_index = self.table.selectionModel().selectedIndexes()[0].row()
        self.alertDialog = JigDialog(self, self.agent, proxy_row_index)
        self.alertDialog.setWindowTitle("修改治具")
        self.alertDialog.JigUpdate.connect(self.JigUpdate)
        self.alertDialog.show()

    def JigDelete(self):
        if self.table.selectionModel().selectedIndexes() == []:
            # TODO: 弹出选择行数窗口
            return

        # 确认删除操作
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这些记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        # 完成删除
        for index in self.table.selectionModel().selectedRows():
            proxy_row_index = index.row()

            # 获取源模型行索引
            source_index = self.agent.mapToSource(self.agent.index(proxy_row_index, 0))
            source_row = source_index.row()

            if reply == QMessageBox.Yes:
                # 从源模型中删除行
                self.model.removeRow(source_row)

                # 提交更改到数据库
                if not self.model.submitAll():
                    QMessageBox.critical(
                        self, "错误", f"删除失败: {self.model.lastError().text()}"
                    )
                    self.model.revertAll()
                else:
                    QMessageBox.information(self, "成功", "记录已删除")

        # 刷新模型
        self.model.select()
        self.agent.invalidate()

    def JigUpdate(self, proxy_row_index=None):
        # 定位到新增的行
        self.model.select()
        self.agent.invalidate()
        self.table.selectRow(self.agent.index(proxy_row_index, 0).row())
