import sys
import os
import logging
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
    QDialog,
)


sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from custom_utils.jiglogger import setup_logging, user_context_filter
from gui.mainWin import MainWindow

setup_logging()

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


class StartWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(400, 200)
        self.setWindowTitle("治具管理系统")

        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)

        self.vLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.vLayout)
        self.vSpacer1 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.vLayout.addSpacerItem(self.vSpacer1)

        self.hLayout = QHBoxLayout()
        self.vLayout.addLayout(self.hLayout)
        self.hSpacer1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.hLayout.addSpacerItem(self.hSpacer1)

        self.mainLayout = QVBoxLayout()
        self.hLayout.addLayout(self.mainLayout)

        self.hSpacer2 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.hLayout.addSpacerItem(self.hSpacer2)

        self.vSpacer2 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.vLayout.addSpacerItem(self.vSpacer2)

        self.initForm()

    def initForm(self):
        self.formLayout = QFormLayout()
        self.formLayout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.mainLayout.addLayout(self.formLayout)

        self.label_username = QLabel(self.tr("用户名："))
        self.line_username = QLineEdit()
        self.formLayout.addRow(self.label_username, self.line_username)
        self.label_password = QLabel(self.tr("密码："))
        self.line_password = QLineEdit()
        self.line_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.formLayout.addRow(self.label_password, self.line_password)

        self.btnLayout = QHBoxLayout()
        self.button_login = QPushButton(self.tr("登录"))
        self.button_login.clicked.connect(self.login)
        self.button_login.setDefault(True)
        self.btnLayout.addWidget(self.button_login)
        self.button_exit = QPushButton(self.tr("退出"))
        self.button_exit.clicked.connect(self.close)
        self.button_exit.setAutoDefault(True)
        self.btnLayout.addWidget(self.button_exit)
        self.mainLayout.addLayout(self.btnLayout)

        self.button_guest = QPushButton(self.tr("访客登录"))
        self.button_guest.clicked.connect(self.guest)
        self.mainLayout.addWidget(self.button_guest)

    def login(self):
        username = self.line_username.text()
        password = self.line_password.text()
        if username == "admin" and password == "ort":
            user_context_filter.current_user = username
            logger.info(username + self.tr("登录成功！"))
            self.user_role = "admin"
            self.startMainWin()
        else:
            QMessageBox.warning(self, self.tr("错误"), self.tr("用户名或密码错误！"))

    def guest(self):
        guestDlg = QDialog(self)
        guestDlg.setWindowTitle(self.tr("访客登录"))
        mainLayout = QVBoxLayout()
        guestDlg.setLayout(mainLayout)
        mainLayout.addWidget(QLabel(self.tr("访客身份登记：")))
        guestName = QLineEdit()
        mainLayout.addWidget(guestName)
        mainLayout.addWidget(QPushButton(self.tr("确定"), clicked=guestDlg.accept))
        if guestDlg.exec() == QDialog.DialogCode.Accepted:
            guestname = guestName.text()
            if guestname == "":
                QMessageBox.warning(self, self.tr("错误"), self.tr("请输入访客名称！"))
                return

        user_context_filter.current_user = "Guest_" + guestname
        logger.info(user_context_filter.current_user + self.tr("访客登录成功！"))

        self.user_role = "Guest"
        self.startMainWin()

    def startMainWin(self):
        self.mainWin = MainWindow(self.user_role)
        self.mainWin.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartWindow()
    window.show()
    sys.exit(app.exec())
