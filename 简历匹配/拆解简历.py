import pdfplumber


def extract_all_text_from_pdf(pdf_path):
    """
    从 PDF 中提取所有文字内容（包含正文和表格）
    返回一个完整的字符串
    """
    texts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # 1. 提取正文文本
            page_text = page.extract_text()
            if page_text:
                texts.append(page_text)

            # 2. 提取表格文本
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row_text = " ".join(
                        cell.strip() for cell in row if cell
                    )
                    if row_text:
                        texts.append(row_text)

    return "\n".join(texts).strip()


# ==================== 使用示例 ====================
if __name__ == "__main__":
    pdf_path = "./合适/【数据产品经理】查雯婷 7年.pdf"  # PDF 路径

    text = extract_all_text_from_pdf(pdf_path)

    print(text)
