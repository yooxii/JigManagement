# PydanticFormWidget.py
from __future__ import annotations
import sys
import logging
from typing import (
    Any,
    Dict,
    Literal,
    Optional,
    get_origin,
    get_args,
    Union,
    List,
    Callable,
)
from datetime import date as py_date
from enum import Enum
from abc import ABC, abstractmethod

from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QLabel,
    QPushButton,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QLayout,
    QMessageBox,
)
from PySide6.QtCore import Qt, QDate, QModelIndex, QSortFilterProxyModel
from PySide6.QtSql import QSqlRecord, QSqlTableModel
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 自定义控件：文件选择器 ====================
class FilePickerWidget(QWidget):
    def __init__(self, parent=None, file_filter="All Files (*)"):
        super().__init__(parent)
        self.file_filter = file_filter
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.line_edit = QLineEdit()
        self.button = QPushButton("浏览...")
        self.button.clicked.connect(self._browse)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def text(self):
        return self.line_edit.text()

    def setText(self, text):
        self.line_edit.setText(text)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", self.file_filter)
        if path:
            self.line_edit.setText(path)


# ==================== 布局策略 ====================
class LayoutStrategy(ABC):
    @abstractmethod
    def add_field(
        self,
        layout,
        label_text: str,
        widget: QWidget,
        error_label: QLabel,
        ui_options: dict = None,
    ):
        pass

    @abstractmethod
    def create_layout(self) -> "QLayout":
        pass


class FormLayoutStrategy(LayoutStrategy):
    def create_layout(self):
        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        return layout

    def add_field(self, layout, label_text, widget, error_label, ui_options=None):
        layout.addRow(f"{label_text}:", widget)
        layout.addRow("", error_label)


class GridLayoutStrategy(LayoutStrategy):
    def __init__(self):
        self.next_row = 0

    def create_layout(self):
        self.next_row = 0
        layout = QGridLayout()
        layout.setColumnStretch(1, 1)
        return layout

    def add_field(self, layout, label_text, widget, error_label, ui_options=None):
        ui = ui_options or {}
        row = ui.get("row")
        col = ui.get("col", 0)
        col_span = ui.get("col_span", 1)
        label_on_left = ui.get("label_on_left", False)

        if row is None:
            row = self.next_row
            self.next_row += 2  # 每个字段占两行（控件+错误）

        if label_on_left:
            label_w = QLabel(f"{label_text}:")
            layout.addWidget(label_w, row, col, Qt.AlignmentFlag.AlignRight)
            layout.addWidget(widget, row, col + 1, 1, col_span)
            layout.addWidget(error_label, row + 1, col + 1, 1, col_span)
        else:
            layout.addWidget(QLabel(f"{label_text}:"), row, col, 1, col_span + 1)
            layout.addWidget(widget, row + 1, col, 1, col_span + 1)
            layout.addWidget(error_label, row + 2, col, 1, col_span + 1)
            self.next_row = row + 3


class VerticalLayoutStrategy(LayoutStrategy):
    def create_layout(self):
        return QVBoxLayout()

    def add_field(self, layout, label_text, widget, error_label, ui_options=None):
        box = QVBoxLayout()
        box.addWidget(QLabel(f"{label_text}:"))
        box.addWidget(widget)
        box.addWidget(error_label)
        layout.addLayout(box)


# ==================== 工具函数 ====================
def _get_ui_options(field_info) -> dict:
    extra = getattr(field_info, "json_schema_extra", None)
    if isinstance(extra, dict):
        return extra.get("ui", {})
    return {}


def map_proxy_to_sql_record(proxy_model, proxy_row: int, column=0):
    """
    从任意层级的代理模型，递归映射到最底层的 QSqlTableModel，并返回 record。

    :param proxy_model: 最外层的代理模型（如 QSortFilterProxyModel）
    :param proxy_row: 代理模型中的行号
    :param column: 用于构建索引的列（通常为 0）
    :return: QSqlRecord 或 None
    """
    current_model = proxy_model
    current_index = current_model.index(proxy_row, column)

    # 递归向下映射，直到找到 QSqlTableModel
    while current_model and not isinstance(current_model, QSqlTableModel):
        if not current_index.isValid():
            return None
        # 映射到源模型
        source_index = current_model.mapToSource(current_index)
        if not source_index.isValid():
            return None
        current_model = current_model.sourceModel()
        current_index = source_index

    # 现在 current_model 是 QSqlTableModel
    if isinstance(current_model, QSqlTableModel):
        return current_model.record(current_index.row())

    return None


