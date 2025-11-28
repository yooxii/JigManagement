from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTableView
from PySide6.QtGui import QAction, QColor, QBrush
from PySide6.QtCore import (
    Qt,
    QIdentityProxyModel,
    QModelIndex,
    QAbstractItemModel,
    QDateTime,
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

    for col in range(model.columnCount()):
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

    def set_column_indices(self, indices: dict):
        """手动设置列名到索引的映射"""
        self._column_indices.update(indices)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        # 获取原始数据
        original_data = super().data(index, role)

        if role == Qt.BackgroundRole:
            col_name = self.headerData(index.column(), Qt.Horizontal)
            if col_name in ["最大使用次数", "单次校验可使用次数"]:
                # 只对这两个列进行逻辑判断
                value = super().data(index, Qt.DisplayRole)
                try:
                    val = int(value)
                except (ValueError, TypeError):
                    return None

                # 获取对应列的数据
                row = index.row()
                if col_name == "最大使用次数":
                    used = self.get_value(row, "已使用次数")
                    if used is not None and val - used < 100:
                        return QBrush(QColor("red"))
                elif col_name == "单次校验可使用次数":
                    used = self.get_value(row, "单次校验已使用次数")
                    if used is not None and val - used < 100:
                        return QBrush(QColor("red"))

            # 判断“下一个校验日是否在前两周”
            elif col_name == "校验日期":
                date_str = super().data(index, Qt.DisplayRole)
                try:
                    check_date = QDateTime.fromString(date_str, "yyyy-MM-dd").toDate()
                    period_days = self.get_value(row, "校验周期（天）")
                    next_check = check_date.addDays(int(period_days))
                    today = QDateTime.currentDateTime().date()

                    # 是否在前两周内？
                    two_weeks_before = next_check.addDays(-14)
                    if two_weeks_before <= today <= next_check:
                        return QBrush(QColor("orange"))
                except:
                    pass

        return original_data

    def get_value(self, row: int, column_name: str):
        """获取指定行和列的值"""
        col_idx = self._column_indices.get(column_name)
        if col_idx is None or col_idx < 0:
            return None
        index = self.index(row, col_idx)
        if not index.isValid():
            return None
        return super().data(index, Qt.DisplayRole)
