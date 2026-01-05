import copy
import re
from hashlib import md5
from urllib.parse import urljoin

import scrapy
from bs4 import BeautifulSoup


class MohrssPolicySpider(scrapy.Spider):
    name = "edu_policy_mohrss"
    allowed_domains = ["www.mohrss.gov.cn"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "COOKIES_ENABLED": True,
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index_1.html",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    }

    cookies = {
        "path": "/",
        "__tst_status": "1065405420#",
        "EO_Bot_Ssid": "1706819584",
        "turingcross": "%7B%22distinct_id%22%3A%2219b2b81aae2d97-07fb34b48a999f-26061a51-1440000-19b2b81aae31900%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219b2b81aae2d97-07fb34b48a999f-26061a51-1440000-19b2b81aae31900%22%7D",
        "Hm_lvt_64e46e3f389bd47c0981fa5e4b9f2405": "1765960189,1766462458",
        "HMACCOUNT": "87F8838732B4A041",
        "arialoadData": "false",
        "ariauseGraymode": "false",
        "Hm_lpvt_64e46e3f389bd47c0981fa5e4b9f2405": "1766481191"
    }

    infoes = [
        # {
        #     "url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index.html",
        #     "base_url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/jinengrencai/index{}.html",
        #     "label": "人才人事;政策文件;技能人才",
        #     "total": 8,
        #     "page": 1,
        #
        #     "detail_xpath": '//div[@class="organGeneralNewListConType"]',
        #     "url_xpath": './/span[@class="organMenuTxtLink"]/a/@href',
        #     "title_xpath": './/span[@class="organMenuTxtLink"]/a/text()',
        #     "publish_time_xpath": './/div[@class="organGeneralNewListTxtConTime"]//span/text()',
        #     "body_xpath": '//div[@class="clearboth"]',
        # },
        # {
        #     "url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/zhuanyejishurenyuan/index.html",
        #     "base_url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/rencairenshi/zcwj/zhuanyejishurenyuan/index{}.html",
        #     "label": "人才人事;政策文件;专业技术人才",
        #     "total": 19,
        #     "page": 1,
        #
        #     "detail_xpath": '//div[@class="organGeneralNewListConType"]',
        #     "url_xpath": './/span[@class="organMenuTxtLink"]/a/@href',
        #     "title_xpath": './/span[@class="organMenuTxtLink"]/a/text()',
        #     "publish_time_xpath": './/div[@class="organGeneralNewListTxtConTime"]//span/text()',
        #     "body_xpath": '//div[@class="clearboth"]',
        # },
        {
            'url': 'https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/qt/gztz/index.html',
            "base_url": "https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/qt/gztz/index_{}.html",
            'label': "通知公告;其他;工作通知",
            'detail_xpath': '//div[@id="wascontent"]/ul/li',
            'url_xpath': './div[contains(@class, "res_title")]/a/@href',
            'title_xpath': './div[contains(@class, "res_title")]/a/text()',
            'publish_time_xpath': 'substring(./div[contains(@class, "res_infos")]/span[@class="fr"]/text(), 6)',
            'total': 20,
            'page': 0,
            "body_xpath": '//div[@class="clearboth"]'
        },
        {
            'url': 'https://www.mohrss.gov.cn/SYrlzyhshbzb/zwgk/gggs/tg/index.html',
            "base_url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/zwgk/gggs/tg/index_{}.html",
            'label': "通知公告;公示",
            'detail_xpath': '//div[@class="serviceMainListConType"]/div[@class="serviceMainListTabCon"]',
            'url_xpath': './div[@class="serviceMainListTxt"]/span[@class="serviceMainListTxtLink"]/a/@href',
            'title_xpath': './div[@class="serviceMainListTxt"]/span[@class="serviceMainListTxtLink"]/a/@title',
            'publish_time_xpath': './div[@class="organGeneralNewListTxtConTime_a"]/span[@class="organMenuTxtLink"]/text()',
            'total': 8,
            'page': 0,
            "body_xpath": '//div[@class="insMainConTxt"]'
        },
        {
            'url': 'https://www.mohrss.gov.cn/SYrlzyhshbzb/dongtaixinwen/buneiyaowen/rsxw/index.html',
            "base_url": "https://www.mohrss.gov.cn/SYrlzyhshbzb/dongtaixinwen/buneiyaowen/rsxw/index_{}.html",
            'label': "资讯;人社新闻",
            'detail_xpath': '//div[@class="serviceMainListConType"]/div[@class="serviceMainListTabCon"]',
            'url_xpath': './div[@class="serviceMainListTxt"]/span[@class="serviceMainListTxtLink"]/a/@href',
            'title_xpath': './div[@class="serviceMainListTxt"]/span[@class="serviceMainListTxtLink"]/a/@title',
            'publish_time_xpath': './div[@class="organGeneralNewListTxtConTime_a"]/span[@class="organMenuTxtLink"]/text()',
            'total': 34,
            'page': 0,
            "body_xpath": '//div[@class="insMainConTxt"]'
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            yield scrapy.Request(
                url=info["url"],
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_list,
                meta=copy.deepcopy(info),
                dont_filter=True,
            )

    def parse_list(self, response):
        meta = response.meta

        nodes = response.xpath(meta["detail_xpath"])
        if not nodes:
            self.logger.warning(f"列表页未解析到数据: {response.url}")

        for node in nodes:
            href = node.xpath(meta["url_xpath"]).get()
            if not href:
                continue

            url = response.urljoin(href)
            title = node.xpath(meta["title_xpath"]).get()
            publish_time = node.xpath(meta["publish_time_xpath"]).get()

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta={
                    "label": meta["label"],
                    "title": title.strip() if title else "",
                    "publish_time": publish_time.strip() if publish_time else "",
                    "body_xpath": meta["body_xpath"],
                },
                dont_filter=True
            )

        # 翻页逻辑必须独立存在
        page = meta["page"]
        total = meta["total"]

        if page < total:
            next_page = page + 1
            new_meta = meta.copy()
            new_meta["page"] = next_page

            if next_page == 1:
                next_url = meta["base_url"].format("")
            else:
                next_url = meta["base_url"].format(f"_{next_page}")

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_list,
                meta=new_meta,
                dont_filter=True
            )

    def parse_detail(self, response):
        meta = response.meta
        soup = BeautifulSoup(response.text, "html.parser")

        body_div = soup.find("div", class_="clearboth")

        body_html = body_div.decode() if body_div else ""
        content = body_div.get_text(strip=True) if body_div else ""

        publish_time = meta.get("publish_time")
        if not publish_time:
            m = re.search(r"\d{4}-\d{2}-\d{2}", response.text)
            publish_time = m.group(0) if m else ""

        yield {
            "_id": md5((response.url + meta["title"]).encode("utf-8")).hexdigest(),
            "url": response.url,
            "title": meta["title"],
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "spider_from": "人力资源社会保障部",
            "label": meta["label"],
        }
