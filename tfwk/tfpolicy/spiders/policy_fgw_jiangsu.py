import copy
import re
import requests
from hashlib import md5
from lxml import etree

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()


class DataSpider(CrawlSpider):
    name = 'policy_fgw_jiangsu'
    allowed_domains = ['fzggw.jiangsu.gov.cn']

    _from = '江苏省发展和改革委员会'
    dupefilter_field = {"batch": "20241111"}

    # =============================
    # 启动逻辑：接口分页
    # =============================
    def start_requests(self):
        """
        调接口获取所有详情页 URL，再逐条 yield scrapy.Request
        """
        base_api = "https://fzggw.jiangsu.gov.cn/module/jslib/zcjd/right.jsp"

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://fzggw.jiangsu.gov.cn",
            "Pragma": "no-cache",
            "Referer": "https://fzggw.jiangsu.gov.cn/module/jslib/zcjd/zcjd.htm",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

        cookies = {
            "JSESSIONID": "21530C2A382F886CF75A32063333943F",
            "4e592537-9abc-4c60-a2bb-cecd0f661748": "WyIyNDcwODEzNDE5Il0",
            "__jsluid_s": "cccbcc5be814769ca76c51e8b6a2342e",
            "zh_choose_3": "s"
        }

        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(cookies)

        # 这里分页上限 333（总页数），如接口有变可调整
        for page in range(1, 334):
            data = {
                "name": "",
                "keytype": "",
                "year": "",
                "ztflid": "",
                "fwlbbm": "",
                "pageSize": "10",
                "pageNo": page
            }
            try:
                resp = session.post(base_api, data=data, timeout=10)
                resp.encoding = "utf-8"
                data_json = resp.json()
            except Exception as e:
                self.logger.warning(f"第 {page} 页请求失败：{e}")
                continue

            if data_json.get("result") != "true" or "data" not in data_json:
                self.logger.warning(f"第 {page} 页无有效数据：{data_json}")
                continue

            for item in data_json["data"]:
                detail_url = f"https://fzggw.jiangsu.gov.cn{item['url']}"
                title = item.get("vc_title")
                publish_time = item.get("c_deploytime")

                meta = {
                    "label": "政策解读",
                    "title": title,
                    "publish_time": publish_time,
                    "body_xpath": '//div[@class="bt-box-main bt-art-0001-D7 clearfix"]'
                }

                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_detail,
                    meta=copy.deepcopy(meta),
                    dont_filter=True
                )

    # =============================
    # 详情页解析
    # =============================
    def parse_detail(self, response):
        _meta = response.meta
        method = response.request.method
        try:
            body = response.request.body.decode('utf-8')
        except Exception:
            body = ''
        url = response.request.url

        body_xpath = _meta.get('body_xpath')
        title = _meta.get('title')
        publish_time = _meta.get('publish_time')

        # 抓正文内容
        content = ' '.join(response.xpath(f'{body_xpath}//text()').extract()).strip()

        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                 ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()

        # 附件识别
        attachment_urls = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or '
            'contains(@href, ".docx") or contains(@href, ".xls") or '
            'contains(@href, ".xlsx") or contains(@href, ".zip") or '
            'contains(@href, ".rar")]'
        )

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": _meta.get('label'),
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": ' '.join(response.xpath(body_xpath).extract()),
            "content": content,
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            "spider_topic": "spider-policy-jiangsu"
        })
