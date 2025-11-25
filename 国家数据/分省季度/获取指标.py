import json
import requests

# --- 保持不变的配置 ---
headers = {
    "Accept": "text/plain, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://data.stats.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://data.stats.gov.cn/easyquery.htm?cn=E0102",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    # 请注意：这里的JSESSIONID可能已失效，您可能需要更新它以确保请求成功
    "$JSESSIONID": "HP245zWMd5fBqMfR5dXA-eYwe3aNzxRJZN9lUSDS8vv5PGcvSnbC\\u0021-993230399",
    "u": "2"
}
url = "https://data.stats.gov.cn/easyquery.htm"
zhibiao1 = {
    "A01": "国民经济核算",
    "A02": "建筑业",
    "A03": "人民生活",
    "A04": "农业",
    "A05": "价格指数",
    "A06": "国内贸易"
}
# --- 核心修改部分 ---

# 1. 初始化最终结果列表
result_list = []

for zhibiao1_id, zhibiao1_name in zhibiao1.items():
    # 2. 初始化当前一级指标下的二级指标列表
    le2_list = []

    # 3. 构造请求数据
    data = {
        "id": zhibiao1_id,
        "dbcode": "fsjd",
        "wdcode": "zb",
        "m": "getTree"
    }

    # 4. 发送请求
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=data)
        # 检查响应状态码和内容，确保请求成功
        response.raise_for_status()
        zhibiao_list = json.loads(response.text)
    except requests.exceptions.RequestException as e:
        print(f"请求 {zhibiao1_name} ({zhibiao1_id}) 失败: {e}")
        continue
    except json.JSONDecodeError:
        print(f"解析 {zhibiao1_name} ({zhibiao1_id}) 响应失败，响应内容: {response.text[:100]}...")
        continue

    # 5. 遍历二级指标，并按目标格式添加到 le2_list
    for zhibiao in zhibiao_list:
        le2_id = zhibiao.get("id")
        le2_name = zhibiao.get("name")

        # 确保 id 和 name 存在
        if le2_id and le2_name:
            le2_data = {
                "le2_id": le2_id,
                "le2_name": le2_name,
            }
            le2_list.append(le2_data)

    # 6. 将当前一级指标和其二级指标列表包装成目标字典格式，并添加到总列表
    # 目标格式: {"一级指标名": [二级指标列表]}
    if le2_list:  # 仅在有数据时添加
        zhibiao1_dict = {
            zhibiao1_name: le2_list
        }
        result_list.append(zhibiao1_dict)

# 7. 构造最终的 JSON 结构 (使用 "分省季度指标" 作为最外层键)
# 如果您想要的最外层键是 "固定资产投资(不含农户)"，请自行修改下面的变量名
overall_key = "分省季度指标"
final_json_data = {
    overall_key: result_list
}

# 8. 输出到控制台或文件
print("\n--- 最终 JSON 结构 (部分展示) ---")
# 打印格式化的 JSON 字符串
print(json.dumps(final_json_data, indent=2, ensure_ascii=False))


with open("zhibiao_output.json", "w", encoding="utf-8") as f:
    json.dump(final_json_data, f, indent=2, ensure_ascii=False)
print("\n数据已保存到 zhibiao_output.json 文件。")