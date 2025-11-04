import copy
import re
from hashlib import md5
from loguru import logger
import scrapy
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class EitdznewsSpider(scrapy.Spider):
    name = "zj_fzggw_news"
    allowed_domains = ["fzggw.zj.gov.cn"]

    _from = '浙江省发展和改革委员会'
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
            'url': 'https://fzggw.zj.gov.cn/col/col1599562/index.html?uid=4892867&pageNum=1',
            'label': "新闻发布会;新闻发布会",
            'detail_xpath': '//*[@id="4892867"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@id="zoom" or contains(@class,"main-txt")]',
            'total': 9,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1599562/index.html?uid=4892867&pageNum={}'
        },
        {
            'url': 'https://fzggw.zj.gov.cn/col/col1229318206/index.html?uid=4892867&pageNum=1',
            'label': "新闻发布会;在线访谈",
            'detail_xpath': '//*[@id="7468062"]/div/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="main-txt" and @id="zoom"] | //*[@id="img-content"]',
            'total': 2,
            'page': 1,
            'base_url': 'https://fzggw.zj.gov.cn/col/col1229318206/index.html?uid=4892867&pageNum={}'
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

        xml_text = ''.join(response.xpath('//script[@type="text/xml"]/text()').getall())
        html_blocks = []

        if xml_text:
            # 新版结构：<record><![CDATA[<li>...</li>]]></record>
            html_blocks = re.findall(r'<record><!\[CDATA\[(.*?)\]\]></record>', xml_text, flags=re.S)
            # 旧版兼容
            if not html_blocks:
                html_blocks = re.findall(r'<p class="lb-list">.*?</p>', xml_text, flags=re.S)
        else:
            # fallback：直接HTML结构
            logger.warning("未找到 <script type='text/xml'>，尝试直接解析HTML列表结构")
            html_blocks = response.xpath('//div[@id and contains(@class,"list")]/ul/li').getall()

        logger.info(f"匹配到 {len(html_blocks)} 条记录")

        for block in html_blocks:
            sel = scrapy.Selector(text=block)
            relative_url = sel.xpath('.//a/@href').get()
            title = sel.xpath('.//a/@title').get() or sel.xpath('.//a/text()').get()
            publish_time = sel.xpath('.//span/text()').get()

            if not relative_url:
                continue

            url = response.urljoin(relative_url)
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

        # ======================
        # 翻页逻辑
        # ======================
        current_page = response.meta.get('page', 1)
        total_page = response.meta.get('total', 1)
        base_url = response.meta.get('base_url')

        if current_page < total_page:
            next_page = current_page + 1
            next_url = base_url.format(next_page)
            logger.info(f"翻页至第 {next_page} 页: {next_url}")

            next_meta = copy.deepcopy(response.meta)
            next_meta['page'] = next_page

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=next_meta,
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
            'spider_topic': "spider-news-zhejiang"
        })
