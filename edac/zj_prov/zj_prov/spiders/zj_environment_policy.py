import copy
import re
from hashlib import md5
from loguru import logger
import scrapy
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class EitdznewsSpider(scrapy.Spider):
    name = "zj_environment_policy"
    allowed_domains = ["sthjt.zj.gov.cn/"]

    _from = '浙江省生态环境厅'
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
            'url': 'https://sthjt.zj.gov.cn/col/col1229116546/index.html',
            'label': "政策文件及解读;上级文件",
            'detail_xpath': '//*[@id="div1229106886"]/table/tbody/tr/td/div/div[2]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './b',
            'body_xpath': '',
            'total': 6,
            'page': 1,
            'base_url': ''
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
                dont_filter=True
            )

    def parse_item(self, response):
        """解析列表页，提取详情链接、标题、发布时间"""
        logger.info("进入函数parse_item")
        print(response.text)
        _meta = response.meta
        label = _meta.get('label')
        detail_xpath = _meta.get('detail_xpath')
        url_xpath = _meta.get('url_xpath')
        title_xpath = _meta.get('title_xpath')
        publish_time_xpath = _meta.get('publish_time_xpath')
        body_xpath = _meta.get('body_xpath')
        total = _meta.get('total')
        page = _meta.get('page')
        base_url = _meta.get('base_url')

        # 遍历详情页链接
        for ex_url in response.xpath(detail_xpath):
            relative_url = ex_url.xpath(url_xpath).get()
            logger.info(f"relative_url是: {relative_url}")
            if not relative_url:
                logger.info("没有relative_url")
                continue

            # 自动补全完整 URL
            if relative_url.startswith('/'):
                url = f'https://jxt.zj.gov.cn{relative_url}'
            else:
                url = response.urljoin(relative_url)

            title = ''.join(ex_url.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(ex_url.xpath(publish_time_xpath).getall()).strip()

            print(f"[详情链接] {url}")

            meta = {
                'label': label,
                'title': title,
                'publish_time': publish_time,
                'body_xpath': body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

        if page < total:
            page += 1
            next_url = _meta.get('base_url').format(page)
            print(f"正在抓取第 {page} 页：{next_url}")

            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                meta=copy.deepcopy({
                    'label': label,
                    'detail_xpath': detail_xpath,
                    'url_xpath': url_xpath,
                    'title_xpath': title_xpath,
                    'publish_time_xpath': publish_time_xpath,
                    'body_xpath': body_xpath,
                    'total': total,
                    'page': page,
                    'base_url': base_url
                }),
                dont_filter=True
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
