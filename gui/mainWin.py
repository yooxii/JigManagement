import subprocess
import sys
import os
import logging
from configparser import ConfigParser
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTableView,
    QHeaderView,
    QLabel,
    QMenu,
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
    QFrame,
    QFileDialog,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QAbstractItemView,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QSortFilterProxyModel, QPoint, QDate
from PySide6.QtSql import QSqlDatabase, QSqlTableModel
import pandas as pd
from rich import inspect


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from gui import EnumManageWin, JigDialog, SettingsDlg
from Model import JigDynamic, JigType, JigUseStatus
from custom_utils import Model2SQL
from custom_utils.ColorModel import ColoredSqlProxyModel, find_column_by_header

# 配置日志
logger = logging.getLogger(__name__)

# 获取正确的基础路径
if getattr(sys, "frozen", False):  # 检查是否为PyInstaller打包环境
    # 如果是打包后的exe文件运行
    root_path = os.path.dirname(sys.executable)
else:
    # 如果是普通Python脚本运行
    root_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.join(root_path, "..")
root_path = os.path.abspath(root_path)
data_path = os.path.join(root_path, "datas")


def export_table_to_file(
    parent,
    model,
    view=None,  # 新增：传入 QTableView 以获取选中行
    export_selection_only=False,  # 是否只导出行
    file_filter="CSV Files (*.csv);;Excel Files (*.xlsx);;Text Files (*.txt)",
):
    """
    导出表格数据，支持全部或仅选中行。

    :param parent: 父窗口
    :param model: QAbstractItemModel（通常是代理模型）
    :param view: QTableView（用于获取选中行，当 export_selection_only=True 时必需）
    :param export_selection_only: 是否只导出选中行
    :param file_filter: 文件类型过滤器
    """
    if not model or model.rowCount() == 0:
        QMessageBox.warning(parent, "导出失败", "表格无数据")
        return

    # 获取要导出的行索引
    if export_selection_only:
        if not view:
            raise ValueError("必须提供 QTableView 以导出选中行")
        # 获取所有选中的行号（去重并排序）
        selected_rows = sorted({index.row() for index in view.selectedIndexes()})
        if not selected_rows:
            QMessageBox.warning(parent, "导出失败", "请先选择要导出的行")
            return
    else:
        # 导出所有行
        selected_rows = list(range(model.rowCount()))

    # 弹出保存对话框
    file_path, selected_filter = QFileDialog.getSaveFileName(
        parent, "导出表格数据", "", file_filter
    )
    if not file_path:
        return

    try:
        # 自动补全扩展名
        if selected_filter.startswith("Excel") and not file_path.endswith(".xlsx"):
            file_path += ".xlsx"
        elif selected_filter.startswith("CSV") and not file_path.endswith(".csv"):
            file_path += ".csv"
        elif selected_filter.startswith("Text") and not file_path.endswith(".txt"):
            file_path += ".txt"

        # 提取表头
        headers = []
        for col in range(model.columnCount()):
            header = model.headerData(col, Qt.Horizontal)
            headers.append(str(header) if header is not None else f"Column {col}")

        # 提取选中行的数据
        data = []
        for row in selected_rows:
            row_data = []
            for col in range(model.columnCount()):
                index = model.index(row, col)
                value = model.data(index, Qt.DisplayRole)
                row_data.append(value if value is not None else "")
            data.append(row_data)

        # 创建 DataFrame 并导出
        df = pd.DataFrame(data, columns=headers)

        if file_path.endswith(".xlsx"):
            df.to_excel(file_path, index=False, engine="openpyxl")
        elif file_path.endswith(".csv"):
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
        elif file_path.endswith(".txt"):
            df.to_csv(file_path, index=False, sep="\t", encoding="utf-8")
        else:
            df.to_csv(file_path, index=False, encoding="utf-8-sig")

        QMessageBox.information(parent, "导出成功", f"数据已保存至：\n{file_path}")

    except Exception as e:
        QMessageBox.critical(parent, "导出失败", f"错误：{str(e)}")


def init_config(config_path):
    config = ConfigParser()
    config.add_section("颜色")
    config.add_section("校验")
    config.add_section("使用次数")
    config.add_section("单次校验可使用次数")

    config["颜色"]["警告"] = "orange"
    config["颜色"]["严重警告"] = "red"
    config["校验"]["前多少天警告"] = "14"
    config["校验"]["过期是否加重警告"] = "是"
    config["使用次数"]["剩余多少次警告"] = "50"
    config["使用次数"]["剩余多少次严重警告"] = "10"
    config["单次校验可使用次数"]["剩余多少次警告"] = "50"
    config["单次校验可使用次数"]["剩余多少次严重警告"] = "10"
    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f, space_around_delimiters=False)


