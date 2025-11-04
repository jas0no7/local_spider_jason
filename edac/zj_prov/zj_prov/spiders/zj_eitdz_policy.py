import copy
import re
from hashlib import md5
from loguru import logger
import scrapy
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class EitdznewsSpider(scrapy.Spider):
    name = "zj_eitdz_policy"
    allowed_domains = ["jxt.zj.gov.cn"]

    _from = '浙江省经济和信息化厅'
    dupefilter_field = {
        "batch": "20240322"
    }
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
            'zj_prov.middlewares.EducationDownloaderMiddleware': None,
        }
    }

    infoes = [
        {
            'url': 'https://jxt.zj.gov.cn/col/col1229895084/index.html?uid=5024951&pageNum=1',
            'label': "统计分析;统计信息",
            'detail_xpath': '//*[@id="5024951"]/div/p',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="bt-box-1170 c1"] | //div[@class="wrapper_detail_text"] | //div[@class="article-content"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://jxt.zj.gov.cn/col/col1229895084/index.html?uid=5024951&pageNum={}'
        },
        {
            'url': 'https://jxt.zj.gov.cn/col/col1229895085/index.html?uid=5024951&pageNum=1',
            'label': "统计分析;监测分析",
            'detail_xpath': '//*[@id="5024951"]/div/p',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="bt-box-1170 c1"] | //div[@class="wrapper_detail_text"] | //div[@class="article-content"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://jxt.zj.gov.cn/col/col1229895085/index.html?uid=5024951&pageNum={}'
        },

    ]

    def start_requests(self):
        """起始请求"""
        for info in self.infoes:
            url = info.get('url')
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                meta=copy.deepcopy(info),
                dont_filter=False
            )

    def parse_item(self, response):
        """解析列表页"""
        logger.info(f"页面URL: {response.url}")

        # 1. 取出包裹在 <script type="text/xml"> 里的内容
        xml_text = ''.join(response.xpath('//script[@type="text/xml"]/text()').getall())
        if not xml_text:
            logger.warning("未找到 <script type='text/xml'> 内容")
            return

        # 2. 提取所有 <p class="lb-list"> 段落
        html_blocks = re.findall(r'<p class="lb-list">.*?</p>', xml_text, flags=re.S)

        logger.info(f"匹配到 {len(html_blocks)} 条记录")

        for block in html_blocks:
            sel = scrapy.Selector(text=block)
            relative_url = sel.xpath('//a/@href').get()
            title = sel.xpath('//a/text()').get()
            publish_time = sel.xpath('//span/text()').get()

            if not relative_url:
                continue

            # 3. 自动补全 URL
            if relative_url.startswith('/'):
                url = f'https://jxt.zj.gov.cn{relative_url}'
            else:
                url = relative_url

            logger.info(f"抓取链接: {url}")

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

        # 提取作者信息（来源）
        author = (
                ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
                ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        # 提取附件
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
