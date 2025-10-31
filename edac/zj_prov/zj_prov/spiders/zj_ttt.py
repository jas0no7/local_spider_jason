import copy
import re
from hashlib import md5
import scrapy
from scrapy.crawler import CrawlerProcess


class ZjNyjSpider(scrapy.Spider):
    name = "zj_nyj_local"
    allowed_domains = ["zjb.nea.gov.cn"]

    _from = '国家能源局浙江监管办公室'

    infoes = [
        {
            'url': 'https://zjb.nea.gov.cn/xxgk/zcfg/',
            'label': "政策法规",
            'detail_xpath': '//div[@class="wrapper_item_content active_con"]/ul/li/a',
            'url_xpath': './@href',
            'title_xpath': './span[1]/text()',
            'publish_time_xpath': './span[2]/text()',
            'body_xpath': '//div[@class="channel-page"]',
            'total': 15,   # 可调小做测试
            'page': 1,
            'base_url': 'https://zjb.nea.gov.cn/xxgk/zcfg/index_{}.shtml'
        },
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
        """解析列表页"""
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

        for ex_url in response.xpath(detail_xpath):
            url = response.urljoin(ex_url.xpath(url_xpath).get())
            if not url:
                continue

            title = ''.join(ex_url.xpath(title_xpath).getall()).strip()
            publish_time = ''.join(ex_url.xpath(f'string({publish_time_xpath})').getall()).strip() if publish_time_xpath else None

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
            next_url = base_url.format(page)
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
                    'base_url': base_url,
                }),
                dont_filter=True
            )

    def parse_detail(self, response):
        """解析详情页"""
        _meta = response.meta
        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.url

        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').get()
        publish_time = _meta.get('publish_time')
        body_xpath = _meta.get('body_xpath')

        author = (
            ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text)) or
            ''.join(response.xpath('//meta[@name="Author"]/@content').getall())
        ).strip()

        content = ' '.join(response.xpath(f'{body_xpath}//text()').getall()).strip()

        print("\n===============================")
        print("Title:", title)
        print("Publish time:", publish_time)
        print("Author:", author)
        print("URL:", url)
        print("Content preview:", content, "..." if len(content) > 300 else "")
        print("===============================\n")


# 允许直接运行
if __name__ == "__main__":
    process = CrawlerProcess(settings={
        "LOG_LEVEL": "INFO",
        "DOWNLOAD_DELAY": 0.5,  # 防止被封
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    process.crawl(ZjNyjSpider)
    process.start()