def read_settings():
    config = ConfigParser()
    config_path = os.path.join(root_path, "config.ini")
    if not os.path.exists(config_path):
        init_config(config_path)

    config.read(config_path, encoding="utf-8")

    return config


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("开始初始化主窗口")
        self.setWindowTitle(self.tr("治具管理系统"))
        self.resize(800, 600)

        self.config = read_settings()

        self.db_name = os.path.join(data_path, "jig.db")

        self.setSQLite()

        self.setMainMenu()
        self.setMainWidget()
        self.setTable()
        self.setTableMenu()

        self.setConnect()
        self.updateSettings()
        logger.info("主窗口初始化完成")
        self.getCols()

    def getCols(self):
        self.col_jigname = find_column_by_header(self.agent, "治具名称")
        self.col_jigtype = find_column_by_header(self.agent, "治具类型")
        self.col_jigmodel = find_column_by_header(self.agent, "适用机种")
        self.col_jigno = find_column_by_header(self.agent, "治具编号")
        self.col_usestatus = find_column_by_header(self.agent, "使用状态")
        self.col_usecount = find_column_by_header(self.agent, "已使用次数")
        self.col_checkcount = find_column_by_header(self.agent, "单次校验已使用次数")

    ################### 初始化 #################
    def setConnect(self):
        self.searchBtn.clicked.connect(self.searchTable)

        self.btn_add.clicked.connect(self.JigAdd)
        self.btn_alter.clicked.connect(self.JigAlter)
        self.btn_delete.clicked.connect(self.JigDelete)
        self.btn_getjig.clicked.connect(self.getJig)
        self.btn_returnjig.clicked.connect(self.returnJig)
        # self.btn_import.clicked.connect(self.importJig)
        self.btn_exportselect.clicked.connect(self.on_export_selected_table)
        self.btn_exportall.clicked.connect(self.on_export_all_table)
        self.btn_restart.clicked.connect(self.restart_application)
        self.btn_exit.clicked.connect(self.close)

        self.action_exportSelect.triggered.connect(self.on_export_selected_table)
        self.action_exportAll.triggered.connect(self.on_export_all_table)
        self.action_add.triggered.connect(self.JigAdd)
        self.action_alter.triggered.connect(self.JigAlter)
        self.action_delete.triggered.connect(self.JigDelete)
        self.action_initdb.triggered.connect(self.on_init_database)
        self.action_exit.triggered.connect(self.close)
        self.action_jigtype.triggered.connect(self.on_jigtype_manage)
        self.action_getjig.triggered.connect(self.getJig)
        self.action_returnjig.triggered.connect(self.returnJig)
        self.action_settings.triggered.connect(self.show_settings)

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
        self.mainLayout = QHBoxLayout()
        self.centralWidget.setLayout(self.mainLayout)

        self.controlLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.controlLayout)
        self.controlLayout.addSpacing(10)
        self.btn_add = QPushButton(self.tr("添加"))
        self.controlLayout.addWidget(self.btn_add)
        self.btn_alter = QPushButton(self.tr("修改"))
        self.controlLayout.addWidget(self.btn_alter)
        self.btn_delete = QPushButton(self.tr("删除"))
        self.controlLayout.addWidget(self.btn_delete)
        self.btn_jigtype = QPushButton(self.tr("治具类型管理"))
        self.controlLayout.addWidget(self.btn_jigtype)
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        self.controlLayout.addWidget(line1)
        self.btn_getjig = QPushButton(self.tr("取用治具"))
        self.controlLayout.addWidget(self.btn_getjig)
        self.btn_returnjig = QPushButton(self.tr("归还治具"))
        self.controlLayout.addWidget(self.btn_returnjig)
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        self.controlLayout.addWidget(line2)
        self.btn_import = QPushButton(self.tr("导入"))
        self.controlLayout.addWidget(self.btn_import)
        self.btn_exportselect = QPushButton(self.tr("导出选择行"))
        self.controlLayout.addWidget(self.btn_exportselect)
        self.btn_exportall = QPushButton(self.tr("导出整个表格"))
        self.controlLayout.addWidget(self.btn_exportall)
        self.controlLayout.addStretch()
        self.btn_restart = QPushButton(self.tr("重启"))
        self.controlLayout.addWidget(self.btn_restart)
        self.btn_exit = QPushButton(self.tr("退出"))
        self.controlLayout.addWidget(self.btn_exit)

        self.dataLayout = QVBoxLayout()
        self.mainLayout.addLayout(self.dataLayout)

        self.group_filter = QGroupBox(self.tr("筛选"))
        self.dataLayout.addWidget(self.group_filter)
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
        self.edit_makedate_st.setCalendarPopup(True)
        self.edit_makedate_st.setDate(QDate.currentDate().addDays(-1))
        self.edit_makedate_ed = QDateEdit()
        self.edit_makedate_ed.setCalendarPopup(True)
        self.edit_makedate_ed.setDate(QDate.currentDate())
        layout_makedate.addWidget(self.check_makedate)
        layout_makedate.addWidget(label_makedate)
        layout_makedate.addWidget(self.edit_makedate_st)
        layout_makedate.addWidget(QLabel(self.tr("-")))
        layout_makedate.addWidget(self.edit_makedate_ed)
        self.layout_filter.addLayout(
            layout_makedate, 0, 0, 1, 2, Qt.AlignmentFlag.AlignLeft
        )

        layout_checkdate = QHBoxLayout()
        self.check_checkdate = QCheckBox()
        label_checkdate = QLabel(self.tr("校验日期："))
        self.edit_checkdate_st = QDateEdit()
        self.edit_checkdate_st.setCalendarPopup(True)
        self.edit_checkdate_st.setDate(QDate.currentDate().addDays(-1))
        self.edit_checkdate_ed = QDateEdit()
        self.edit_checkdate_ed.setCalendarPopup(True)
        self.edit_checkdate_ed.setDate(QDate.currentDate())
        layout_checkdate.addItem(hSpacer)
        layout_checkdate.addWidget(self.check_checkdate)
        layout_checkdate.addWidget(label_checkdate)
        layout_checkdate.addWidget(self.edit_checkdate_st)
        layout_checkdate.addWidget(QLabel(self.tr("-")))
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
        self.dataLayout.addLayout(self.layout_search)

    def setMainMenu(self):
        self.menu = self.menuBar()

        self.menu_file = self.menu.addMenu(self.tr("文件"))
        self.action_import = QAction(self.tr("从文件中导入"))
        self.action_exportSelect = QAction(self.tr("导出选择行"))
        self.action_exportAll = QAction(self.tr("导出整张表格"))
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
        self.action_initdb = QAction(self.tr("初始化数据库"))
        self.action_settings = QAction(self.tr("设置"))

        self.action_getjig = QAction(self.tr("取用治具"))
        self.menu.addAction(self.action_getjig)

        self.action_returnjig = QAction(self.tr("归还治具"))
        self.menu.addAction(self.action_returnjig)

        self.action_about = QAction(self.tr("关于"))
        self.menu.addAction(self.action_about)

        self.menu_file.addAction(self.action_import)
        self.menu_file.addAction(self.action_exportSelect)
        self.menu_file.addAction(self.action_exportAll)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_exit)
        self.menu_operation.addAction(self.action_add)
        self.menu_operation.addAction(self.action_alter)
        self.menu_operation.addAction(self.action_delete)
        self.menu_option.addAction(self.action_jigtype)
        # self.menu_option.addAction(self.action_initdb) # 不建议初始化数据库
        self.menu_option.addAction(self.action_settings)
        self.setMenuWidget(self.menu)

    def setTableMenu(self):
        self.tableMenu = QMenu()
        self.action_copy = QAction(self.tr("复制"))
        self.action_copy.setShortcut("Ctrl+C")

        self.tableMenu.addAction(self.action_copy)
        self.tableMenu.addAction(self.action_getjig)
        self.tableMenu.addAction(self.action_returnjig)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        def show_menu(pos):
            if self.table.selectedIndexes() != []:
                global_pos = self.table.mapToGlobal(pos)
                self.tableMenu.exec(global_pos)
            else:
                self.tableMenu.close()

        self.table.customContextMenuRequested.connect(show_menu)

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

        self.dataLayout.addWidget(self.table)

    ############## 筛选和搜索 ##############
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

    ############## 添加、修改、删除 ##############
    def JigAdd(self):
        self.addDialog = JigDialog(self, self.color_model)
        self.addDialog.JigUpdate.connect(self.JigUpdate)
        self.addDialog.show()

    def JigAlter(self):
        if self.table.selectionModel().selectedIndexes() == []:
            # TODO: 弹出选择行数窗口
            return

        # proxy_row_index = self.table.selectionModel().selectedIndexes()[0].row()
        proxy_row_index = self.agent.mapToSource(
            self.table.selectionModel().selectedIndexes()[0]
        ).row()
        self.alertDialog = JigDialog(self, self.color_model, proxy_row_index)
        self.alertDialog.setWindowTitle("修改治具")
        self.alertDialog.JigUpdate.connect(self.JigUpdate)
        self.alertDialog.show()

    def JigDelete(self):
        selected_proxy_rows = self.table.selectionModel().selectedRows()
        if not selected_proxy_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的行")
            return

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除选中的 {len(selected_proxy_rows)} 条记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        # 获取源行号（去重 + 降序）
        source_rows = set()
        for proxy_index in selected_proxy_rows:
            source_index = self.agent.mapToSource(proxy_index)
            if source_index.isValid():
                source_rows.add(source_index.row())

        source_rows = sorted(source_rows, reverse=True)

        # 批量删除
        for row in source_rows:
            self.model.removeRow(row)

        # 一次性提交
        if not self.model.submitAll():
            error = self.model.lastError().text()
            QMessageBox.critical(self, "删除失败", f"数据库错误：{error}")
            self.model.revertAll()
            return

        QMessageBox.information(self, "成功", "记录已成功删除")
        self.table.clearSelection()

    def JigUpdate(self, proxy_row_index=None):
        """
        处理新增或修改后的定位

        :param proxy_row_index:
            - 修改时：传入被修改行在代理模型中的行号（int）
            - 新增时：传 None，自动定位到新行
        """
        # 先刷新模型（确保数据同步）
        self.model.select()  # 从数据库重新加载（可选，若 submitAll 已更新则非必需）
        self.agent.invalidate()  # 刷新代理模型（重要！）

        if proxy_row_index is not None:
            # 修改：直接定位
            index = self.agent.mapFromSource(self.color_model.index(proxy_row_index, 0))
            row_index = index.row()
            if index.isValid():
                self.table.scrollTo(index, QAbstractItemView.PositionAtCenter)
                self.table.selectRow(row_index)
        else:
            # 新增：尝试定位到“最新”行
            # 方法：找到源模型最后一行，再映射到代理模型
            source_row_count = self.model.rowCount()
            if source_row_count == 0:
                return

            # 最后一行在源模型中的索引
            last_source_row = source_row_count - 1
            source_index = self.model.index(last_source_row, 0)

            # 映射到代理模型
            proxy_index = self.agent.mapFromSource(source_index)
            if proxy_index.isValid():
                proxy_row = proxy_index.row()
                self.table.scrollTo(proxy_index, QAbstractItemView.PositionAtCenter)
                self.table.selectRow(proxy_row)
            else:
                # 如果被过滤掉了，提示用户
                QMessageBox.information(
                    self, "提示", "新记录已保存，但当前筛选条件下不可见。"
                )

    ############## 设置 ##############
    def show_settings(self):
        self.settings_dialog = SettingsDlg(self.config, self)
        self.settings_dialog.setWindowTitle("设置")
        self.settings_dialog.updateConfig.connect(self.updateSettings)
        self.settings_dialog.show()

    def updateSettings(self, config: ConfigParser = None):
        if config:
            self.config = config
        self.color_model.color_serious = self.config["颜色"]["严重警告"]
        self.color_model.color_warning = self.config["颜色"]["警告"]
        self.color_model.count_Usedserious = int(
            self.config["使用次数"]["剩余多少次严重警告"]
        )
        self.color_model.count_Usedwarning = int(
            self.config["使用次数"]["剩余多少次警告"]
        )
        self.color_model.count_Checkserious = int(
            self.config["单次校验可使用次数"]["剩余多少次严重警告"]
        )
        self.color_model.count_Checkwarning = int(
            self.config["单次校验可使用次数"]["剩余多少次警告"]
        )
        self.color_model.date_Checkwarning = int(self.config["校验"]["前多少天警告"])
        self.model.select()

    ############## 导出 ##############
    def on_export_all_table(self):
        model = self.table.model()
        export_table_to_file(self, model)

    def on_export_selected_table(self):
        model = self.table.model()
        export_table_to_file(self, model, view=self.table, export_selection_only=True)

    def on_init_database(self):
        # 初始化数据库
        reply = QMessageBox.question(
            self,
            "提示-待完善功能",
            "敏感操作，请确认权限！",
            QMessageBox.StandardButton.Yes,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

    def on_jigtype_manage(self):
        self.jigtypeDlg = EnumManageWin()
        self.jigtypeDlg.setWindowTitle("治具类型管理")
        self.jigtypeDlg.setTablename("JigType")
        self.jigtypeDlg.load_from_db_to_listwidget()
        self.jigtypeDlg.DataChanged.connect(self.restart_application)
        self.jigtypeDlg.show()

    def getJig(self):
        """取出治具"""
        if self.col_usestatus == -1:
            return
        proxy_row_index = self.agent.mapToSource(
            self.table.selectionModel().selectedIndexes()[0]
        ).row()
        usestatus_index = self.model.index(proxy_row_index, self.col_usestatus)
        usestatus = self.model.data(usestatus_index)
        if usestatus == JigUseStatus.USING.value:
            QMessageBox.information(self, self.tr("提示"), self.tr("治具在使用中"))
            return
        if usestatus == JigUseStatus.ERROR.value:
            QMessageBox.information(self, self.tr("提示"), self.tr("治具异常"))
            return
        if usestatus == JigUseStatus.SCRAP.value:
            QMessageBox.information(self, self.tr("提示"), self.tr("治具待报废"))
            return
        if usestatus == JigUseStatus.UNUSE.value:
            jigname_index = self.model.index(proxy_row_index, self.col_jigname)
            jigno_index = self.model.index(proxy_row_index, self.col_jigno)
            jigtype_index = self.model.index(proxy_row_index, self.col_jigtype)
            jigmodel_index = self.model.index(proxy_row_index, self.col_jigmodel)
            jigno = self.model.data(jigno_index)
            jigname = self.model.data(jigname_index)
            jigtype = self.model.data(jigtype_index)
            jigmodel = self.model.data(jigmodel_index)
            self.model.setData(usestatus_index, JigUseStatus.USING.value)
            self.model.submitAll()
            self.model.select()
            msg = self.tr(
                f"取用编号为{jigno}的{jigname}，适用于{jigtype}的{jigmodel}机种"
            )
            logger.info(msg)
            QMessageBox.information(self, self.tr("取用"), msg)
        else:
            logger.error("异常的治具状态")

    def returnJig(self):
        """归还治具"""
        if self.col_usestatus == -1:
            return
        proxy_row_index = self.agent.mapToSource(
            self.table.selectionModel().selectedIndexes()[0]
        ).row()
        usestatus_index = self.model.index(proxy_row_index, self.col_usestatus)
        usestatus = self.model.data(usestatus_index)
        if usestatus == JigUseStatus.UNUSE.value:
            QMessageBox.information(self, self.tr("提示"), self.tr("治具未在使用"))
            return
        if usestatus == JigUseStatus.ERROR.value:
            QMessageBox.information(self, self.tr("提示"), self.tr("治具异常"))
            return
        if usestatus == JigUseStatus.SCRAP.value:
            QMessageBox.information(self, self.tr("提示"), self.tr("治具待报废"))
            return
        if usestatus == JigUseStatus.USING.value:
            usecount_index = self.model.index(proxy_row_index, self.col_usecount)
            checkcount_index = self.model.index(proxy_row_index, self.col_checkcount)
            jigname_index = self.model.index(proxy_row_index, self.col_jigname)
            jigno_index = self.model.index(proxy_row_index, self.col_jigno)
            usecount = self.model.data(usecount_index)
            checkcount = self.model.data(checkcount_index)
            jigno = self.model.data(jigno_index)
            jigname = self.model.data(jigname_index)
            self.model.setData(usecount_index, usecount + 1)
            self.model.setData(checkcount_index, checkcount + 1)
            self.model.setData(usestatus_index, JigUseStatus.UNUSE.value)
            self.model.submitAll()
            self.model.select()
            msg = self.tr(
                f"编号为{jigno}的{jigname}已归还"
            )
            logger.info(msg)
            QMessageBox.information(self, self.tr("归还"), msg)
        else:
            logger.error("异常的治具状态")

    def restart_application(self):
        # 执行清理工作
        self.cleanup_before_restart()

        # 使用 QTimer 延迟重启，确保当前事件循环完成
        from PySide6.QtCore import QTimer

        QTimer.singleShot(100, self._restart_process)

    def cleanup_before_restart(self):
        """
        重启前的清理工作
        """
        # 关闭数据库连接
        if hasattr(self, "db") and self.db.isOpen():
            self.db.close()
            logger.info("数据库连接已关闭")

        # 可以添加其他清理逻辑
        logger.info("执行重启前清理工作")

    def _restart_process(self):
        """
        实际执行重启过程
        """
        QApplication.quit()
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
