import copy
import scrapy
from hashlib import md5
import re
from loguru import logger
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class ZjsthjtSpider(scrapy.Spider):
    name = "zj_sthjt_policy"
    allowed_domains = ["sthjt.zj.gov.cn"]

    _from = "浙江省生态环境厅"

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
            'zj_prov.middlewares.EducationDownloaderMiddleware': None,
        }
    }

    infoes = [
        {
            "url": "https://sthjt.zj.gov.cn/module/xxgk/search.jsp",
            "label": "上级文件",
            "body_xpath": '//div[@class="content_body"]',
            "divid": "div1229106886",
            "infotypeId": "B001A012",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "total": 6,
        },
        {
            "url": "https://sthjt.zj.gov.cn/module/xxgk/search.jsp",
            "label": "国家法律法规",
            "body_xpath": '//div[@class="content_body"]',
            "divid": "div1229106886",
            "infotypeId": "B001A015",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "total": 3,
        },
        {
            "url": "https://sthjt.zj.gov.cn/module/xxgk/search.jsp",
            "label": "地方性法规规章",
            "body_xpath": '//*[@id="article"]',
            "divid": "div1229106886",
            "infotypeId": "B001A013",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "total": 3,
        },
        {
            "url": "https://sthjt.zj.gov.cn/module/xxgk/search.jsp",
            "label": "政府规章",
            "body_xpath": '//*[@id="barrierfree_container"]/div[4]/div/div[2]',
            "divid": "div1229106886",
            "infotypeId": "B001A014",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "total": 2,
        },
        {
            "url": "https://sthjt.zj.gov.cn/module/xxgk/search.jsp",
            "label": "政策解读",
            "body_xpath": '//div[@class="main"]',
            "divid": "div1229106886",
            "infotypeId": "B001A011",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "total": 13,
        },
        {
            "url": "https://sthjt.zj.gov.cn/module/xxgk/search.jsp",
            "label": "本机关其他政策文件",
            "body_xpath": '//div[@class="main"]',
            "divid": "div1229106886",
            "infotypeId": "B001AC001",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "total": 44,
        },
        {
            "url": "https://sthjt.zj.gov.cn/module/xxgk/search.jsp",
            "label": "行政规范性文件",
            "body_xpath": '//div[@class="main"]',
            "divid": "div1229106886",
            "infotypeId": "B001G001",
            "jdid": "1756",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "total": 10,
        },
    ]

    def start_requests(self):
        """起始请求"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Referer": "https://sthjt.zj.gov.cn/module/xxgk/tree.jsp?divid=div1229106886&area=&rootName=&standardXxgk=1",
            "Origin": "https://sthjt.zj.gov.cn",
            "X-Requested-With": "XMLHttpRequest",
        }

        for info in self.infoes:
            for page in range(1, info["total"] + 1):
                formdata = {
                    "divid": info["divid"],
                    "infotypeId": info["infotypeId"],
                    "jdid": info["jdid"],
                    "area": "",
                    "sortfield": "",
                    "requestUrl": info["requestUrl"],
                    "standardXxgk": "1",
                    "currpage": str(page),
                }
                yield scrapy.FormRequest(
                    url=info["url"],
                    formdata=formdata,
                    headers=headers,
                    callback=self.parse_item,
                    meta=copy.deepcopy(info),
                    dont_filter=True
                )

    def parse_item(self, response):
        """解析列表页：提取标题、链接、日期"""
        logger.info(f"解析页面: {response.url}")

        # 提取列表 li/a 结构
        for a in response.xpath('//div[@class="zfxxgk_zdgkc"]//ul/li/a'):
            title = a.xpath('./@title').get()
            href = a.xpath('./@href').get()
            publish_time = a.xpath('../b/text()').get()

            if not href:
                continue
            if href.startswith("/"):
                href = response.urljoin(href)

            logger.info(f"抓取链接: {href}")

            meta = {
                "label": response.meta.get("label"),
                "title": title.strip() if title else "",
                "publish_time": publish_time.strip() if publish_time else "",
                "body_xpath": response.meta.get("body_xpath"),
            }

            yield scrapy.Request(
                url=href,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=True,
            )

    def parse_detail(self, response):
        """解析详情页内容"""
        _meta = response.meta
        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        title = _meta.get("title") or response.xpath("//title/text()").get()
        publish_time = _meta.get("publish_time")
        body_xpath = _meta.get("body_xpath")

        author = (
            "".join(re.findall(r"来源[:：]\s*(.*?)<", response.text))
            or "".join(response.xpath("//meta[@name='Author']/@content").getall())
        ).strip()

        attachment_urls = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or contains(@href, ".wps")]'
        )

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": _meta.get("label"),
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": " ".join(response.xpath(body_xpath).getall()),
            "content": " ".join(response.xpath(f"{body_xpath}//text()").getall()),
            "images": [response.urljoin(i) for i in response.xpath(f"{body_xpath}//img/@src").getall()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            "spider_topic": "spider-policy-zhejiang"
        })
