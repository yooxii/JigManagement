import logging
import os
import pandas as pd
import sqlite3


from faker import Faker

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

os.chdir(os.path.dirname(__file__))
con = sqlite3.connect("test.db")
jigTypes = pd.DataFrame({"治具类型名称": ["Server", "PC", "AMZ", "Adpter"]})

fake = Faker()
Jigs = pd.DataFrame(
    [
        {
            "治具编号": fake.random_int(),
            "治具名称": ("".join(fake.random_letters(8))).upper(),
            "制作日期": fake.date(),
            "适用机种": ("".join(fake.random_letters(8))).upper(),
            "治具类型": fake.random_element(jigTypes["治具类型名称"]),
            "版本": fake.random_letter(),
            "最大使用次数": fake.random_int(min=1000),
            "已使用次数": fake.random_int(max=1000),
            "位置": fake.word(),
            "单次校验可使用次数": 100,
            "单次校验已使用次数": fake.random_int(max=100),
            "校验日期": fake.date(),
            "使用状态": fake.random_element(["正常", "异常", "停用"]),
            "备注": "",
        }
        for _ in range(1000)
    ]
)
# 打印第一行数据
print(Jigs.head(1))
logger.info("开始将Jigs数据写入数据库")
Jigs.to_sql("Jig", con, index=False, if_exists="replace")
logger.info("Jigs数据写入完成")

logger.info("开始将jigTypes数据写入数据库")
jigTypes.to_sql("JigType", con, index=False, if_exists="replace")
logger.info("jigTypes数据写入完成")

con.close()
logger.info("数据库连接已关闭")