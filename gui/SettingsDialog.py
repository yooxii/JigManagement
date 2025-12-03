import sys
import os
import logging
import configparser
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QScrollArea,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QDialog,
)
from PySide6.QtCore import Qt, Signal

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


class SettingsDlg(QDialog):
    """
    设置窗口
    """

    updateConfig = Signal(configparser.ConfigParser)

    def __init__(self, config: configparser.ConfigParser, parent=None):
        super().__init__(parent)

        self.config = config
        self.mainlayout = QVBoxLayout()
        self.setLayout(self.mainlayout)

        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.mainlayout.addWidget(self.scrollarea)

        self.scroll_widget = QWidget()
        self.scrollarea.setWidget(self.scroll_widget)
        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)

        btns_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        btns_layout.addWidget(self.btn_save)
        self.btn_save.clicked.connect(lambda: self.save_settings(True))
        self.btn_apply = QPushButton("应用")
        btns_layout.addWidget(self.btn_apply)
        self.btn_apply.clicked.connect(self.save_settings)
        self.btn_cancel = QPushButton("取消")
        btns_layout.addWidget(self.btn_cancel)
        self.btn_cancel.clicked.connect(self.close)
        self.mainlayout.addLayout(btns_layout)

        self.setWidgets()
        logger.info("设置窗口初始化完成")

    def setWidgets(self):
        for k in self.config.sections():
            groupbox = QGroupBox(k)
            group_layout = QVBoxLayout(groupbox)
            for k1, v1 in self.config.items(k):
                label = QLabel(k1)
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                lineedit = QLineEdit(v1)
                lineedit.setObjectName(k + k1)
                edit_layout = QHBoxLayout()
                edit_layout.addSpacing(10)
                edit_layout.addWidget(label)
                edit_layout.addSpacing(5)
                edit_layout.addWidget(lineedit)
                group_layout.addLayout(edit_layout)
            self.scroll_layout.addWidget(groupbox)

    def save_settings(self, close=False):
        for k in self.config.sections():
            for k1, v1 in self.config.items(k):
                lineedit = self.scroll_widget.findChild(QLineEdit, k + k1)
                self.config.set(k, k1, lineedit.text())
        with open(os.path.join(root_path, "config.ini"), "w", encoding="utf-8") as f:
            self.config.write(f, space_around_delimiters=False)
            logger.info("设置已保存")
        self.updateConfig.emit(self.config)
        if close:
            self.close()

    def closeEvent(self, arg__1):
        logger.info("设置窗口关闭")
        return super().closeEvent(arg__1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    config = configparser.ConfigParser()
    config.read(os.path.join(root_path, "config.ini"), encoding="utf-8")
    dlg = SettingsDlg(config)
    dlg.show()
    sys.exit(app.exec())
