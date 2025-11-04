import copy
import json
import re
from hashlib import md5
from loguru import logger
import scrapy
from lxml import etree
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class EitdznewsSpider(scrapy.Spider):
    name = "hb_economicinfo_policy"
    allowed_domains = ["jxt.hubei.gov.cn"]

    _from = "湖北省经济信息化厅"

    dupefilter_field = {"batch": "20240322"}

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
            'zj_prov.middlewares.EducationDownloaderMiddleware': None,
        }
    }

    def start_requests(self):
        """入口：请求 JSON 列表接口"""
        url = "https://jxt.hubei.gov.cn/fbjd/zc/gfxwj/zcwj.json"
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Referer": "https://jxt.hubei.gov.cn/fbjd/zc/gfxwj/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }
        cookies = {
            "_trs_uv": "mhkcqgt2_2997_6ior",
            "_trs_ua_s_1": "mhkcqgt2_2997_2nn9",
            "_trs_gv": "g_mhkcqgt2_2997_6ior",
            "dataHide2": "256a69aa-1bbb-44de-b1af-a4f627d4170a",
            "Hm_lvt_b6564ffd7a04bf8cb06eea91adfbce21": "1762247644",
            "HMACCOUNT": "8F1962303CCAC654",
            "Hm_lpvt_b6564ffd7a04bf8cb06eea91adfbce21": "1762248078"
        }

        yield scrapy.Request(
            url=url,
            headers=headers,
            cookies=cookies,
            callback=self.parse_item,
            dont_filter=True
        )

    def parse_item(self, response):
        """解析 JSON 列表并调度详情页"""
        data = json.loads(response.text)
        items = data.get("data", [])

        for item in items:
            meta = {
                "IdxID": item.get("IdxID", ""),
                "URL": item.get("URL", ""),
                "FILENAME": item.get("FILENAME", ""),
                "FILENUM": item.get("FILENUM", ""),
                "PUBLISHER": item.get("PUBLISHER", ""),
                "PUBDATE": item.get("PUBDATE", ""),
            }

            detail_url = item.get("URL")
            if not detail_url:
                continue

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta=meta,
                dont_filter=False
            )

    def parse_detail(self, response):
        """解析详情页正文并产出 DataItem"""
        meta = response.meta
        body_xpath = '//div[@class="article"]'

        title = meta.get("FILENAME") or response.xpath('//title/text()').get("")
        publish_time = meta.get("PUBDATE", "")
        author = meta.get("PUBLISHER", "")
        url = meta.get("URL", "")
        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        attachment_urls = response.xpath(f"{body_xpath}//a/@href").getall()

        yield DataItem({
            "_id": md5(f"{url}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": "政策文件",
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").getall()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            "spider_topic": "spider-policy-hubei"
        })
