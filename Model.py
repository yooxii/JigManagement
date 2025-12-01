import json
import sys
import os
import sqlite3
import logging
import pandas as pd
from typing import List, Type

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pydantic import BaseModel, Field, create_model
from enum import Enum
from custom_utils.PydanticFormWidget import PydanticFormWidget, py_date


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 数据库文件路径
# 获取正确的基础路径
if getattr(sys, "frozen", False):  # 检查是否为PyInstaller打包环境
    # 如果是打包后的exe文件运行
    data_path = os.path.dirname(sys.executable)
else:
    # 如果是普通Python脚本运行
    data_path = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(data_path, "datas")
if not os.path.exists(data_path):
    os.makedirs(data_path)
db_enum_path = os.path.join(data_path, "enum.db")
logger.info(f"数据库文件路径：{db_enum_path}")


def init_enum_from_db(
    db_path: str,
    init_datas=[
        {"JigType": ["server", "pc", "adapter", "amz"]},
        {"JigUseStatus": ["未使用", "使用中", "异常", "待报废"]},
    ],
) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        for init_data in init_datas:
            for k in init_data.keys():
                df = pd.DataFrame(init_data)
                df.to_sql(k, conn, index=False, if_exists="replace")
                logger.info(f"已创建表 {k}")
    except Exception as e:
        logger.error(f"❌ 初始化数据库失败: {e}", exc_info=True)
        return False
    finally:
        conn.close()
    return True


if not os.path.exists(db_enum_path):
    init_enum_from_db(db_enum_path)


def load_enum_from_file(filepath: str, enum_name: str = "DynamicEnum") -> Type[Enum]:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    # 创建 Enum 类：键为成员名，值为成员值
    # 注意：成员名必须是合法 Python 标识符（大写、无空格等）
    return Enum(enum_name, data, type=str)


def load_enum_from_db(
    db_path: str, table_name: str, enum_name: str = "DynamicEnum"
) -> Type[Enum]:
    """从数据库中加载动态枚举"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        datas = cursor.execute(f"SELECT * FROM {table_name}").fetchall()
    except:
        if not init_enum_from_db(db_path):
            raise Exception("无法初始化数据库")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        datas = cursor.execute(f"SELECT * FROM {table_name}").fetchall()
    finally:
        conn.close()

    data = {}
    for i, row in enumerate(datas):
        data[str(i)] = row[0]
    return Enum(enum_name, data, type=str)


JigType = load_enum_from_db(db_enum_path, "JigType", "JigType")
JigUseStatus = load_enum_from_db(db_enum_path, "JigUseStatus", "JigUseStatus")

fields = {
    "id": (
        int,
        Field(
            None,
            title="ID",
            json_schema_extra={"primary_key": True, "ui": {"hidden": True}},
        ),
    ),
    "name": (
        str,
        Field(title="治具名称", json_schema_extra={"ui": {"row": 0, "col": 0}}),
    ),
    "model": (
        str,
        Field(title="适用机种", json_schema_extra={"ui": {"row": 0, "col": 2}}),
    ),
    "type": (
        JigType,
        Field(title="治具类型", json_schema_extra={"ui": {"row": 0, "col": 4}}),
    ),
    "count": (
        int,
        Field(
            title="治具数量",
            default=1,
            le=999,
            json_schema_extra={"ui": {"row": 0, "col": 6}},
        ),
    ),
    "no": (
        str,
        Field(title="治具编号", json_schema_extra={"ui": {"row": 2, "col": 0}}),
    ),
    "UseStatus": (
        JigUseStatus,
        Field(title="使用状态", json_schema_extra={"ui": {"row": 2, "col": 4}}),
    ),
    "Checkdate": (
        py_date,
        Field(title="校验日期", json_schema_extra={"ui": {"row": 4, "col": 6}}),
    ),
    "Usedcount": (
        int,
        Field(
            le=999999,
            title="已使用次数",
            json_schema_extra={"ui": {"row": 6, "col": 0}},
        ),
    ),
    "Maxcount": (
        int,
        Field(
            title="最大使用次数",
            default=10000,
            le=999999,
            json_schema_extra={"ui": {"row": 4, "col": 0}},
        ),
    ),
    "CheckUsedcount": (
        int,
        Field(
            title="单次校验已使用次数",
            json_schema_extra={"ui": {"row": 6, "col": 2}, "maximum": 99999},
        ),
    ),
    "CheckMaxcount": (
        int,
        Field(
            title="单次校验可使用次数",
            default=2000,
            json_schema_extra={"ui": {"row": 4, "col": 2}, "maximum": 99999},
        ),
    ),
    "CheckCycle": (
        int,
        Field(
            title="校验周期（天）",
            default=365,
            le=9999,
            json_schema_extra={"ui": {"row": 2, "col": 2}},
        ),
    ),
    "Version": (
        str,
        Field(title="治具版本", json_schema_extra={"ui": {"row": 4, "col": 4}}),
    ),
    "Makedate": (
        py_date,
        Field(title="制作日期", json_schema_extra={"ui": {"row": 2, "col": 6}}),
    ),
    "Location": (
        str,
        Field(
            title="存放位置",
            json_schema_extra={"ui": {"row": 6, "col": 4, "col_span": 4}},
        ),
    ),
    "Remark": (
        str,
        Field(
            title="备注",
            json_schema_extra={"ui": {"row": 8, "col": 0, "col_span": 8}},
        ),
    ),
}


class Jig(BaseModel):
    """Jig Model"""

    id: int = Field(
        None,
        title="ID",
        json_schema_extra={"primary_key": True, "ui": {"hidden": True}},
    )
    name: str = Field(title="治具名称", json_schema_extra={"ui": {"row": 0, "col": 0}})
    model: str = Field(title="适用机种", json_schema_extra={"ui": {"row": 0, "col": 2}})
    type: JigType = Field(  # type: ignore
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
    UseStatus: JigUseStatus = Field(  # type: ignore
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


JigDynamic = create_model("Jig", **fields)
