import re
import json
from pathlib import Path

# =========================
# 配置区
# =========================
LOG_FILE = "_policy-orc_dealer_paddle_v3_01_logs.txt"
OUTPUT_JSON = "pdf_extract_failed_articles.json"
OUTPUT_CSV = "pdf_extract_failed_articles.csv"

# =========================
# 正则规则
# =========================
ARTICLE_ID_PATTERN = re.compile(r"article_id=([a-f0-9]{32})")
PDF_FAIL_PATTERN = re.compile(r"提取PDF文字失败")
FAIL_REASON_PATTERN = re.compile(r"失败原因[:：]\s*(.*)$")

# =========================
# 主逻辑
# =========================
def extract_pdf_failures(log_path: str):
    results = []

    lines = Path(log_path).read_text(encoding="utf-8", errors="ignore").splitlines()

    last_article_id = None

    for idx, line in enumerate(lines):
        # 1. 捕获 article_id（持续更新）
        m_id = ARTICLE_ID_PATTERN.search(line)
        if m_id:
            last_article_id = m_id.group(1)

        # 2. 命中 PDF 提取失败
        if PDF_FAIL_PATTERN.search(line):
            # 提取失败原因
            reason_match = FAIL_REASON_PATTERN.search(line)
            reason = reason_match.group(1) if reason_match else line.strip()

            results.append({
                "article_id": last_article_id,
                "fail_reason": reason,
                "log_line_number": idx + 1,
                "raw_log": line.strip()
            })

    return results


# =========================
# 输出
# =========================
def save_results(results):
    # JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # CSV
    if results:
        import csv
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["article_id", "fail_reason", "log_line_number", "raw_log"]
            )
            writer.writeheader()
            writer.writerows(results)


# =========================
# 入口
# =========================
if __name__ == "__main__":
    failures = extract_pdf_failures(LOG_FILE)
    save_results(failures)

    print(f"PDF 提取失败条数: {len(failures)}")
    print(f"结果已输出：")
    print(f" - {OUTPUT_JSON}")
    print(f" - {OUTPUT_CSV}")
# --coding:utf-8--
