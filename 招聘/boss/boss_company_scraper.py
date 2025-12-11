# -*- coding:utf-8 -*-

import requests
import time
import json
from datetime import datetime
import pandas as pd
from loguru import logger

TARGET_COMPANIES = [
    "中新社（北京）国际传播集团有限公司四川分公司",
    "成都利鑫互动科技有限公司",
    "成都黑焰联动科技有限公司",
    "成都灵枫科技有限公司",
    "成都赢挣科技有限公司",
    "四川顽偶星工场传媒有限公司",
    "成都方之影视制作有限公司",
    "成都艾末塔网络科技有限公司",
    "成都上岸互娱文化科技有限公司",
    "成都鲸顶文化传播有限公司",
    "成都入元睿科技有限公司",
    "成都硕云网络科技有限公司",
    "成都冰火无线科技有限公司",
    "成都火猴互动科技有限责任公司",
    "成都游点牛网络科技有限公司",
    "成都卓尔派科技有限公司",
    "四川聿梦文化科技有限公司",
    "成都吉米力科技有限公司",
    "成都零橙互娱科技有限公司",
    "重庆缘漫动漫设计有限公司",
    "重庆隐豹数字传媒有限公司",
    "重庆超梦动漫制作有限公司",
    "重庆赢挣动漫设计有限公司",
    "重庆创谷动漫设计有限公司",
    "四川省文化大数据有限责任公司"
]

# 你的抓包 headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 "
                  "MicroMessenger/7.0.20.1781(0x6700143B)",
    "mini_ver": "13.2200",
    "ua": '{"model":"microsoft","platform":"windows"}',
    "wt2": "",
    "zp_app_id": "10002",
    "content-type": "application/x-www-form-urlencoded",
    "traceid": "M-Wc804202tKil7ChhA",
    "mpt": "4a7ef6b7e729328608d0a7ce98396fd7",
    "scene": "1256",
    "xweb_xhr": "1",
    "x-requested-with": "XMLHttpRequest",
    "zp_product_id": "10002",
    "platform": "zhipin/windows",
    "ver": "13.2200",
    "referer": "https://servicewechat.com/wxa8da525af05281f3/587/page-frame.html",
    "accept-language": "zh-CN,zh;q=0.9"
}

CITY_CODES = ["101270100", "101040000"]  # 成都 + 重庆


def search_company(company_name):
    results = []

    for city_code in CITY_CODES:
        logger.info(f"开始搜索公司：{company_name} 城市：{city_code}")

        url = "https://www.zhipin.com/wapi/zpgeek/miniapp/search/joblist.json"

        params = {
            "pageSize": 15,
            "query": company_name,
            "city": city_code,
            "source": "1",
            "sortType": "0",
            "page": "1",
            "appId": "10002"
        }

        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            data = resp.json()
        except Exception as e:
            logger.error(f"请求失败：{e}")
            continue

        if data.get("code") != 0:
            logger.error(f"接口错误：{data.get('message')}")
            continue

        job_list = data.get("zpData", {}).get("list", [])

        for job in job_list:
            results.append({
                "company_search": company_name,
                "search_city_code": city_code,
                "company": job.get("brandName"),
                "job_name": job.get("jobName"),
                "salary": job.get("salaryDesc"),
                "exp": job.get("jobExperience"),
                "degree": job.get("jobDegree"),
                "city": job.get("cityName"),
                "district": job.get("districtName"),
                "boss": job.get("bossName"),
                "company_size": job.get("brandScale"),
                "job_labels": job.get("jobLabels"),
                "job_url": f"https://www.zhipin.com/job_detail/{job.get('encryptJobId')}.html",
                "spider_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

        time.sleep(1)

    return results


def run_once_and_save():
    all_rows = []

    for company in TARGET_COMPANIES:
        rows = search_company(company)
        all_rows.extend(rows)
        time.sleep(1)

    df = pd.DataFrame(all_rows)
    df.to_csv("boss_company_search.csv", index=False, encoding="utf-8-sig")

    with open("boss_company_search.json", "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    logger.success("已保存 boss_company_search.csv / boss_company_search.json")


if __name__ == "__main__":
    run_once_and_save()
