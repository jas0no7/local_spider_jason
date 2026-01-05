import json
import time
import requests
from pathlib import Path

FAILED_FILE = "failed_attachments.json"
BASE_DIR = Path(r"D:/minio_upload_cache")

JX_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,"
        "application/pdf,"
        "application/msword,"
        "application/vnd.ms-excel,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
}

session = requests.Session()

def download(url, save_path: Path):
    save_path.parent.mkdir(parents=True, exist_ok=True)

    for i in range(1, 4):
        try:
            with session.get(
                url,
                headers=JX_HEADERS,
                stream=True,
                timeout=(10, 240),  # ★ read timeout 拉到 4 分钟
            ) as r:
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(2048):  # 慢一点
                        if chunk:
                            f.write(chunk)
            return True
        except Exception as e:
            print(f"[江西重试 {i}/3] {url} -> {e}")
            time.sleep(15 * i)
    return False

def main():
    with open(FAILED_FILE, "r", encoding="utf-8") as f:
        failed = json.load(f)

    still_failed = []

    for item in failed:
        url = item["attachment_url"]
        err = item["error"]

        if "drc.jiangxi.gov.cn" not in url:
            continue
        if "Read timed out" not in err:
            continue

        save_path = BASE_DIR / item["relative_path"].lstrip("/")

        if save_path.exists():
            print(f"[已存在] {save_path}")
            continue

        print(f"[江西慢速补抓] {url}")
        ok = download(url, save_path)

        if not ok:
            still_failed.append(item)

    if still_failed:
        with open("failed_attachments_stage2.json", "w", encoding="utf-8") as f:
            json.dump(still_failed, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
