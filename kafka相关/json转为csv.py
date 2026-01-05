import json
import csv

# =========================
# 1. 文件路径
# =========================
INPUT_JSON = "./YkcSichuanTemporary.json"
OUTPUT_CSV = "./YkcSichuanTemporary.csv"

# =========================
# 2. 读取 JSON
# =========================
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# data 必须是 {"data": [...]}
rows = data.get("data", [])

# =========================
# 3. 只保留包含 name 的记录
# =========================
filtered = [item for item in rows if "name" in item and item["name"]]

print(f"原始记录数: {len(rows)}")
print(f"保留含 name 的记录数: {len(filtered)}")

if not filtered:
    raise ValueError("没有任何包含 name 字段的数据")

# =========================
# 4. 定义 CSV 字段（只取你真正关心的）
# =========================
fieldnames = [
    "station_id",
    "name",
    "address",
    "lng",
    "lat",
    "operator",
    "business_hours",
    "park_fee_desc",
    "from",
    "spider_date",
    "update_date",
]

# =========================
# 5. 写入 CSV
# =========================
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for item in filtered:
        writer.writerow({
            key: item.get(key, "")
            for key in fieldnames
        })

print(f"CSV 写入完成：{OUTPUT_CSV}")
