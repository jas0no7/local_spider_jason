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
    name = 'news_fgw_jiangsu'
    allowed_domains = ['fzggw.jiangsu.gov.cn']

    _from = '江苏省发展和改革委员会'
    dupefilter_field = {"batch": "20240322"}

    def start_requests(self):
        """
        启动时直接从接口分页抓取文章列表
        """
        base_url = "https://fzggw.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp"
        headers = {
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://fzggw.jiangsu.gov.cn",
            "Pragma": "no-cache",
            "Referer": "https://fzggw.jiangsu.gov.cn/col/col282/index.html?uid=423656&pageNum=1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

        cookies = {
            "JSESSIONID": "21530C2A382F886CF75A32063333943F",
            "4e592537-9abc-4c60-a2bb-cecd0f661748": 'WyIyNDcwODEzNDE5Il0',
            "__jsluid_s": "cccbcc5be814769ca76c51e8b6a2342e",
            "zh_choose_3": "s"
        }

        data_base = {
            "col": "1",
            "appid": "1",
            "webid": "3",
            "path": "/",
            "columnid": "282",
            "sourceContentType": "1",
            "unitid": "423656",
            "webname": "江苏省发展和改革委员会",
            "permissiontype": "0"
        }

        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(cookies)

        for page in range(1, 16):
            startrecord = (page - 1) * 10 + 1
            endrecord = page * 10
            params = {
                "startrecord": startrecord,
                "endrecord": endrecord,
                "perpage": "10"
            }

            resp = session.post(base_url, params=params, data=data_base, timeout=10)
            resp.encoding = "utf-8"
            blocks = re.findall(r'<!\[CDATA\[(.*?)\]\]>', resp.text, re.S)

            for block in blocks:
                html = etree.HTML(block)
                href = html.xpath('//a/@href')
                title = html.xpath('//a/@title')
                publish_time = html.xpath('//span/text()')

                href = f"https://fzggw.jiangsu.gov.cn{href[0]}" if href else None
                title = title[0].strip() if title else None
                publish_time = publish_time[0].strip() if publish_time else None

                if not href or not title:
                    continue

                meta = {
                    "label": "发改要闻",
                    "title": title,
                    "publish_time": publish_time,
                    "body_xpath": '//div[@class="bt-box-main bt-art-0001-D7 clearfix"]',
                }

                yield scrapy.Request(
                    url=href,
                    callback=self.parse_detail,
                    meta=copy.deepcopy(meta),
                    dont_filter=True
                )

    def parse_detail(self, response):
        """
        详情页解析
        """
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

        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                 ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()

        attachment_urls = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or '
            'contains(@href, ".docx") or contains(@href, ".xls") or '
            'contains(@href, ".xlsx") or contains(@href, ".zip") or '
            'contains(@href, ".rar")]'
        )

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            'spider_from': self._from,
            'label': _meta.get('label'),
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).extract()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').extract()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            'spider_topic': "spider-news-jiangsu"
        })
