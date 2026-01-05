import json
import requests
from pathlib import Path

# ======================
# 1. 配置
# ======================
JSON_FILE = "article_ocr_task_fixed.json"
BASE_DIR = Path(r"D:/minio_upload_cache")
FAILED_FILE = Path("failed_attachments.json")

TIMEOUT = 30

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/141.0.0.0",
    "Accept": "*/*",
}

# ======================
# 2. 下载函数
# ======================
def download_file(url: str, save_path: Path):
    save_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

# ======================
# 3. 主逻辑
# ======================
def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    failed = []

    for item in data:
        for att in item.get("attachment", []):
            url = att.get("attachment_url")
            relative_path = att.get("relative_path")

            if not url or not relative_path:
                print(f"[跳过] 字段不完整: {att}")
                continue

            # ⭐ 正确的路径拼接方式
            save_path = BASE_DIR / relative_path.lstrip("/")

            # 已存在则跳过
            if save_path.exists():
                print(f"[已存在] {save_path}")
                continue

            try:
                print(f"[下载] {url}")
                download_file(url, save_path)
                print(f"[成功] {save_path}")
            except Exception as e:
                print(f"[失败] {url} -> {e}")
                failed.append({
                    "attachment_url": url,
                    "relative_path": relative_path,
                    "error": str(e),
                })

    if failed:
        with open(FAILED_FILE, "w", encoding="utf-8") as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)
        print(f"\n失败附件已记录到 {FAILED_FILE}")

if __name__ == "__main__":
    main()
