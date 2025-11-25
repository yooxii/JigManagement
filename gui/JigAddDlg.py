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
)
from PySide6.QtCore import Qt


class JigAddDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加治具")
        self.setBaseSize(400, 300)
        # self.setWindowModality(Qt.ApplicationModal)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout_inputs = QGridLayout()
        self.layout_inputs.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.addLayout(self.layout_inputs)

        self.layout_name = QHBoxLayout()
        self.label_jig_name = QLabel(self.tr("治具名称："))
        self.edit_jig_name = QLineEdit()
        self.layout_name.addWidget(self.label_jig_name)
        self.layout_name.addWidget(self.edit_jig_name)
        self.layout_inputs.addLayout(self.layout_name, 0, 0, Qt.AlignmentFlag.AlignLeft)

        self.layout_type = QHBoxLayout()
        self.label_jig_type = QLabel(self.tr("治具类型："))
        self.Combo_jigType = QComboBox()
        self.Combo_jigType.addItems(["-"])
        self.layout_type.addWidget(self.label_jig_type)
        self.layout_type.addWidget(self.Combo_jigType)
        self.layout_inputs.addLayout(self.layout_type, 0, 1, Qt.AlignmentFlag.AlignLeft)

        self.layout_model = QHBoxLayout()
        self.label_jig_model = QLabel(self.tr("适用机种："))
        self.edit_jig_model = QLineEdit()
        self.layout_model.addWidget(self.label_jig_model)
        self.layout_model.addWidget(self.edit_jig_model)
        self.layout_inputs.addLayout(
            self.layout_model, 1, 0, Qt.AlignmentFlag.AlignLeft
        )

        self.layout_count = QHBoxLayout()
        self.label_jig_count = QLabel(self.tr("机种数量："))
        self.edit_jig_count = QSpinBox()
        self.edit_jig_count.setValue(1)
        self.edit_jig_count.setMinimum(0)
        self.layout_count.addWidget(self.label_jig_count)
        self.layout_count.addWidget(self.edit_jig_count)
        self.layout_inputs.addLayout(
            self.layout_count, 1, 1, Qt.AlignmentFlag.AlignLeft
        )

        self.layout_Maxcount = QHBoxLayout()
        self.label_jig_Maxcount = QLabel(self.tr("最大使用次数："))
        self.edit_jig_Maxcount = QSpinBox()
        self.edit_jig_Maxcount.setValue(1000)
        self.edit_jig_Maxcount.setMinimum(0)
        self.layout_Maxcount.addWidget(self.label_jig_Maxcount)
        self.layout_Maxcount.addWidget(self.edit_jig_Maxcount)
        self.layout_inputs.addLayout(
            self.layout_Maxcount, 2, 1, Qt.AlignmentFlag.AlignLeft
        )
