# test_layouts.py
import sys
import os
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pydantic import BaseModel, Field
from enum import Enum
from custom_utils.PydanticFormWidget import PydanticFormWidget, py_date


class JigUseStatus(str, Enum):
    """Use Status"""

    UNUSE = "未使用"
    USING = "使用中"
    ERROR = "异常"
    TO_BE_SCRAPPED = "待报废"


class JigType(str, Enum):
    """Jig Type"""

    SERVER = "server"
    PC = "pc"
    ADAPTER = "adapter"
    AMZ = "amz"


class Jig(BaseModel):
    """Jig Model"""

    id: int = Field(
        None,
        title="ID",
        json_schema_extra={"primary_key": True, "ui": {"hidden": True}},
    )
    name: str = Field(title="治具名称", json_schema_extra={"ui": {"row": 0, "col": 0}})
    model: str = Field(title="适用机种", json_schema_extra={"ui": {"row": 0, "col": 2}})
    type: JigType = Field(
        title="治具类型", json_schema_extra={"ui": {"row": 0, "col": 4}}
    )
    count: int = Field(
        title="治具数量",
        default=1,
        le=999,
        json_schema_extra={"ui": {"row": 0, "col": 6}},
    )
    no: str = Field(title="治具编号", json_schema_extra={"ui": {"row": 2, "col": 0}})
    CheckCycle: int = Field(
        title="校验周期（天）",
        default=360,
        le=9999,
        json_schema_extra={"ui": {"row": 2, "col": 2}},
    )
    UseStatus: JigUseStatus = Field(
        title="使用状态", json_schema_extra={"ui": {"row": 2, "col": 4}}
    )
    Makedate: py_date = Field(
        title="制作日期", json_schema_extra={"ui": {"row": 2, "col": 6}}
    )
    Maxcount: int = Field(
        title="最大使用次数",
        default=10000,
        le=99999,
        json_schema_extra={"ui": {"row": 4, "col": 0}},
    )
    CheckMaxcount: int = Field(
        title="单次校验可使用次数",
        json_schema_extra={"ui": {"row": 4, "col": 2}, "maximum": 9999},
    )
    Version: str = Field(
        title="治具版本", json_schema_extra={"ui": {"row": 4, "col": 4}}
    )
    Checkdate: py_date = Field(
        title="校验日期", json_schema_extra={"ui": {"row": 4, "col": 6}}
    )
    Usedcount: int = Field(
        title="已使用次数", json_schema_extra={"ui": {"row": 6, "col": 0}}
    )
    CheckUsedcount: int = Field(
        title="单次校验已使用次数",
        json_schema_extra={"ui": {"row": 6, "col": 2}, "maximum": 9999},
    )
    Location: str = Field(
        title="存放位置", json_schema_extra={"ui": {"row": 6, "col": 4, "col_span": 4}}
    )
    Remark: str = Field(
        title="备注",
        json_schema_extra={"ui": {"row": 8, "col": 0, "col_span": 8}},
    )
