from collections import OrderedDict
import logging
import os
import pandas as pd
import sqlite3


from faker import Faker

os.chdir(os.path.dirname(__file__))
con = sqlite3.connect("test.db")
jigTypes = pd.DataFrame({"治具类型名称": ["server", "pc", "amz", "adpter"]})

fake = Faker()
Jigs = pd.DataFrame(
    [
        {
            "id": i + 1,
            "name": ("".join(fake.random_letters(8))).upper(),
            "model": ("".join(fake.random_letters(8))).upper(),
            "type": fake.random_element(jigTypes["治具类型名称"]),
            "count": 1,
            "no": fake.random_int(),
            "UseStatus": fake.random_element(
                OrderedDict(
                    [
                        ("未使用", 0.7),
                        ("使用中", 0.2),
                        ("异常", 0.05),
                        ("待报废", 0.05),
                    ]
                )
            ),
            "Checkdate": fake.date_between("-1y", "today"),
            "Usedcount": fake.random_int(max=10000),
            "Maxcount": 10000,
            "CheckUsedcount": fake.random_int(max=2000),
            "CheckMaxcount": 2000,
            "CheckCycle": 365,
            "Version": fake.random_letter(),
            "Makedate": fake.date_between("-3y", "today"),
            "Location": fake.word(),
            "Remark": "",
        }
        for i in range(10)
    ]
)
# 打印第一行数据
print(Jigs.head(1))
# Jigs.to_sql("Jig", con, index=False, if_exists="replace")
Jigs.to_html("Jig.html", index=False, max_rows=10)

con.close()
