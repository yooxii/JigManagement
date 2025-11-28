import logging
from typing import Type, get_origin, get_args, Optional, Union
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

# 配置日志
logger = logging.getLogger(__name__)


def _map_type_to_sql(python_type, field_schema: dict) -> str:
    """根据 JSON Schema 映射 SQL 类型"""
    # 基础类型映射
    if python_type is int:
        return "INTEGER"
    elif python_type is float:
        return "REAL"
    elif python_type is bool:
        return "BOOLEAN"
    elif python_type is str:
        max_len = field_schema.get("maxLength")
        return f"TEXT({max_len})" if max_len is not None else "TEXT"
    elif getattr(python_type, "__name__", None) == "date":
        return "DATE"
    elif getattr(python_type, "__name__", None) == "datetime":
        return "DATETIME"
    else:
        return "TEXT"


def _get_constraints(field_name: str, field_info: FieldInfo, field_schema: dict) -> str:
    parts = []
    checks = []

    # 从 JSON Schema 提取数值约束
    if "minimum" in field_schema:
        checks.append(f"{field_name} >= {field_schema['minimum']}")
    if "exclusiveMinimum" in field_schema:
        checks.append(f"{field_name} > {field_schema['exclusiveMinimum']}")
    if "maximum" in field_schema:
        checks.append(f"{field_name} <= {field_schema['maximum']}")
    if "exclusiveMaximum" in field_schema:
        checks.append(f"{field_name} < {field_schema['exclusiveMaximum']}")

    if checks:
        parts.append("CHECK (" + " AND ".join(checks) + ")")
    if field_info.json_schema_extra and field_info.json_schema_extra.get("primary_key"):
        parts.append("PRIMARY KEY")
        # 如果是主键且类型为int，则添加AUTOINCREMENT
        if field_info.annotation is int:
            parts.append("AUTOINCREMENT")

    # DEFAULT 值处理（保持不变）
    if field_info.default is not PydanticUndefined:
        dv = field_info.default
        if isinstance(dv, bool):
            sql_val = "1" if dv else "0"
        elif isinstance(dv, str):
            dv = dv.replace("'", "''")
            sql_val = f"'{dv}'"
        elif dv is None:
            sql_val = "NULL"
        elif isinstance(dv, (int, float)):
            sql_val = str(dv)
        elif hasattr(dv, "isoformat"):  # date / datetime
            sql_val = f"'{dv.isoformat()}'"
        else:
            dv = str(dv).replace("'", "''")
            sql_val = f"'{dv}'"
        parts.append(f"DEFAULT {sql_val}")

    return " ".join(parts)


def pydantic_model_to_sql_create_table(
    model_class: Type[BaseModel], table_name: Optional[str] = None
) -> str:
    if table_name is None:
        table_name = model_class.__name__.lower()

    # ✅ 一次性生成整个模型的 JSON Schema
    full_schema = model_class.model_json_schema()
    properties_schema = full_schema.get("properties", {})

    fields = model_class.model_fields
    column_defs = []

    for name, field in fields.items():
        # 获取该字段的 JSON Schema 片段
        field_schema = properties_schema.get(name, {})

        # 映射 SQL 类型（需要原始 annotation + schema）
        col_type = _map_type_to_sql(field.annotation, field_schema)

        # 判断是否可为空
        origin = get_origin(field.annotation)
        args = get_args(field.annotation)
        is_optional = origin is Union and type(None) in args
        not_null = "" if is_optional else "NOT NULL"

        # 获取约束（传入 field_schema）
        constraints = _get_constraints(name, field, field_schema)

        col_def = f"    {name} {col_type} {not_null} {constraints}".strip()
        column_defs.append(col_def)

    columns_str = ",\n".join(column_defs)
    return f"CREATE TABLE {table_name} (\n{columns_str}\n);"


def create_table_from_pydantic_model(
    model_class: Type[BaseModel],
    db_path: str = ":memory:",
    table_name: Optional[str] = None,
    recreate: bool = False,
):
    """
    根据 Pydantic 模型在 SQLite 中创建表。

    :param model_class: 继承自 BaseModel 的类
    :param db_path: SQLite 数据库路径，:memory: 表示内存数据库
    :param table_name: 表名，默认为模型类名小写
    :param recreate: 是否先 DROP 再 CREATE
    """
    import sqlite3

    if table_name is None:
        table_name = model_class.__name__.lower()

    logger.info(f"开始创建表 {table_name}，数据库路径: {db_path}")

    # 生成完整 schema
    full_schema = model_class.model_json_schema()
    properties_schema = full_schema.get("properties", {})

    fields = model_class.model_fields
    column_defs = []

    for name, field in fields.items():
        field_schema = properties_schema.get(name, {})
        col_type = _map_type_to_sql(field.annotation, field_schema)

        origin = get_origin(field.annotation)
        args = get_args(field.annotation)
        is_optional = origin is Union and type(None) in args
        not_null = "" if is_optional else "NOT NULL"

        constraints = _get_constraints(name, field, field_schema)
        col_def = f"{name} {col_type} {not_null} {constraints}".strip()
        column_defs.append(col_def)
        logger.debug(f"字段定义: {col_def}")

    columns_str = ",\n    ".join(column_defs)
    create_sql = f"CREATE TABLE {'IF NOT EXISTS' if not recreate else ''} {table_name} (\n    {columns_str}\n);"

    if recreate:
        drop_sql = f"DROP TABLE IF EXISTS {table_name};"

    # 连接数据库并执行
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.debug(f"执行SQL: {create_sql}")

    try:
        if recreate:
            cursor.execute(drop_sql)
            logger.info(f"已删除现有表 {table_name}")
        print(create_sql)
        cursor.execute(create_sql)
        conn.commit()
        logger.info(f"✅ 表 '{table_name}' 已在数据库 '{db_path}' 中创建。")
        print(f"✅ 表 '{table_name}' 已在数据库 '{db_path}' 中创建。")
    except Exception as e:
        logger.error(f"❌ 创建表失败: {e}", exc_info=True)
        print(f"❌ 创建表失败: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from Model import JigDynamic

    # print(pydantic_model_to_sql_create_table(Jig))
    os.chdir(os.path.dirname(__file__))
    db_path = "../datas/jig.db"
    create_table_from_pydantic_model(JigDynamic, db_path=db_path, recreate=True)
