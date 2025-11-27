import scrapy
import copy
import re
import datetime
from hashlib import md5
from loguru import logger
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_attachment, get_now_date

settings = get_project_settings()


class ZjsthjtSpider(scrapy.Spider):
    name = "policy_sthjt2_zhejiang"
    allowed_domains = ["sthjt.zj.gov.cn"]
    category = '政府网站'

    _from = "浙江省生态环境厅"

    custom_settings = {}

    infoes = [
        {
            "label": "上级文件",
            "divid": "div1229106886",
            "infotypeId": "B001A012",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "body_xpath": '//div[@class="content_body"]',
            "total": 6,
        },
        {
            "label": "国家法律法规",
            "divid": "div1229106886",
            "infotypeId": "B001A015",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "body_xpath": '//div[@class="content_body"]',
            "total": 3,
        },
        {
            "label": "地方性法规规章",
            "divid": "div1229106886",
            "infotypeId": "B001A013",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "body_xpath": '//*[@id="article"]',
            "total": 3,
        },
        {
            "label": "政府规章",
            "divid": "div1229106886",
            "infotypeId": "B001A014",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "body_xpath": '//*[@id="barrierfree_container"]/div[4]/div/div[2]',
            "total": 2,
        },
        {
            "label": "政策解读",
            "divid": "div1229106886",
            "infotypeId": "B001A011",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "body_xpath": '//div[@class="main"]',
            "total": 13,
        },
        {
            "label": "本机关其他政策文件",
            "divid": "div1229106886",
            "infotypeId": "B001AC001",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "body_xpath": '//div[@class="main"]',
            "total": 44,
        },
        {
            "label": "行政规范性文件",
            "divid": "div1229106886",
            "infotypeId": "B001G001",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "body_xpath": '//div[@class="main"]',
            "total": 10,
        },
    ]

    @staticmethod
    def detect_body_xpath(response):
        xps = [
            '//div[@class="content_body"]',
            '//div[@class="main"]',
            '//div[@class="article-content"]',
            '//div[@id="article"]',
            '//div[@class="wrapper_detail_text"]',
        ]
        for xp in xps:
            if response.xpath(xp):
                return xp
        return '//body'

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://sthjt.zj.gov.cn/module/xxgk/tree.jsp",
            "Origin": "https://sthjt.zj.gov.cn",
            "X-Requested-With": "XMLHttpRequest",
        }

        search_url = "https://sthjt.zj.gov.cn/module/xxgk/search.jsp"

        for info in self.infoes:
            for page in range(1, info["total"] + 1):

                formdata = {
                    "divid": info["divid"],
                    "infotypeId": info["infotypeId"],
                    "jdid": info["jdid"],
                    "area": "",
                    "unit": "",
                    "keyWord": "",
                    "sortfield": "compaltedate:0",
                    "currpage": str(page),
                    "requestUrl": info["requestUrl"],
                    "standardXxgk": "1",
                }

                yield scrapy.FormRequest(
                    url=search_url,
                    formdata=formdata,
                    headers=headers,
                    callback=self.parse_item,
                    meta=copy.deepcopy(info),
                    dont_filter=False,
                )

    def parse_item(self, response):
        logger.info(f"解析列表页: {response.url}")

        # 真实结构
        lis = response.xpath('//div[@class="zfxxgk_list_con"]/ul/li')

        for li in lis:
            a = li.xpath("./a")
            href = a.xpath("./@href").get()
            title = a.xpath("string(.)").get().strip()
            publish_time = li.xpath("./span/text()").get("")

            if not href:
                continue

            href = response.urljoin(href)

            detail_meta = {
                "label": response.meta.get("label"),
                "title": title,
                "publish_time": publish_time,
                "body_xpath": response.meta.get("body_xpath"),
            }

            yield scrapy.Request(
                url=href,
                callback=self.parse_detail,
                meta=copy.deepcopy(detail_meta),
                dont_filter=False,
            )

    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body_raw = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        title = meta.get("title") or response.xpath("//title/text()").get()
        publish_time = meta.get("publish_time")
        body_xpath = meta.get("body_xpath")

        if not body_xpath or not response.xpath(body_xpath):
            body_xpath = self.detect_body_xpath(response)

        author = (
            "".join(re.findall(r"来源[:：]\s*(.*?)<", response.text))
            or "".join(response.xpath("//meta[@name='Author']/@content").getall())
        ).strip()

        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or '
            f'contains(@href, ".doc") or contains(@href, ".docx") or '
            f'contains(@href, ".wps")]'
        )
        attachments = get_attachment(attachment_nodes, url, self._from)

        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        yield DataItem({
            "_id": md5(f"{method}{url}{body_raw}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": meta["label"],
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
