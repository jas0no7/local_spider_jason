import copy
import re
from hashlib import md5
from loguru import logger
import scrapy
from scrapy.spiders import CrawlSpider


def get_now_date():
    """简单替代函数：返回当前时间字符串"""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_attachment(attachment_nodes, base_url, spider_from):
    """简单替代函数：解析附件链接"""
    files = []
    for a in attachment_nodes:
        href = a.xpath("./@href").get()
        if href:
            files.append({
                "url": a.root.base_url.rstrip("/") + "/" + href.lstrip("/"),
                "name": (a.xpath("text()").get() or "").strip(),
                "from": spider_from
            })
    return files


class DataSpider(CrawlSpider):
    name = 'example'
    allowed_domains = ['gxt.jiangsu.gov.cn']

    _from = '示例'

    # 只保留你的配置，不做修改   //div[@class="default_pgContainer"]/ul/li/a/@title
    infoes = [
        {
            'url': 'https://gxt.jiangsu.gov.cn/col/col80181/index.html?uid=403740&pageNum=1',
            'label': "价格政策",
            'detail_xpath': '//div[@class="default_pgContainer"]/ul/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './b',
            'body_xpath': '//*[@id="Zoom"]',
            'total': 9,
            'page': 1,
            'base_url': 'https://gxt.jiangsu.gov.cn/col/col80181/index.html?uid=403740&pageNum={}'
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
        """列表页"""
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
            if url.endswith('.pdf'):
                continue

            title = ''.join(ex_url.xpath(title_xpath).getall())
            if publish_time_xpath:
                publish_time = ''.join(ex_url.xpath(f'string({publish_time_xpath})').getall()).replace('(', '').replace(')', '').strip()
            else:
                publish_time = None

            meta = {
                "label": label,
                "title": title,
                'publish_time': publish_time,
                'body_xpath': body_xpath,
            }
            print("+++++++++++++++++++++++++++++++++",meta)

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

        # 下一页
        if page < total:
            page += 1
            if page == 1:
                next_url = _meta['url']
            else:
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
        """详情页"""
        logger.info("进入详情页")
        _meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8') if response.request.body else ''
        url = response.request.url
        logger.info(f"详情页的url为{url}")

        body_xpath = _meta.get('body_xpath')
        title = _meta.get('title') or response.xpath('//meta[@name="ArticleTitle"]/@content').get()

        publish_time = _meta.get('publish_time') or \
                       ''.join(response.xpath('//publishtime/text()').getall()).strip() or \
                       ''.join(re.findall(r'发布日期.*?(\d{4}-\d{2}-\d{2})', response.text, re.DOTALL)).strip()

        author = response.xpath('//meta[@name="Author"]/@content').get() or \
                 ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span></li>', response.text, re.DOTALL)).strip() or \
                 ''.join(re.findall(r'>信息来源：(.*?)</', response.text, re.DOTALL)).strip()

        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        # 构造 item 内容（但我们不保存，只打印）
        item = {
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
            "spider_date": get_now_date()
        }

        # 输出到控制台
        print("\n==================== ITEM ====================")
        for k, v in item.items():
            print(f"{k}: {v}")
        print("==============================================\n")

        yield item  # scrapy 调试时也可以 yield，但不会存储
