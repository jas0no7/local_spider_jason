import pandas as pd
import re

# ===============================
# 读取 Excel 或 CSV 文件
# ===============================
file_path = r"company_with_address.xlsx"  # TODO: 替换为你的文件路径
df = pd.read_excel(file_path)

# 检查是否包含必要列
if not {"name", "input_name"}.issubset(df.columns):
    raise ValueError("Excel 文件必须包含 'name' 和 'input_name' 两列")

# ===============================
# 定义匹配函数
# ===============================
def is_match(name, input_name):
    """
    判断两列是否匹配：
    规则：
    - 完全一致
    - 去除括号内容后匹配
    - 一列包含另一列
    - 其他情况
    """
    if pd.isna(name) or pd.isna(input_name):
        return False

    # 去除中英文括号及其中内容
    def clean(text):
        return re.sub(r"[（）()]", "", text)

    n1 = clean(name)
    n2 = clean(input_name)

    # 去掉空格、全角空格
    n1 = n1.replace(" ", "").replace("\u3000", "")
    n2 = n2.replace(" ", "").replace("\u3000", "")

    # 规则判断
    if n1 == n2:
        return True
    if n1 in n2 or n2 in n1:
        return True
    return False

# ===============================
#  应用匹配规则并输出结果
# ===============================
df["是否匹配"] = df.apply(lambda x: "匹配" if is_match(x["name"], x["input_name"]) else "不匹配", axis=1)

# ===============================
# 4️⃣ 输出结果保存
# ===============================
output_path = r"check_result2222.xlsx"
df.to_excel(output_path, index=False)
print(f"检查完成，结果已保存至：{output_path}")
