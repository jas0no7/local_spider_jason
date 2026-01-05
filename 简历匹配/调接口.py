import requests
from pathlib import Path


API_URL = "http://192.168.10.53:8000/extract-text-json"
PDF_PATH = r"./合适/【数据产品经理】查雯婷 7年.pdf"  # 改成你的 PDF 路径


def call_extract_api(pdf_path: str):
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 不存在: {pdf_path}")

    with open(pdf_path, "rb") as f:
        files = {
            "file": (pdf_path.name, f, "application/pdf")
        }

        response = requests.post(API_URL, files=files, timeout=60)

    # HTTP 层错误
    response.raise_for_status()

    # FastAPI 返回 JSON
    return response.json()


if __name__ == "__main__":
    result = call_extract_api(PDF_PATH)

    print("文件名:", result.get("filename"))
    print("=" * 60)
    print(result.get("text"))
