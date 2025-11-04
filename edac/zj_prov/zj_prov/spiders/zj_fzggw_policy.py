import copy
import re
from hashlib import md5
from loguru import logger
import scrapy
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class EitdznewsSpider(scrapy.Spider):
    name = "zj_fzggw_policy"
    allowed_domains = ["fzggw.zj.gov.cn"]

    _from = '浙江省发展和改革委员会'
    dupefilter_field = {"batch": "20240322"}

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
            'zj_prov.middlewares.EducationDownloaderMiddleware': None,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visited_urls = set()

    infoes = [
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1229565788/index.html?uid=4892867&pageNum=1',
            'label': "政策文件;行政规范性文件",
            'detail_xpath': '//*[@id="4892867"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@id="zoom" or contains(@class,"main-txt")]',
            'total': 26,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1229565788/index.html?uid=4892867&pageNum={}'
        },
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1229603564/index.html?uid=7468062&pageNum=1',
            'label': "政策文件;政策解读;规划解读",
            'detail_xpath': '//*[@id="7468062"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="main-txt" and @id="zoom"]',
            'total': 6,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1229603564/index.html?uid=7468062&pageNum={}'
        },
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1229603565/index.html?uid=7468062&pageNum=1',
            'label': "政策文件;政策解读;其他解读",
            'detail_xpath': '//*[@id="7468062"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="main-txt" and @id="zoom"]',
            'total': 6,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1229603565/index.html?uid=7468062&pageNum={}'
        },
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1599544/index.html?uid=4892867&pageNum=1',
            'label': "政策文件;通知公告",
            'detail_xpath': '//*[@id="4892867"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="main-txt" and @id="zoom"]',
            'total': 182,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1599544/index.html?uid=4892867&pageNum={}'
        },
    ]

    def start_requests(self):
        """起始请求"""
        for info in self.infoes:
            yield scrapy.Request(
                url=info.get('url'),
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=False
            )


    def parse_item(self, response):
        logger.info(f"页面URL: {response.url}")

        xml_text = ''.join(response.xpath('//script[@type="text/xml"]/text()').getall())
        html_blocks = []

        if xml_text:
            html_blocks = re.findall(r'<record><!\[CDATA\[(.*?)\]\]></record>', xml_text, flags=re.S)
            if not html_blocks:
                html_blocks = re.findall(r'<p class="lb-list">.*?</p>', xml_text, flags=re.S)
        else:
            logger.warning("未找到 <script type='text/xml'>，尝试直接解析HTML列表结构")
            html_blocks = response.xpath('//div[@id and contains(@class,"list")]/ul/li').getall()

        logger.info(f"匹配到 {len(html_blocks)} 条记录")

        for block in html_blocks:
            sel = scrapy.Selector(text=block)
            relative_url = sel.xpath('.//a/@href').get()
            if not relative_url:
                continue

            url = response.urljoin(relative_url)
            url = url.replace("http://", "https://")

            # ✅ 关键：全局唯一 URL 防重
            if url in self.visited_urls:
                logger.debug(f"重复URL跳过: {url}")
                continue
            self.visited_urls.add(url)

            title = sel.xpath('.//a/@title').get() or sel.xpath('.//a/text()').get()
            publish_time = sel.xpath('.//span/text()').get()

            meta = {
                'label': response.meta.get('label'),
                'title': title.strip() if title else '',
                'publish_time': publish_time.strip() if publish_time else '',
                'body_xpath': response.meta.get('body_xpath'),
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=False
            )

    def parse_detail(self, response):
        """解析详情页内容"""
        _meta = response.meta
        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.url

        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').get()
        publish_time = _meta.get('publish_time')
        body_xpath = _meta.get('body_xpath')

        author = (
            ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text))
            or ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        attachment_urls = response.xpath(
            f'{body_xpath}//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or contains(@href, ".wps")]'
        )

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            'spider_from': self._from,
            'label': _meta.get('label'),
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).getall()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').getall()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').getall()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            'spider_topic': "spider-policy-zhejiang"
        })
