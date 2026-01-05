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
    name = 'policy_fgw_jiangxi'
    allowed_domains = ['drc.jiangxi.gov.cn']

    _from = '江西发改委'
    category = "政策"

    dupefilter_field = {
        "batch": "20240322"
    }

    list_api = "https://drc.jiangxi.gov.cn/queryList"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://drc.jiangxi.gov.cn",
        "Pragma": "no-cache",
        "Referer": "https://drc.jiangxi.gov.cn/jxsfzhggwyh/col/col14590/index.html?uid=522756&pageNum=1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    cookies = {
        "arialoadData": "false",
        "zh_choose_undefined": "s",
        "ariauseGraymode": "false"
    }

    # 多栏目配置
    infoes = [
        {"page_start": 1, "page_end": 106, "channelCode[]": "col14590", "label": "通知公告"},
        {"page_start": 1, "page_end": 131, "channelCode[]": "col14636", "label": "价格监测"},
        {"page_start": 1, "page_end": 8,   "channelCode[]": "col14637", "label": "居民消费价格指数"},
    ]

    # ===============================================================
    # 1) Scrapy 的入口：start_requests
    # ===============================================================
    def start_requests(self):

        for info in self.infoes:
            channel = info["channelCode[]"]
            label = info["label"]

            for page in [1]:

                formdata = {
                    "current": str(page),
                    "unitid": "522756",
                    "webSiteCode[]": "jxsfzhggwyh",
                    "channelCode[]": channel,
                    "dataBefore": "",
                    "dataAfter": "",
                    "perPage": "15",
                    "showMode": "full",
                    "groupSize": "1",
                    "barPosition": "bottom",
                    "titleMax": "39",
                    "templateContainerId": "div522756",
                    "themeName": "default",
                    "pageSize": "15"
                }

                yield scrapy.FormRequest(
                    url=self.list_api,
                    method="POST",
                    headers=self.headers,
                    cookies=self.cookies,
                    formdata=formdata,
                    callback=self.parse_list,
                    meta={"label": label, "channel": channel, "page": page},
                    dont_filter=True
                )

    # ===============================================================
    # 2) 解析列表页 JSON
    # ===============================================================
    def parse_list(self, response):

        label = response.meta["label"]
        channel = response.meta["channel"]
        page = response.meta["page"]

        j = response.json()
        results = j.get("data", {}).get("results", [])
        self.logger.info(f"[{label}] 第 {page} 页解析 {len(results)} 条")

        for res in results:

            src = res.get("source", {})

            title = (src.get("title") or "").strip()
            pub_date = (src.get("pubDate") or "").strip()

            # ========= images ==========
            images_raw = src.get("images", "")
            images_list = []

            if isinstance(images_raw, str) and images_raw.strip():
                try:
                    img_metas = json.loads(images_raw)
                    if isinstance(img_metas, dict):
                        img_metas = [img_metas]

                    for m in img_metas:
                        if not isinstance(m, dict):
                            continue

                        domain = (m.get("domainName") or "").rstrip("/")
                        path = m.get("cover") or m.get("filePath") or ""

                        if path:
                            if not path.startswith("http"):
                                full = domain + path
                            else:
                                full = path
                            images_list.append(full)
                except:
                    pass

            # ========= urls（详情页）==========
            urls_str = src.get("urls", "{}")
            try:
                urls_dict = json.loads(urls_str)
            except:
                urls_dict = {}

            pc_url = urls_dict.get("pc", "")
            if pc_url.startswith("/"):
                pc_url = "https://drc.jiangxi.gov.cn" + pc_url

            # ========= content ==========
            raw_content = src.get("content", "")
            if isinstance(raw_content, str):
                content = raw_content.strip()
            else:
                content = json.dumps(raw_content, ensure_ascii=False)

            # 传递给 parse_detail
            meta = {
                "title": title,
                "publish_time": pub_date,
                "label": label,
                "images_raw": images_list,   # <<< 列表页返回的图片
                "body_xpath": '//body',      # 这个页面几乎都是 JS 输出内容
            }

            yield scrapy.Request(
                url=pc_url,
                headers=self.headers,
                cookies=self.cookies,
                callback=self.parse_detail,
                meta=meta
            )

    # ===============================================================
    # 3) 解析详情页（保持你的工程风格）
    # ===============================================================
    def parse_detail(self, response):
        _meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url

        title = _meta.get("title")
        publish_time = _meta.get("publish_time")
        label = _meta.get("label")

        body_xpath = _meta.get("body_xpath")
        images_raw = _meta.get("images_raw", [])

        # 详情页作者
        author = (
            response.xpath('//meta[@name="Author"]/@content').get() or
            ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span></li>', response.text, re.DOTALL)).strip() or
            ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()
        )

        # 附件
        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        # 详情页图片
        detail_images = [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').getall()]

        # 合并：列表页图片 + 详情页图片
        all_images = list(set(images_raw + detail_images))

        attachments = get_attachment(attachment_urls, url, self._from)

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": label,
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": ' '.join(response.xpath(body_xpath).getall()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').getall()),
            "images": all_images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