def _apply_widget_style(widget: QWidget, ui_options: dict):
    """应用控件样式（宽高、字体、颜色等）"""
    if "width" in ui_options:
        widget.setFixedWidth(ui_options["width"])
    if "height" in ui_options:
        widget.setFixedHeight(ui_options["height"])
    if "min_width" in ui_options:
        widget.setMinimumWidth(ui_options["min_width"])
    if "min_height" in ui_options:
        widget.setMinimumHeight(ui_options["min_height"])
    if "max_width" in ui_options:
        widget.setMaximumWidth(ui_options["max_width"])
    if "max_height" in ui_options:
        widget.setMaximumHeight(ui_options["max_height"])
    if "style" in ui_options:
        widget.setStyleSheet(ui_options["style"])


# ==================== 控件创建 ====================
def _create_widget_for_field(name: str, field_info, field_schema: dict, parent=None):
    from datetime import date

    ui = _get_ui_options(field_info)
    widget_type = ui.get("widget", None)

    has_default = field_info.default not in (PydanticUndefined, None)
    default_val = field_info.default if has_default else None

    # ========== 显式指定 widget ==========
    if widget_type == "password":
        w = QLineEdit(parent)
        w.setEchoMode(QLineEdit.EchoMode.Password)
        if has_default:
            w.setText(str(default_val))
        _apply_widget_style(w, ui)
        return w

    elif widget_type == "date":
        w = QDateEdit(parent)
        w.setCalendarPopup(True)
        w.setDisplayFormat("yyyy-MM-dd")
        if has_default and default_val:
            if isinstance(default_val, str):
                dt = QDate.fromString(default_val, "yyyy-MM-dd")
            elif isinstance(default_val, (py_date, date)):
                dt = QDate(default_val.year, default_val.month, default_val.day)
            else:
                dt = QDate.currentDate()
            w.setDate(dt)
        else:
            w.setDate(QDate.currentDate())
        _apply_widget_style(w, ui)
        return w

    elif widget_type == "file":
        file_filter = ui.get("file_filter", "All Files (*)")
        w = FilePickerWidget(parent, file_filter=file_filter)
        if has_default:
            w.setText(str(default_val))
        _apply_widget_style(w, ui)
        return w

    annotation = field_info.annotation
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Handle Optional[T]
    if hasattr(annotation, "__origin__") and annotation.__origin__ is Union:
        real_types = [t for t in get_args(annotation) if t is not type(None)]
        if len(real_types) == 1:
            annotation = real_types[0]
            origin = get_origin(annotation)
            args = get_args(annotation)

    try:
        schema = field_schema
        ge = schema.get("minimum")
        le = schema.get("maximum")
        gt = schema.get("exclusiveMinimum")
        lt = schema.get("exclusiveMaximum")
    except Exception:
        ge = le = gt = lt = None

    if annotation is bool:
        w = QCheckBox(parent)
        if has_default:
            w.setChecked(bool(default_val))
        _apply_widget_style(w, ui)
        return w

    elif annotation is py_date and widget_type is None:
        w = QDateEdit(parent)
        w.setCalendarPopup(True)
        w.setDisplayFormat("yyyy-MM-dd")
        w.setMinimumWidth(100)
        if has_default and default_val:
            if isinstance(default_val, str):
                dt = QDate.fromString(default_val, "yyyy-MM-dd")
            else:
                dt = QDate(default_val.year, default_val.month, default_val.day)
            w.setDate(dt)
        else:
            w.setDate(QDate.currentDate())
        _apply_widget_style(w, ui)
        return w

    elif annotation is int:
        w = QSpinBox(parent)
        if ge is not None:
            w.setMinimum(int(ge))
        elif gt is not None:
            w.setMinimum(int(gt) + 1)
        if le is not None:
            w.setMaximum(int(le))
        elif lt is not None:
            w.setMaximum(int(lt) - 1)
        if has_default:
            w.setValue(int(default_val))
        _apply_widget_style(w, ui)
        return w

    elif annotation is float:
        w = QDoubleSpinBox(parent)
        w.setDecimals(2)
        if ge is not None:
            w.setMinimum(float(ge))
        elif gt is not None:
            w.setMinimum(float(gt) + 1e-9)
        if le is not None:
            w.setMaximum(float(le))
        elif lt is not None:
            w.setMaximum(float(lt) - 1e-9)
        if has_default:
            w.setValue(float(default_val))
        _apply_widget_style(w, ui)
        return w

    elif origin is Literal:
        w = QComboBox(parent)
        items = [str(v) for v in args]
        w.addItems(items)
        if has_default:
            try:
                idx = items.index(str(default_val))
                w.setCurrentIndex(idx)
            except ValueError:
                pass
        _apply_widget_style(w, ui)
        return w

    elif isinstance(annotation, type) and issubclass(annotation, Enum):
        w = QComboBox(parent)
        values = [
            e.value if isinstance(e.value, str) else str(e.value) for e in annotation
        ]
        w.addItems(values)
        if has_default:
            val_str = str(
                default_val.value if isinstance(default_val, Enum) else default_val
            )
            try:
                idx = values.index(val_str)
                w.setCurrentIndex(idx)
            except (ValueError, AttributeError):
                pass
        _apply_widget_style(w, ui)
        return w

    elif annotation is str:
        w = QLineEdit(parent)
        if has_default:
            w.setText(str(default_val))
        # 可选：支持 placeholder
        if "placeholder" in ui:
            w.setPlaceholderText(ui["placeholder"])
        _apply_widget_style(w, ui)
        return w

    else:
        print(
            f"Warning: Unsupported type {annotation} for field '{name}', using QLineEdit."
        )
        w = QLineEdit(parent)
        _apply_widget_style(w, ui)
        return w


