import json

# ==========================
# 1. 读取原始 JSON
# ==========================
with open("./yunkuaichong_city.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# ==========================
# 2. 过滤四川省并转换格式
# ==========================
result = {
    "area": []
}

for item in data.get("city", []):
    if item.get("pCityName") == "四川省":
        result["area"].append({
            "name": item.get("cityName"),
            "code": int(item.get("cityCode")),
            "lng": item.get("lng"),
            "lat": item.get("lat")
        })

# ==========================
# 3. 输出结果
# ==========================
print(json.dumps(result, ensure_ascii=False, indent=2))
