import pandas as pd
import pymysql

# 读取 Excel
local_station = pd.read_excel(r"C:/Users/edac/Desktop/charge_station(1).xlsx")

# 只保留必要字段
local_station = local_station[["站编码", "站点类型"]]

# 去除空的“站点类型”
local_station = local_station.dropna(subset=["站点类型"])

# 建立 Excel 的映射: {station_no: station_category}
excel_map = dict(zip(local_station["站编码"].astype(str), local_station["站点类型"]))

print("Excel 映射数量:", len(excel_map))

# ================
# 更新 MySQL
# ================
conn = pymysql.connect(
    host='192.168.0.217',
    user='root',
    password='edac123456',
    database='scdd_db',
    port=1106,
    charset="utf8mb4"
)
cursor = conn.cursor()

# 获取需要更新的 station_no 列表
sql = """
SELECT station_no 
FROM charging_station
WHERE property_owner_merhant_id = 119
"""
cursor.execute(sql)
rows = cursor.fetchall()

update_count = 0

for (station_no,) in rows:
    station_no = str(station_no)

    if station_no in excel_map:
        new_value = excel_map[station_no]

        update_sql = """
        UPDATE charging_station
        SET station_category = %s
        WHERE station_no = %s
          AND property_owner_merhant_id = 119
        """

        cursor.execute(update_sql, (new_value, station_no))
        update_count += 1

conn.commit()
cursor.close()
conn.close()

print(f"更新完成，共更新 {update_count} 条记录")
