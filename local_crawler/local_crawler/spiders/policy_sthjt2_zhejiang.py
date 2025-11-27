import scrapy
import copy
import re
import datetime
from hashlib import md5
from loguru import logger


class ZjsthjtSpider(scrapy.Spider):
    name = "policy_sthjt2_zhejiang"
    allowed_domains = ["sthjt.zj.gov.cn"]

    _from = "浙江省生态环境厅"

    # ⚠ 删除旧项目中不存在的中间件
    custom_settings = {}

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

    # ---------- 工具函数 ----------
    @staticmethod
    def get_now_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_attachment(a_nodes, page_url):
        urls = []
        for a in a_nodes:
            href = a.xpath("./@href").get()
            if not href:
                continue
            if href.startswith("http"):
                urls.append(href)
            else:
                base = page_url.rsplit("/", 1)[0]
                urls.append(base + "/" + href.lstrip("/"))
        return urls

    # ---------- 起始请求 ----------
    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://sthjt.zj.gov.cn/module/xxgk/tree.jsp",
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
                    dont_filter=False,
                )

    # ---------- 列表页 ----------
    def parse_item(self, response):
        logger.info(f"解析页面: {response.url}")

        # li/a 列表项
        for a in response.xpath('//div[@class="zfxxgk_zdgkc"]//ul/li/a'):

            title = a.xpath("./@title").get()
            href = a.xpath("./@href").get()
            publish_time = a.xpath("../b/text()").get()

            if not href:
                continue

            href = response.urljoin(href)

            detail_meta = {
                "label": response.meta.get("label"),
                "title": title.strip() if title else "",
                "publish_time": publish_time.strip() if publish_time else "",
                "body_xpath": response.meta.get("body_xpath"),
            }

            yield scrapy.Request(
                url=href,
                callback=self.parse_detail,
                meta=copy.deepcopy(detail_meta),
                dont_filter=False,
            )

    # ---------- 自动识别正文 ----------
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

    # ---------- 详情页 ----------
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body_raw = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.url

        title = meta.get("title") or response.xpath("//title/text()").get()
        publish_time = meta.get("publish_time")
        body_xpath = meta.get("body_xpath")

        # 自动补充 body_xpath
        if not body_xpath or not response.xpath(body_xpath):
            body_xpath = self.detect_body_xpath(response)

        author = (
                "".join(re.findall(r"来源[:：]\s*(.*?)<", response.text))
                or "".join(response.xpath("//meta[@name='Author']/@content").getall())
        ).strip()

        # 附件
        attachment_nodes = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or '
            f'contains(@href, ".doc") or contains(@href, ".docx") or '
            f'contains(@href, ".wps")]'
        )
        attachments = self.get_attachment(attachment_nodes, url)

        body_html = " ".join(response.xpath(body_xpath).getall())
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()
        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        yield {
            "_id": md5(f"{method}{url}{body_raw}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_from": self._from,
            "label": meta["label"],
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": self.get_now_date(),

        }
