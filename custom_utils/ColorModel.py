from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTableView
from PySide6.QtGui import QAction, QColor, QBrush
from PySide6.QtCore import (
    Qt,
    QIdentityProxyModel,
    QModelIndex,
    QAbstractItemModel,
    QDateTime,
    QDate,
    QTime,
)
from PySide6.QtSql import QSqlDatabase, QSqlTableModel

import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from Model import JigDynamic, JigType, JigUseStatus


def find_column_by_header(model: QAbstractItemModel, header_text: str) -> int:
    """
    在代理模型中查找指定标题对应的列索引。

    :param model: QAbstractItemModel 的子类实例（如 QSortFilterProxyModel）
    :param header_text: 要查找的列标题文本
    :return: 列索引（int），未找到返回 -1
    """
    if not model:
        return -1

    count = model.columnCount()
    for col in range(count):
        header_data = model.headerData(col, Qt.Horizontal)
        # 转为字符串比较，兼容 QVariant 可能是 int 等类型
        if str(header_data) == header_text:
            return col
    return -1


# 自定义代理模型：实现条件着色
class ColoredSqlProxyModel(QIdentityProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._column_indices = {
            "校验日期": None,
            "已使用次数": None,
            "最大使用次数": None,
            "单次校验已使用次数": None,
            "单次校验可使用次数": None,
            "校验周期（天）": None,
        }

    def get_column_indices(self):
        self._column_indices = {
            header_text: find_column_by_header(self.sourceModel(), header_text)
            for header_text in self._column_indices.keys()
        }

    def set_column_indices(self, indices: dict):
        """手动设置列名到索引的映射"""
        self._column_indices.update(indices)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        # 获取原始数据
        original_data = super().data(index, role)

        if role == Qt.ItemDataRole.BackgroundRole:
            col_name = self.headerData(index.column(), Qt.Horizontal)
            # 获取对应列的数据
            row = index.row()
            if col_name in ["已使用次数", "单次校验已使用次数"]:
                # 只对这两个列进行逻辑判断
                value = super().data(index, Qt.ItemDataRole.DisplayRole)
                try:
                    val = int(value)
                except (ValueError, TypeError):
                    return None

                if col_name == "已使用次数":
                    maxcount = self.get_value(row, "最大使用次数")
                    if maxcount is not None and maxcount - val < 50:
                        return QBrush(QColor("red"))
                elif col_name == "单次校验已使用次数":
                    maxcount = self.get_value(row, "单次校验可使用次数")
                    if maxcount is not None and maxcount - val < 50:
                        return QBrush(QColor("red"))

            # 判断“下一个校验日是否在前两周”
            elif col_name == "校验日期":
                date_str = super().data(index, Qt.ItemDataRole.DisplayRole)
                if isinstance(date_str, str):
                    check_date = QDateTime.fromString(date_str, "yyyy-MM-dd")
                elif isinstance(date_str, QDateTime):
                    check_date = date_str
                elif isinstance(date_str, QDate):
                    check_date = date_str.startOfDay()
                else:
                    raise ValueError("Invalid date format")
                period_days = self.get_value(row, "校验周期（天）")
                next_check = check_date.addDays(int(period_days))
                today = QDateTime.currentDateTime()

                # 是否在前两周内？
                two_weeks_before = next_check.addDays(-14)
                if two_weeks_before <= today <= next_check:
                    return QBrush(QColor("orange"))

        return original_data

    def invalidate(self):
        """
        添加 invalidate 方法以兼容现有代码
        """
        self.beginResetModel()
        self.endResetModel()

    def get_value(self, row: int, column_name: str):
        """获取指定行和列的值"""
        col_idx = self._column_indices.get(column_name)
        if col_idx is None or col_idx < 0:
            return None
        index = self.index(row, col_idx)
        if not index.isValid():
            return None
        return super().data(index, Qt.ItemDataRole.DisplayRole)
