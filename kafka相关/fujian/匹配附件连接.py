

import json
import pandas as pd

# 1. 读取失败 article_id
csv_df = pd.read_csv("./pdf_extract_failed_articles.csv")
failed_ids = set(csv_df["article_id"].astype(str).str.strip())

print(f"失败 article_id 数量: {len(failed_ids)}")

matched = []

# 2. 逐行读取 JSONL（容错）
with open("article_ocr_task_fixed.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
        except Exception:
            continue

        # 🔑 关键防御
        if not isinstance(data, dict):
            continue

        _id = str(data.get("_id", "")).strip()
        if _id in failed_ids:
            matched.append(data)

print(f"匹配到的记录数: {len(matched)}")

# 3. 保存结果
with open("matched_failed_articles.json", "w", encoding="utf-8") as f:
    json.dump(matched, f, ensure_ascii=False, indent=2)

