import requests
import json
import time
import csv
import random
# --- 请确保以下信息是你最新抓包获取的 ---
URL = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"

HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=8&token=237409963&lang=zh_CN&timestamp=1767508830006",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "x-requested-with": "XMLHttpRequest"
}

# 复制你刚才代码里的完整 cookies
COOKIES = {
    "RK": "4n+Q7DkbR9",
    "ptcz": "06e610245ea18abb2595ee44c7d0c0450dbb48a7fae61bbe2abcac5360ccb6be",
    "eas_sid": "D17774J9Z1l781e8l0L168N4B0",
    "pgv_pvid": "6344216056",
    "fqm_pvqid": "6050f84b-b1c3-4bfa-bede-f3e200232741",
    "_qimei_uuid42": "19a0d09073b1001f4c22c7617089ea6dbba6c68348",
    "_qimei_fingerprint": "0b0d42084c6cb29bed570ad51ec3b7d1",
    "_qimei_q36": "",
    "_qimei_h38": "a4fa7af74c22c7617089ea6d0200000bc19a0d",
    "ua_id": "3CFB2Iz0DlqKspPgAAAAAG2Ivt-ZgQCXnR1dn7nS6P0=",
    "_clck": "yi6308|1|g2f|0",
    "wxuin": "67508769800339",
    "mm_lang": "zh_CN",
    "uuid": "f05f01c118e1d92ed01b467205237a2d",
    "rand_info": "CAESIPcdrhgNGR/zyjvvqqRZEF6cDsa0Ml3SJZjmwf40jHoo",
    "slave_bizuin": "3576963203",
    "data_bizuin": "3576963203",
    "bizuin": "3576963203",
    "data_ticket": "woNCu5BCMyNC/vKvNnglk1QEtuL4xZyAKR3iB8WLZHnkCn2jv4AVu1o4mZPNnIvN",
    "slave_sid": "NHUwMEMwVHNrNXFDN09SME9fZGpHUVpIS2g5eEtWNlN4eEZxNkdSbGR6UlVJbTZjTU9lbTRHaWJ6WkIyaUhQRkhpUWpjZFlTUV91Zm9aYUNSeDRjdWJZRFBUOVB5cEI0S0Y3M2UyVkV2Q2JrNnhaVnZoTHdsQTU5NWsyODJZTEhqRjI4dHptMmtwTHg1bkxs",
    "slave_user": "gh_3bc6203573ae",
    "xid": "7206fef30475299c424024bd48d83d5e",
    "_clsk": "1hhcnx6|1767508833730|4|1|mp.weixin.qq.com/weheat-agent/payload/record"
}

# 基础请求参数
BASE_PARAMS = {
    "sub": "list",
    "search_field": "null",
    "count": "5",  # 每次抓5篇
    "query": "",
    "fakeid": "MzU5NDg1OTc5MQ==",  # 目标公众号ID
    "type": "101_1",
    "free_publish_type": "1",
    "sub_action": "list_ex",
    "token": "237409963",  # 你的 Token
    "lang": "zh_CN",
    "f": "json",
    "ajax": "1"
}


def parse_and_save(json_data, csv_writer):
    """解析嵌套的 JSON 并写入 CSV"""
    try:
        # 第一层解析：publish_page
        publish_page_str = json_data.get("publish_page", "{}")
        publish_page_dict = json.loads(publish_page_str)

        # 第二层解析：publish_list
        publish_list = publish_page_dict.get("publish_list", [])

        if not publish_list:
            return False

        for item in publish_list:
            # 第三层解析：publish_info
            publish_info_str = item.get("publish_info", "{}")
            publish_info_dict = json.loads(publish_info_str)

            # 第四层解析：appmsgex (真正的文章列表)
            articles = publish_info_dict.get("appmsgex", [])

            for article in articles:
                title = article.get("title")
                link = article.get("link")
                # 转换时间戳
                ts = article.get("update_time")
                update_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

                print(f"[{update_time}] 抓取到: {title}")
                print(link)
                csv_writer.writerow([update_time, title, link])

        return True
    except Exception as e:
        print(f"解析出错: {e}")
        return False


def main():
    # 创建 CSV 文件
    with open('wechat_articles.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['发布时间', '文章标题', '文章链接'])

        begin = 0  # 起始页
        while True:
            params = BASE_PARAMS.copy()
            params["begin"] = str(begin)

            print(f"\n--- 正在请求 begin={begin} 的数据 ---")

            try:
                response = requests.get(URL, headers=HEADERS, cookies=COOKIES, params=params, timeout=10)

                # 检查是否触发频率限制
                if response.json().get("base_resp", {}).get("ret") == 200013:
                    print("!!! 触发频率限制，请停止脚本，稍后再试，或更换 Cookie !!!")
                    break

                # 解析并保存
                has_data = parse_and_save(response.json(), writer)

                if not has_data:
                    print("没有更多数据了，抓取结束。")
                    break

                # 翻页
                begin += 5

                # 随机休眠 5-10 秒，保护账号
                sleep_time = random.uniform(5, 10)
                print(f"休眠 {sleep_time:.2f} 秒...")
                time.sleep(sleep_time)

            except Exception as e:
                print(f"请求发生错误: {e}")
                break


if __name__ == "__main__":
    main()
