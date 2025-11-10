import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from edac.tfwk.tfpolicy.mydefine import get_now_date, get_attachment

settings = get_project_settings()

policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')


class DataSpider(CrawlSpider):
    name = 'policy_scsdsjzx'
    allowed_domains = [
        'www.scdsjzx.cn'
    ]

    _from = '四川省大数据中心'
    dupefilter_field = {
        "batch": "20240322"
    }

    infoes = [
        {
            'url': 'https://www.scdsjzx.cn/scdsjzx/zhengcewenjian/xingxigongkai_list.shtml',
            'label': "首页;信息公开;政策文件",
            'detail_xpath': '//div[@class="title"]/a',
            'url_xpath': './@href',
            'title_xpath': '',
            'publish_time_xpath': '',
            'body_xpath': '//div[@class="art_detail_body"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://sthjt.sc.gov.cn/sthjt/c23101801/xzgfxwj_{}.shtml'
        },
        {
            'url': 'https://www.scdsjzx.cn/scdsjzx/guifanxingwenjian/xingxigongkai_list.shtml',
            'label': "首页;信息公开;相关文件",
            'detail_xpath': '//div[@class="title"]/a',
            'url_xpath': './@href',
            'title_xpath': '',
            'publish_time_xpath': '',
            'body_xpath': '//div[@class="art_detail_body"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://sthjt.sc.gov.cn/sthjt/c23101802/qtwj_{}.shtml'
        },
        {
            'url': 'https://www.scdsjzx.cn/scdsjzx/guojiazhengce/zhengcefagui.shtml',
            'label': "首页;数字法规;国家政策",
            'detail_xpath': '//div[@class="rows"]/div/a',
            'url_xpath': './@href',
            'title_xpath': './span[@class="title"]/text()',
            'publish_time_xpath': './span[@class="time"]/text()',
            'body_xpath': '//div[@class="art_detail_body"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://www.scdsjzx.cn/scdsjzx/guojiazhengce/zhengcefagui_{}.shtml'
        },
        {
            'url': 'https://www.scdsjzx.cn/scdsjzx/shengsczc/zhengcefagui.shtml',
            'label': "首页;数字法规;四川政策;省级政策文件",
            'detail_xpath': '//div[@class="rows"]/div/a',
            'url_xpath': './@href',
            'title_xpath': './span[@class="title"]/text()',
            'publish_time_xpath': './span[@class="time"]/text()',
            'body_xpath': '//div[@class="art_detail_body"]',
            'total': 2,
            'page': 1,
            'base_url': 'https://www.scdsjzx.cn/scdsjzx/shengsczc/zhengcefagui_{}.shtml'
        },
        {
            'url': 'https://www.scdsjzx.cn/scdsjzx/busczc/zhengcefagui.shtml',
            'label': "首页;数字法规;四川政策;部门政策文件",
            'detail_xpath': '//div[@class="rows"]/div/a',
            'url_xpath': './@href',
            'title_xpath': './span[@class="title"]/text()',
            'publish_time_xpath': './span[@class="time"]/text()',
            'body_xpath': '//div[@class="art_detail_body"]',
            'total': 2,
            'page': 1,
            'base_url': 'https://www.scdsjzx.cn/scdsjzx/busczc/zhengcefagui_{}.shtml'
        },
        {
            'url': 'https://www.scdsjzx.cn/scdsjzx/zhousczc/zhengcefagui.shtml',
            'label': "首页;数字法规;四川政策;市州政策文件",
            'detail_xpath': '//div[@class="rows"]/div/a',
            'url_xpath': './@href',
            'title_xpath': './span[@class="title"]/text()',
            'publish_time_xpath': './span[@class="time"]/text()',
            'body_xpath': '//div[@class="art_detail_body"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://www.scdsjzx.cn/scdsjzx/zhousczc/zhengcefagui_{}.shtml'
        },
        {
            'url': 'https://www.scdsjzx.cn/scdsjzx/guowaifagui/zhengcefagui.shtml',
            'label': "首页;数字法规;国外法规",
            'detail_xpath': '//div[@class="rows"]/div/a',
            'url_xpath': './@href',
            'title_xpath': './span[@class="title"]/text()',
            'publish_time_xpath': './span[@class="time"]/text()',
            'body_xpath': '//div[@class="art_detail_body"]',
            'total': 1,
            'page': 1,
            'base_url': 'https://www.scdsjzx.cn/scdsjzx/guowaifagui/zhengcefagui_{}.shtml'
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
        body_xpath = _meta.get('body_xpath')
        total = _meta.get('total')
        page = _meta.get('page')
        base_url = _meta.get('base_url')

        for ex_url in response.xpath(detail_xpath):
            url = response.urljoin(ex_url.xpath(url_xpath).extract_first())
            if url.endswith('.pdf'):
                continue

            if title_xpath:
                title = ''.join(ex_url.xpath(title_xpath).extract())
            else:
                title = None

            if publish_time_xpath:
                publish_time = ''.join(ex_url.xpath(f'string({publish_time_xpath})').extract()).strip()
            else:
                publish_time = None

            meta = {
                "label": label,
                "title": title,
                'publish_time': publish_time,
                'body_xpath': body_xpath,
            }
            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta)
            )

        if page < total:
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
                    'body_xpath': body_xpath,
                    'total': total,
                    'page': page,
                    'base_url': base_url,
                }),
            )

    def parse_detail(self, response):
        """
        详情
        :param response:
        :return:
        """
        _meta = response.meta

        method = response.request.method
        body = response.request.body.decode('utf-8')
        url = response.request.url

        body_xpath = _meta.get('body_xpath')
        title = _meta.get('title') or \
                response.xpath('//meta[@name="ArticleTitle"]/@content').extract_first() or \
                response.xpath('//div[@class="title"]/text()').extract_first()

        publish_time = _meta.get('publish_time') or \
                       response.xpath('//div[@class="info"]//td[1]/text()').extract_first() or \
                       ''.join(re.findall(r'发布日期：</b></span>(.*?)</li>', response.text, re.DOTALL)).strip() or \
                       ''.join(re.findall(r'\[发布时间：(.*?)\]', response.text, re.DOTALL))

        author = response.xpath('//meta[@name="Author"]/@content').extract_first() or \
                 ''.join(re.findall(r'<td .*?>.*?信息来源：(.*?)</td>', response.text, re.DOTALL)).strip() or \
                 ''.join(re.findall(r'发布机关：</b></span>(.*?)</li>', response.text, re.DOTALL)).strip() or \
                 ''.join(re.findall(r'\[来源：(.*?)\]', response.text, re.DOTALL))

        attachment_urls = response.xpath(f'{body_xpath}//a')

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            'spider_from': self._from,
            'label': _meta.get('label'),
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).extract()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').extract()),
            "images": [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()],
            "attachment": get_attachment(attachment_urls, url, self._from),
            "spider_date": get_now_date(),
            'spider_topic': policy_kafka_topic
        })
