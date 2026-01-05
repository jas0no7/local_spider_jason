import json
import re
from hashlib import md5
import time
import scrapy
from scrapy.spiders import Spider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()


class DataSpider(Spider):
    name = "policy_zhejiangfagai"
    allowed_domains = ["mp.weixin.qq.com"]

    _from = "浙江发改"
    category = "政策"
    dupefilter_field = {"batch": "20240322"}

    LIST_URL = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"

    HEADERS_LIST = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=8&token=237409963&lang=zh_CN",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
        "x-requested-with": "XMLHttpRequest",
    }
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
        "_clsk": "1hhcnx6|1767508833730|4|1|mp.weixin.qq.com/weheat-agent/payload/record",
    }

    BASE_PARAMS = {
        "sub": "list",
        "search_field": "null",
        "count": "5",
        "query": "",
        "fakeid": "MzU5NTEzODg0NQ==",
        "type": "101_1",
        "free_publish_type": "1",
        "sub_action": "list_ex",
        "token": "237409963",
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
    }

    DETAIL_HEADERS = {
        "user-agent": HEADERS_LIST["user-agent"],
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "zh-CN,zh;q=0.9",
        "referer": "https://mp.weixin.qq.com/",
    }

    custom_settings = {
        # 你也可以放到全局 settings.py
        "DOWNLOAD_TIMEOUT": 25,
        "RETRY_TIMES": 6,
        "DOWNLOAD_DELAY": 1.2,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS": 4,
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        begin = 0
        params = dict(self.BASE_PARAMS)
        params["begin"] = str(begin)

        yield scrapy.Request(
            url=self.LIST_URL,
            method="GET",
            headers=self.HEADERS_LIST,
            cookies=self.COOKIES,
            cb_kwargs={"begin": begin, "count": int(self.BASE_PARAMS["count"])},
            meta={"params": params},
            dont_filter=True,
            callback=self.parse_list,
        )

    KEYWORD_IN_TITLE = "数说发改"

    def parse_list(self, response, begin, count):
        if "begin=" not in response.url:
            params = response.meta.get("params") or {}
            qs = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.LIST_URL}?{qs}"
            yield scrapy.Request(
                url=url,
                method="GET",
                headers=self.HEADERS_LIST,
                cookies=self.COOKIES,
                cb_kwargs={"begin": begin, "count": count},
                dont_filter=True,
                callback=self.parse_list,
            )
            return

        data = json.loads(response.text)

        if data.get("base_resp", {}).get("ret") == 200013:
            self.logger.warning("触发频率限制(ret=200013)，停止爬取。")
            return

        publish_page_str = data.get("publish_page", "{}")
        publish_page = json.loads(publish_page_str)
        publish_list = publish_page.get("publish_list", [])
        if not publish_list:
            self.logger.info("没有更多数据，结束。")
            return

        total = 0
        kept = 0

        for item in publish_list:
            publish_info_str = item.get("publish_info", "{}")
            publish_info = json.loads(publish_info_str)
            articles = publish_info.get("appmsgex", [])

            for a in articles:
                total += 1
                title = a.get("title") or ""
                link = a.get("link") or ""
                ts = a.get("update_time")
                publish_time = (
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else None
                )

                # ✅ 只保留标题包含关键词
                if self.KEYWORD_IN_TITLE not in title:
                    continue

                kept += 1
                yield scrapy.Request(
                    url=link,
                    headers=self.DETAIL_HEADERS,
                    callback=self.parse_detail,
                    cb_kwargs={
                        "fallback_title": title,
                        "fallback_publish_time": publish_time,
                    },
                    dont_filter=True,
                )

        next_begin = begin + count
        params = dict(self.BASE_PARAMS)
        params["begin"] = str(next_begin)
        next_qs = "&".join([f"{k}={v}" for k, v in params.items()])
        next_url = f"{self.LIST_URL}?{next_qs}"

        self.logger.info(
            f"begin={begin} 本页总数={total}，命中关键词={kept}，翻页到 begin={next_begin}"
        )
        yield scrapy.Request(
            url=next_url,
            method="GET",
            headers=self.HEADERS_LIST,
            cookies=self.COOKIES,
            cb_kwargs={"begin": next_begin, "count": count},
            dont_filter=True,
            callback=self.parse_list,
        )

    def parse_detail(self, response, fallback_title, fallback_publish_time):
        method = response.request.method
        body_req = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        og_title = response.css('meta[property="og:title"]::attr(content)').get()
        title = (og_title or fallback_title or "").strip()

        # ✅ 二次校验：最终标题不含关键词直接丢弃
        if self.KEYWORD_IN_TITLE not in title:
            return

        publish_time = (response.css("#publish_time::text").get() or "").strip()
        if not publish_time:
            publish_time = fallback_publish_time

        label = self.category

        js = response.css("#js_content")
        body_inner_html = "".join(js.xpath("./node()").getall())
        content = "\n".join([t.strip() for t in js.xpath(".//text()").getall() if t.strip()])

        imgs = js.xpath(
            ".//img/@data-croporisrc | .//img/@data-src | .//img/@data-original | .//img/@src"
        ).getall()
        seen, images = set(), []
        for u in imgs:
            u = (u or "").strip()
            if u and u not in seen:
                seen.add(u)
                images.append(u)

        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )
        attachments = get_attachment(attachment_urls, url, self._from)

        yield DataItem({
            "_id": md5(f"{method}{url}{body_req}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": label,
            "title": title,
            "author": "",
            "publish_time": publish_time,
            "body_html": body_inner_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
