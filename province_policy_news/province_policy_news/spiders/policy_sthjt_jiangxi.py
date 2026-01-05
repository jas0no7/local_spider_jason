import json
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()


class DataSpider(CrawlSpider):
    name = 'policy_sthjt_jiangxi'
    allowed_domains = ['sthjt.jiangxi.gov.cn']

    _from = '江西生态环境厅'
    category = "政策"

    dupefilter_field = {
        "batch": "20240322"
    }

    list_api = "https://sthjt.jiangxi.gov.cn/queryList"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://sthjt.jiangxi.gov.cn",
        "Pragma": "no-cache",
        "Referer": "https://sthjt.jiangxi.gov.cn/jxssthjt/col/col42150/index.html?uid=380055&pageNum=2",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "cookie": "ariauseGraymode=false; arialoadData=false"
    }

    # --------------------------------------
    # 新增：多栏目统一入口
    # --------------------------------------
    infoes = [
        {"page_start": 1, "page_end": 30, "channelCode[]": "col42150", "label": "政策法规框解读"},
        {"page_start": 1, "page_end": 3,  "channelCode[]": "col57149", "label": "规范性文件"},
    ]

    # --------------------------------------
    # start_requests 支持多栏目多页
    # --------------------------------------
    def start_requests(self):
        """
        起始请求：多个栏目分别翻页
        """

        for info in self.infoes:

            channel = info["channelCode[]"]
            label = info["label"]
            page_start = info["page_start"]
            page_end = info["page_end"]

            for page in [1]:
                formdata = {
                    "current": str(page),
                    "unitid": "380055",
                    "webSiteCode[]": "jxssthjt",
                    "channelCode[]": channel,
                    "dataBefore": "",
                    "dataAfter": "",
                    "perPage": "15",
                    "notReturnContent": "false",
                    "showMode": "normal",
                    "groupSize": "1",
                    "barPosition": "bottom",
                    "titleMax": "34",
                    "templateContainerId": "div380055",
                    "themeName": "lucidity",
                    "pageSize": "15"
                }

                yield scrapy.FormRequest(
                    url=self.list_api,
                    method="POST",
                    headers=self.headers,
                    formdata=formdata,
                    callback=self.parse_list,
                    dont_filter=True,
                    meta={
                        "page": page,
                        "channel": channel,
                        "label": label
                    }
                )

    # --------------------------------------
    # 列表解析
    # --------------------------------------
    def parse_list(self, response):
        page = response.meta["page"]
        label = response.meta["label"]

        try:
            j = json.loads(response.text)
        except Exception as e:
            self.logger.error(f"列表页 JSON 解析失败 page={page}: {e}")
            return

        results = j.get("data", {}).get("results", [])
        self.logger.info(f"[{label}] 第 {page} 页解析到 {len(results)} 条数据")

        for item in results:
            src = item.get("source", {})

            title = (src.get("title") or "").strip()
            pub_date = (src.get("pubDate") or "").strip()

            urls_json = src.get("urls", "{}")
            try:
                urls_dict = json.loads(urls_json)
            except:
                urls_dict = {}

            pc_url = urls_dict.get("pc", "") or ""
            if pc_url.startswith("/"):
                pc_url = "https://sthjt.jiangxi.gov.cn" + pc_url

            if not pc_url:
                continue

            meta = {
                "title": title,
                "publish_time": pub_date,
                "label": label,   # <== 区分栏目
                "body_xpath": '//script[@type="text/javascript"]//text()'
            }

            self.logger.debug(f"[{label}] 详情页: {pc_url}")

            yield scrapy.Request(
                url=pc_url,
                headers=self.headers,
                callback=self.parse_detail,
                meta=meta
            )

    # --------------------------------------
    # 详情解析（原样保留你的逻辑）
    # --------------------------------------
    def parse_detail(self, response):
        _meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url

        body_xpath = _meta.get('body_xpath') or '//body'
        title = _meta.get('title')
        publish_time = (
            _meta.get('publish_time') or
            ''.join(response.xpath('//publishtime/text()').getall()).strip() or
            ''.join(re.findall(r'发布日期.*?(\d{4}-\d{2}-\d{2})', response.text, re.DOTALL)).strip()
        )
        label = _meta.get('label')

        author = (
            response.xpath('//meta[@name="Author"]/@content').get() or
            ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span></li>', response.text, re.DOTALL)).strip() or
            ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()
        )

        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        images = [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').getall()]
        attachments = get_attachment(attachment_urls, url, self._from)

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": label,                # <=== 已支持多个栏目
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": ' '.join(response.xpath(body_xpath).getall()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').getall()),
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
