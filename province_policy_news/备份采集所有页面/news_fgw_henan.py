import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()




class DataSpider(CrawlSpider):
    name = "news_fgw_henan"
    allowed_domains = ["fgw.henan.gov.cn"]

    _from = "河南省发展和改革委员会"

    dupefilter_field = {
        "batch": "20231227"
    }

    infoes = [
        {
            "url": "http://fgw.henan.gov.cn/xwzx/fgyw/index.html",
            "label": "发改要闻",
            "detail_xpath": "//div[@class='news-list']/ul/li",
            "url_xpath": "./a/@href",
            "title_xpath": "string(./a)",  # 修正标题
            "publish_time_xpath": "./span",
            "body_xpath": "//div[@class='content']",
            "total": 233,
            "page": 1,
            "base_url": "https://fgw.henan.gov.cn/xwzx/fgyw/index_{}.html"
        },
        {
            "url": "https://fgw.henan.gov.cn/xwzx/tzgg/ggtb/index.html",
            "label": "公告通报",
            "detail_xpath": "//div[@class='news-list']/ul/li",
            "url_xpath": "./a/@href",
            "title_xpath": "string(./a)",  # 修正标题
            "publish_time_xpath": "./span",
            "body_xpath": "//div[@class='content']",
            "total": 11,
            "page": 1,
            "base_url": "https://fgw.henan.gov.cn/xwzx/tzgg/ggtb/index_{}.html"
        }
    ]

    def start_requests(self):
        for info in self.infoes:
            url = info.get('url')
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    def parse_item(self, response):
        """
        详情和下一页url
        :param response:
        :return:
        """

        _meta = response.meta
        label = _meta.get('label')
        detail_xpath = _meta.get('detail_xpath')
        url_xpath = _meta.get('url_xpath')
        title_xpath = _meta.get('title_xpath')
        publish_time_xpath = _meta.get('publish_time_xpath')
        total = _meta.get('total')
        page = _meta.get('page')
        base_url = _meta.get('base_url')

        for ex_url in response.xpath(detail_xpath):
            url = response.urljoin(ex_url.xpath(url_xpath).extract_first())
            if url.endswith('.pdf'):
                continue

            title = ''.join(ex_url.xpath(title_xpath).extract())
            publish_time = ex_url.xpath(f'string({publish_time_xpath})').extract_first().replace('|', '').strip()

            meta = {
                "label": label,
                "title": title,
                'publish_time': publish_time,
            }
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta)
            )

        if page + 1 < total:
            page += 1
            yield scrapy.Request(
                url=f'{base_url.format(page)}',
                callback=self.parse_item,
                meta=copy.deepcopy({
                    'label': label,
                    'detail_xpath': detail_xpath,
                    'url_xpath': url_xpath,
                    'title_xpath': title_xpath,
                    'publish_time_xpath': publish_time_xpath,
                    'total': total,
                    'page': page,
                    'base_url': base_url,
                }),
            )

    def parse_detail(self, response):
        _meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ""
        url = response.url

        # --------------------------
        # ① 自动识别正文 XPath
        # --------------------------
        # 先尝试官方最常用结构
        body_xpath_list = [
            "//div[contains(@class,'article-content')]",
            "//div[contains(@class,'xl_con')]",
            "//div[contains(@class,'content')]",
            "//div[@id='content']",
            "//div[contains(@class,'newscontent')]",
        ]

        body_html = ""
        for xp in body_xpath_list:
            body_html = response.xpath(xp).get()
            if body_html:
                body_xpath = xp
                break
        else:
            body_xpath = "//body"  # 兜底不报错
            body_html = response.xpath(body_xpath).get()

        # 提取文本
        content = "".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        # --------------------------
        # ② 标题、时间、来源
        # --------------------------
        title = _meta.get("title") or response.xpath('//meta[@name="ArticleTitle"]/@content').get()

        publish_time = (
                _meta.get("publish_time")
                or "".join(response.xpath("//publishtime/text()").getall()).strip()
                or "".join(re.findall(r"(\d{4}-\d{2}-\d{2})", response.text))
        )

        author = (
                response.xpath('//meta[@name="author"]/@content').get()
                or response.xpath('//meta[@name="ContentSource"]/@content').get()
        )

        # --------------------------
        # ③ 附件
        # --------------------------
        attachment_urls = response.xpath(
            "//a[contains(@href,'.pdf') or contains(@href,'.doc') or contains(@href,'.docx') or "
            "contains(@href,'.xls') or contains(@href,'.xlsx') or contains(@href,'.zip') or "
            "contains(@href,'.rar')]"
        )

        # --------------------------
        # ④ 构建 item
        # --------------------------
        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode()).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": _meta.get("label"),
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html or "",
            "content": content or "",
            "images": [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").getall()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
        })

