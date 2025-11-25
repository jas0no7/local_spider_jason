import pandas as pd

# 读取 CSV（自动尝试兼容编码）
df = pd.read_csv("企业关键词提取结果.csv", encoding="utf-8")


# 去除空值并转为列表
ids = df["关键词"].dropna().astype(str).tolist()
print(ids)
# 按你需要的格式生成字符串
formatted = "[" + ",".join([f"'{i}'" for i in ids]) + "]"

print(formatted)


