import json
import pandas as pd
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c37)XWEB/14185",
    "mini_ver": "13.2000",
    "ua": "{\"model\":\"microsoft\",\"platform\":\"windows\"}",
    "wt2": "",
    "zp_app_id": "10002",
    "content-type": "application/x-www-form-urlencoded",
    "traceid": "F-fde08cowpU3pu7wv",
    "mpt": "f5852a2247d8d442b948952171a736fc",
    "scene": "1256",
    "xweb_xhr": "1",
    "x-requested-with": "XMLHttpRequest",
    "zp_product_id": "10002",
    "platform": "zhipin/windows",
    "ver": "13.2000",
    "sec-fetch-site": "cross-site",
    "sec-fetch-mode": "cors",
    "sec-fetch-dest": "empty",
    "referer": "https://servicewechat.com/wxa8da525af05281f3/585/page-frame.html",
    "accept-language": "zh-CN,zh;q=0.9",
    "priority": "u=1, i"
}

url = "https://www.zhipin.com/wapi/zpgeek/miniapp/search/brandlist.json"
df = pd.read_excel('科研企业名单.xlsx')
names = df['企业名称']

all_data = []

for name in names:
    # 删除这行：name = "宁夏阿德斯"  # 这行会覆盖从Excel读取的名称

    params = {
        "pageSize": "20",
        "query": name,
        "city": "101270100",
        "source": "1",
        "sortType": "0",
        "subwayLineId": "",
        "subwayStationId": "",
        "districtCode": "",
        "businessCode": "",
        "longitude": "",
        "latitude": "",
        "position": "",
        "expectId": "",
        "expectPosition": "",
        "encryptExpectId": "",
        "page": "1",
        "appId": "10002"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # 检查请求是否成功

        data_list = json.loads(response.text)

        # 添加错误检查
        if ("zpData" in data_list and
                "brandList" in data_list["zpData"] and
                len(data_list["zpData"]["brandList"]) > 0):

            company_name = data_list["zpData"]["brandList"][0]["name"]
            company_location = data_list["zpData"]["brandList"][0]["businessArea"]
            company_id = data_list["zpData"]["brandList"][0]["encryptBrandId"]

            data_dict = {
                "input_name": name,
                "brandId": company_id,
                "brandName": company_name,
                "brandLocation": company_location,
            }
            all_data.append(data_dict)
            print(f"成功获取: {name}")
        else:
            print(f"未找到公司: {name}")
            # 添加未找到的记录
            data_dict = {
                "input_name": name,
                "brandId": "未找到",
                "brandName": "未找到",
                "brandLocation": "未找到",
            }
            all_data.append(data_dict)

    except Exception as e:
        print(f"处理 {name} 时出错: {e}")
        # 添加错误记录
        data_dict = {
            "input_name": name,
            "brandId": "请求失败",
            "brandName": "请求失败",
            "brandLocation": "请求失败",
        }
        all_data.append(data_dict)

# 正确创建DataFrame
df1 = pd.DataFrame(all_data)  # 直接使用列表，不需要再放在列表中

# 保存为CSV文件
df1.to_csv('df1.csv', index=False, encoding='utf-8-sig')
print(f"数据已保存，共处理 {len(all_data)} 条记录")