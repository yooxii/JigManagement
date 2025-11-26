from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QDateEdit,
    QTextEdit,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtSql import QSqlRecord


class JigDialog(QDialog):
    def __init__(self, parent=None, datas=None):
        super().__init__(parent)
        self.setWindowTitle("添加治具")
        self.setBaseSize(400, 300)
        # self.setWindowModality(Qt.ApplicationModal)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.setWidget()
        self.setDatas(datas)

        self.setSpinsValue()
        self.setConnect()

    def setConnect(self):
        self.spin_jig_Maxcount.valueChanged.connect(self.updataMaxcount)
        self.spin_jig_CheckMaxcount.valueChanged.connect(self.updataMaxCheckcount)
        self.edit_jig_Makedate.dateChanged.connect(self.updataDate)

    def setWidget(self):
        self.layout_inputs = QGridLayout()
        self.layout_inputs.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.addLayout(self.layout_inputs)

        self.layout_name = QHBoxLayout()
        self.label_jig_name = QLabel(self.tr("治具名称："))
        self.edit_jig_name = QLineEdit()
        self.edit_jig_name.setMaximumWidth(120)
        self.layout_name.addWidget(self.label_jig_name)
        self.layout_name.addWidget(self.edit_jig_name)
        self.layout_inputs.addLayout(self.layout_name, 0, 0)

        self.layout_model = QHBoxLayout()
        self.label_jig_model = QLabel(self.tr("适用机种："))
        self.edit_jig_model = QLineEdit()
        self.edit_jig_model.setMaximumWidth(120)
        self.layout_model.addWidget(self.label_jig_model)
        self.layout_model.addWidget(self.edit_jig_model)
        self.layout_inputs.addLayout(self.layout_model, 0, 1)

        self.layout_type = QHBoxLayout()
        self.label_jig_type = QLabel(self.tr("治具类型："))
        self.Combo_jigType = QComboBox()
        self.Combo_jigType.addItems(["-"])
        self.layout_type.addWidget(self.label_jig_type)
        self.layout_type.addWidget(self.Combo_jigType)
        self.layout_inputs.addLayout(self.layout_type, 0, 2)

        self.layout_count = QHBoxLayout()
        self.label_jig_count = QLabel(self.tr("治具数量："))
        self.spin_jig_count = QSpinBox()
        self.layout_count.addWidget(self.label_jig_count)
        self.layout_count.addWidget(self.spin_jig_count)
        self.layout_inputs.addLayout(self.layout_count, 0, 3)

        self.layout_JigNo = QHBoxLayout()
        self.label_jig_JigNo = QLabel(self.tr("治具编号："))
        self.edit_jig_JigNo = QLineEdit()
        self.edit_jig_JigNo.setMaximumWidth(120)
        self.layout_JigNo.addWidget(self.label_jig_JigNo)
        self.layout_JigNo.addWidget(self.edit_jig_JigNo)
        self.layout_inputs.addLayout(self.layout_JigNo, 1, 0)

        self.layout_CheckCycle = QHBoxLayout()
        self.label_jig_CheckCycle = QLabel(self.tr("校验周期(天)："))
        self.spin_jig_CheckCycle = QSpinBox()
        self.layout_CheckCycle.addWidget(self.label_jig_CheckCycle)
        self.layout_CheckCycle.addWidget(self.spin_jig_CheckCycle)
        self.layout_inputs.addLayout(self.layout_CheckCycle, 1, 1)

        self.layout_UseStatus = QHBoxLayout()
        self.label_jig_UseStatus = QLabel(self.tr("使用状态："))
        self.Combo_jig_UseStatus = QComboBox()
        self.Combo_jig_UseStatus.addItems(["未使用", "使用中", "异常", "待报废"])
        self.layout_UseStatus.addWidget(self.label_jig_UseStatus)
        self.layout_UseStatus.addWidget(self.Combo_jig_UseStatus)
        self.layout_inputs.addLayout(self.layout_UseStatus, 1, 2)

        self.layout_Makedate = QHBoxLayout()
        self.label_jig_Makedate = QLabel(self.tr("制作日期："))
        self.edit_jig_Makedate = QDateEdit()
        self.layout_Makedate.addWidget(self.label_jig_Makedate)
        self.layout_Makedate.addWidget(self.edit_jig_Makedate)
        self.layout_inputs.addLayout(self.layout_Makedate, 1, 3)

        self.layout_Maxcount = QHBoxLayout()
        self.label_jig_Maxcount = QLabel(self.tr("最大使用次数："))
        self.spin_jig_Maxcount = QSpinBox()
        self.layout_Maxcount.addWidget(self.label_jig_Maxcount)
        self.layout_Maxcount.addWidget(self.spin_jig_Maxcount)
        self.layout_inputs.addLayout(self.layout_Maxcount, 2, 0)

        self.layout_CheckMaxcount = QHBoxLayout()
        self.label_jig_CheckMaxcount = QLabel(self.tr("单次校验可使用次数："))
        self.spin_jig_CheckMaxcount = QSpinBox()
        self.layout_CheckMaxcount.addWidget(self.label_jig_CheckMaxcount)
        self.layout_CheckMaxcount.addWidget(self.spin_jig_CheckMaxcount)
        self.layout_inputs.addLayout(self.layout_CheckMaxcount, 2, 1)

        self.layout_Version = QHBoxLayout()
        self.label_jig_Version = QLabel(self.tr("治具版本："))
        self.edit_jig_Version = QLineEdit()
        self.edit_jig_Version.setMaximumWidth(60)
        self.layout_Version.addWidget(self.label_jig_Version)
        self.layout_Version.addWidget(self.edit_jig_Version)
        self.layout_inputs.addLayout(self.layout_Version, 2, 2)

        self.layout_Checkdate = QHBoxLayout()
        self.label_jig_Checkdate = QLabel(self.tr("校验日期："))
        self.edit_jig_Checkdate = QDateEdit()
        self.layout_Checkdate.addWidget(self.label_jig_Checkdate)
        self.layout_Checkdate.addWidget(self.edit_jig_Checkdate)
        self.layout_inputs.addLayout(self.layout_Checkdate, 2, 3)

        self.layout_Usedcount = QHBoxLayout()
        self.label_jig_Usedcount = QLabel(self.tr("已使用次数："))
        self.spin_jig_Usedcount = QSpinBox()
        self.layout_Usedcount.addWidget(self.label_jig_Usedcount)
        self.layout_Usedcount.addWidget(self.spin_jig_Usedcount)
        self.layout_inputs.addLayout(self.layout_Usedcount, 3, 0)

        self.layout_CheckUsedcount = QHBoxLayout()
        self.label_jig_CheckUsedcount = QLabel(self.tr("单次校验已使用次数："))
        self.spin_jig_CheckUsedcount = QSpinBox()
        self.layout_CheckUsedcount.addWidget(self.label_jig_CheckUsedcount)
        self.layout_CheckUsedcount.addWidget(self.spin_jig_CheckUsedcount)
        self.layout_inputs.addLayout(self.layout_CheckUsedcount, 3, 1)

        self.layout_Location = QHBoxLayout()
        self.label_jig_Location = QLabel(self.tr("存放位置："))
        self.edit_jig_Location = QLineEdit()
        self.layout_Location.addWidget(self.label_jig_Location)
        self.layout_Location.addWidget(self.edit_jig_Location)
        self.layout_inputs.addLayout(self.layout_Location, 3, 2, 1, 2)

        self.layout_Remark = QHBoxLayout()
        self.label_jig_Remark = QLabel(self.tr("备注："))
        self.edit_jig_Remark = QTextEdit()
        self.edit_jig_Remark.setMaximumHeight(25)
        self.layout_Remark.addWidget(self.label_jig_Remark)
        self.layout_Remark.addWidget(self.edit_jig_Remark)
        self.layout_inputs.addLayout(self.layout_Remark, 4, 0, 1, 4)

        self.edit_jig_Makedate.setDate(QDate.currentDate())
        self.edit_jig_Checkdate.setDate(QDate.currentDate().addYears(1))

    def updataDate(self):
        makedate = self.edit_jig_Makedate.date()
        self.edit_jig_Checkdate.setDate(makedate.addYears(1))

    def setSpinsValue(self):
        self.spin_jig_count.setRange(0, 1000)
        self.spin_jig_count.setValue(1)
        self.spin_jig_Maxcount.setRange(0, 999999)
        self.spin_jig_Maxcount.setValue(10000)
        self.updataMaxcount()
        self.spin_jig_Usedcount.setValue(0)
        self.spin_jig_CheckMaxcount.setValue(1000)
        self.updataMaxCheckcount()
        self.spin_jig_CheckUsedcount.setValue(0)

    def updataMaxCheckcount(self):
        maxCheckcount = self.spin_jig_CheckMaxcount.value()
        self.spin_jig_CheckUsedcount.setRange(0, maxCheckcount)

    def updataMaxcount(self):
        maxcount = self.spin_jig_Maxcount.value()
        self.spin_jig_Usedcount.setRange(0, maxcount)
        self.spin_jig_CheckMaxcount.setRange(0, maxcount)

    def setDatas(self, datas: QSqlRecord = None):
        if not datas:
            return
        # 打印数据
        for i in range(datas.count()):
            print(datas.fieldName(i), datas.value(i))