# ==================== Django 风格 Form 类 ====================
class PydanticForm:
    """
    类似 Django Form 的类，可从 Pydantic 模型生成表单
    支持自定义字段标签、顺序、控件等
    """

    def __init__(
        self,
        model_class: type[BaseModel],
        fields: Optional[List[str]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.model_class = model_class
        self.fields = fields or list(model_class.model_fields.keys())
        self.labels = labels or {}
        self.field_widgets: Dict[str, QWidget] = {}
        self._error_labels: Dict[str, QLabel] = {}

    def get_label(self, field_name: str) -> str:
        """获取字段标签文本"""
        # 优先使用 labels 参数
        if field_name in self.labels:
            return self.labels[field_name]
        # 其次使用 Field(title=...) 或字段名
        field_info = self.model_class.model_fields[field_name]
        return field_info.title or field_name.replace("_", " ").capitalize()

    def get_widget_for_field(
        self, field_name: str, field_schema, parent=None
    ) -> QWidget:
        """为指定字段创建控件"""
        if field_name not in self.model_class.model_fields:
            raise ValueError(
                f"Field '{field_name}' not found in model {self.model_class.__name__}"
            )

        field_info = self.model_class.model_fields[field_name]
        return _create_widget_for_field(field_name, field_info, field_schema, parent)

    def get_all_widgets(self, parent=None) -> Dict[str, QWidget]:
        """创建所有字段的控件"""
        widgets = {}
        for field_name in self.fields:
            widgets[field_name] = self.get_widget_for_field(field_name, parent)
        return widgets

    def get_data(self, widgets: Dict[str, QWidget]) -> Dict[str, Any]:
        """从控件获取数据"""
        data = {}
        for name, widget in widgets.items():
            if isinstance(widget, QLineEdit):
                data[name] = widget.text()
            elif isinstance(widget, QDateEdit):
                data[name] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, FilePickerWidget):
                data[name] = widget.text()
            elif isinstance(widget, QSpinBox):
                data[name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                data[name] = widget.value()
            elif isinstance(widget, QCheckBox):
                data[name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                field_info = self.model_class.model_fields[name]
                annotation = field_info.annotation
                origin = get_origin(annotation)
                args = get_args(annotation)

                current_text = widget.currentText()
                if origin is Literal:
                    for val in args:
                        if str(val) == current_text:
                            data[name] = val
                            break
                    else:
                        data[name] = current_text
                elif isinstance(annotation, type) and issubclass(annotation, Enum):
                    try:
                        data[name] = annotation(current_text)
                    except ValueError:
                        data[name] = current_text
                else:
                    data[name] = current_text
            else:
                data[name] = None
        return data

    def validate_and_get_model(
        self, widgets: Dict[str, QWidget]
    ) -> Optional[BaseModel]:
        """验证数据并返回模型实例"""
        data = self.get_data(widgets)
        try:
            return self.model_class(**data)
        except Exception as e:
            from pydantic import ValidationError

            if isinstance(e, ValidationError):
                return None  # 错误信息需要在 UI 中显示
            else:
                raise e


# ==================== 主表单组件（支持 QSortFilterProxyModel） ====================
class PydanticFormWidget(QWidget):
    LAYOUT_STRATEGIES = {
        "form": FormLayoutStrategy,
        "grid": GridLayoutStrategy,
        "vertical": VerticalLayoutStrategy,
    }

    def __init__(
        self,
        model_class: type[BaseModel],
        parent: Optional[QWidget] = None,
        layout_mode: str = "grid",
        show_buttons: bool = True,
        buttons: Optional[List[dict]] = None,
        fields: Optional[List[str]] = None,  # 指定字段顺序
        labels: Optional[Dict[str, str]] = None,  # 自定义标签
        proxy_model: Optional[QSortFilterProxyModel] = None,  # QSortFilterProxyModel
        proxy_row_index: Optional[int] = None,  # 代理模型中的行号
        save_callback: Optional[Callable[[Dict[str, Any]], bool]] = None,  # 保存回调
    ):
        super().__init__(parent)
        self.model_class = model_class
        self.form_instance = PydanticForm(model_class, fields=fields, labels=labels)
        self.field_widgets: Dict[str, QWidget] = {}
        self._error_labels: Dict[str, QLabel] = {}
        self._buttons: Dict[str, QPushButton] = {}

        # QSortFilterProxyModel 相关
        self.proxy_model = proxy_model
        self.proxy_row_index = proxy_row_index
        self.save_callback = save_callback

        if buttons is None:
            buttons = [
                {
                    "name": "submit",
                    "text": "提交",
                    "callback": self._callback_submit,
                },
                {
                    "name": "cancel",
                    "text": "取消",
                    "callback": self.parent().close if self.parent() else None,
                },
            ]

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Build form
        if layout_mode not in self.LAYOUT_STRATEGIES:
            raise ValueError(f"Unsupported layout_mode: {layout_mode}")
        self.strategy = self.LAYOUT_STRATEGIES[layout_mode]()
        self.form_layout = self.strategy.create_layout()
        self._build_form()
        main_layout.addLayout(self.form_layout)

        # Buttons
        if show_buttons and buttons:
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            for cfg in buttons:
                name = cfg["name"]
                text = cfg.get("text", name.capitalize())
                callback = cfg.get("callback")

                btn = QPushButton(text)
                if callback:
                    btn.clicked.connect(callback)
                else:
                    if name == "submit":
                        btn.clicked.connect(self.save_to_proxy_model)
                    elif name == "cancel" and parent and hasattr(parent, "close"):
                        btn.clicked.connect(parent.close)

                btn_layout.addWidget(btn)
                self._buttons[name] = btn
            btn_layout.addStretch()
            main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # 如果有代理模型和行索引，加载数据
        if self.proxy_model and self.proxy_row_index is not None:
            self.load_from_proxy_row(self.proxy_row_index)

    def _build_form(self):
        all_schema = self.model_class.model_json_schema()["properties"]
        for name in self.form_instance.fields:
            field_schema = all_schema[name]
            # 处理hidden属性，如果字段被标记为hidden则跳过
            ui_options = _get_ui_options(self.model_class.model_fields[name])
            if ui_options.get("hidden", False):
                continue
            widget = self.form_instance.get_widget_for_field(name, field_schema, self)
            label_text = self.form_instance.get_label(name)
            self.field_widgets[name] = widget

            error_label = QLabel()
            error_label.setStyleSheet("color: red; font-size: 10px;")
            error_label.setVisible(False)
            self._error_labels[name] = error_label

            ui_opts = _get_ui_options(self.model_class.model_fields[name])
            if isinstance(self.strategy, GridLayoutStrategy):
                self.strategy.add_field(
                    self.form_layout, label_text, widget, error_label, ui_opts
                )
            else:
                self.strategy.add_field(
                    self.form_layout, label_text, widget, error_label
                )

    def get_data(self) -> Dict[str, Any]:
        return self.form_instance.get_data(self.field_widgets)

    def validate_and_get_model(self) -> BaseModel | None:
        for label in self._error_labels.values():
            label.setVisible(False)
        try:
            data = self.get_data()
            logger.debug(f"从表单获取数据: {data}")
            model = self.model_class(**data)
            logger.info("表单数据验证通过")
            return model
        except Exception as e:
            from pydantic import ValidationError

            if isinstance(e, ValidationError):
                logger.warning("表单验证失败", exc_info=True)
                for err in e.errors():
                    field = err["loc"][0]
                    msg = err["msg"]
                    logger.debug(f"字段 {field} 验证错误: {msg}")
                    if field in self._error_labels:
                        self._error_labels[field].setText(msg)
                        self._error_labels[field].setVisible(True)
            else:
                logger.error("表单验证过程中发生未知错误", exc_info=True)
                print("Validation error:", e)
            return None

    def load_from_dict(self, data: dict):
        for name, value in data.items():
            if name not in self.field_widgets:
                continue
            widget = self.field_widgets[name]
            try:
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value) if value is not None else "")
                elif isinstance(widget, QDateEdit):
                    if value:
                        dt = QDate.fromString(str(value), "yyyy-MM-dd")
                        if dt.isValid():
                            widget.setDate(dt)
                elif isinstance(widget, FilePickerWidget):
                    widget.setText(str(value) if value is not None else "")
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value) if value is not None else 0)
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value) if value is not None else 0.0)
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QComboBox):
                    text_val = str(value) if value is not None else ""
                    idx = widget.findText(text_val)
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
            except Exception as e:
                print(f"⚠️ 无法加载字段 {name}: {e}")

    def load_from_record(self, record: QSqlRecord):
        """从 QSqlRecord 加载数据"""
        data = {}
        for i in range(record.count()):
            field_name = record.fieldName(i)
            value = record.value(i)
            if isinstance(value, QDate):
                value = value.toString("yyyy-MM-dd")
            elif value is None:
                value = ""
            data[field_name] = value
        self.load_from_dict(data)

    def load_from_proxy_row(self, proxy_row_index: int):
        """从 QSortFilterProxyModel 的指定行加载数据（支持多层代理）"""
        if not self.proxy_model:
            return

        record = map_proxy_to_sql_record(self.proxy_model, proxy_row_index)
        if record is not None:
            self.load_from_record(record)
            logger.info("从代理模型加载数据成功")
        else:
            logger.warning("无法获取有效记录")

    def _get_field_name_by_title(self, title: str) -> Optional[str]:
        """
        根据字段标题获取对应的字段名

        Args:
            title: 字段标题（如"治具名称"）

        Returns:
            对应的字段名（如"name"），如果找不到则返回None
        """
        for field_name, field_info in self.model_class.model_fields.items():
            if field_info.title == title:
                return field_name
        return None

    def save_to_proxy_model(self) -> bool:
        """将表单数据保存到代理模型对应的源模型（支持新增和修改）"""
        logger.info("开始保存表单数据到代理模型")

        if not self.proxy_model:
            QMessageBox.warning(self, "警告", "未设置代理模型，无法保存数据")
            logger.warning("未设置代理模型，无法保存数据")
            return False

        model = self.validate_and_get_model()
        if not model:
            QMessageBox.warning(self, "验证失败", "表单数据验证失败，无法保存")
            logger.warning("表单数据验证失败，无法保存")
            return False

        # 过滤掉自增主键字段（值为None且标记为primary_key的字段）
        data = model.model_dump()
        filtered_data = {}
        for field_name, value in data.items():
            field_info = self.model_class.model_fields.get(field_name)
            # 检查字段是否为主键且值为None
            is_primary_key = (
                field_info
                and field_info.json_schema_extra
                and field_info.json_schema_extra.get("primary_key") is True
            )

            # 如果是主键且值为None，则跳过该字段
            if is_primary_key and value is None:
                logger.debug(f"跳过自增主键字段 '{field_name}'，其值为None")
                continue

            filtered_data[field_name] = value

        logger.debug(f"过滤后的数据: {filtered_data}")
        source_model = self.proxy_model.sourceModel()

        # === 新增记录 ===
        if self.proxy_row_index is None:
            logger.info("新增记录模式")
            row = source_model.rowCount()
            source_model.insertRow(row)
            for i in range(source_model.columnCount()):
                # 获取表格列标题（中文）
                column_title = source_model.headerData(i, Qt.Orientation.Horizontal)
                # 将标题转换为字段名
                field_name = self._get_field_name_by_title(column_title)

                # 如果找不到对应的字段名，则直接使用列标题
                if field_name is None:
                    field_name = column_title

                if field_name in filtered_data:
                    value = filtered_data[field_name]
                    if isinstance(value, py_date):
                        value = QDate(value.year, value.month, value.day)
                    source_model.setData(source_model.index(row, i), value)
            logger.info(f"新增记录到行 {row}")

        # === 修改记录 ===
        else:
            logger.info(f"修改记录模式，行索引: {self.proxy_row_index}")
            source_index = self.proxy_model.mapToSource(
                self.proxy_model.index(self.proxy_row_index, 0)
            )
            source_row = source_index.row()
            for i in range(source_model.columnCount()):
                # 获取表格列标题（中文）
                column_title = source_model.headerData(i, Qt.Orientation.Horizontal)
                # 将标题转换为字段名
                field_name = self._get_field_name_by_title(column_title)

                # 如果找不到对应的字段名，则直接使用列标题
                if field_name is None:
                    field_name = column_title

                if field_name in filtered_data:
                    value = filtered_data[field_name]
                    if isinstance(value, py_date):
                        value = QDate(value.year, value.month, value.day)
                    if isinstance(value, Enum):
                        value = value.value
                    source_model.setData(source_model.index(source_row, i), value)
            logger.info(f"修改记录在行 {source_row}")

        # 提交更改到数据库
        if hasattr(source_model, "submitAll"):
            if not source_model.submitAll():
                error_text = source_model.lastError().text()
                QMessageBox.critical(self, "错误", f"保存失败: {error_text}")
                source_model.revertAll()
                logger.error(f"保存失败: {error_text}")
                return False

        # 刷新代理模型（确保视图更新）
        self.proxy_model.invalidate()
        logger.info("代理模型已刷新")

        # 调用自定义保存回调（可选）
        if self.save_callback:
            try:
                success = self.save_callback(filtered_data)
                if not success:
                    logger.warning("自定义保存回调返回失败")
                    return False
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存回调执行失败: {str(e)}")
                logger.error(f"保存回调执行失败: {str(e)}", exc_info=True)
                return False

        logger.info("数据保存成功")
        return True

    def _callback_submit(self):
        if self.save_to_proxy_model():
            QMessageBox.information(self, "成功", "数据已保存成功")
        else:
            QMessageBox.critical(self, "错误", "数据保存失败")
        if self.parent():
            self.parent().close()
