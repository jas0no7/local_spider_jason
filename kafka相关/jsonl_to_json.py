
import json


import json

input_path = r"D:\项目文件夹\local_spider_jason\kafka相关\article_ocr_task.jsonl"
output_path = r"D:\项目文件夹\local_spider_jason\kafka相关\article_ocr_task1.json"
objects = []
buffer = ""
brace_count = 0

with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if not line.strip():
            continue

        brace_count += line.count("{")
        brace_count -= line.count("}")

        buffer += line

        if brace_count == 0 and buffer.strip():
            try:
                obj = json.loads(buffer)
                objects.append(obj)
            except json.JSONDecodeError:
                pass
            buffer = ""

with open(output_path, "w", encoding="utf-8", errors="replace") as f:
    json.dump(objects, f, ensure_ascii=False, indent=2)

print(f"成功写出 {len(objects)} 条记录")

