import copy
import re
from hashlib import md5

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment

settings = get_project_settings()

import execjs
from curl_cffi import requests
from loguru import logger
from lxml import etree
import subprocess
import time

session = requests.Session()

# =====================================================================
# 全局请求头
# =====================================================================
headers = {
    "Accept": "text/html, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Referer": "https://fgw.hubei.gov.cn/gzjj/dtyw/fgyw/index.shtml",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}


# =====================================================================
#  自动获取湖北发改委动态 Cookie（主逻辑）
# =====================================================================
def get_valid_cookies(url):
    logger.info(f"[cookie] 获取动态 Cookie for {url}")

    # 第一次访问页面
    res = session.get(url, headers=headers)
    logger.info(f"第一次访问状态：{res.status_code}")

    # 提取 meta 和 script
    tree = etree.HTML(res.text)

    contentStr = tree.xpath('//meta[2]/@content')[0]
    scriptStr = tree.xpath('//script[1]/text()')[0]
    js_src = tree.xpath('//script[2]/@src')[0]
    js_code = session.get("https://fgw.hubei.gov.cn" + js_src, headers=headers).text

    # 保存 JS 文件
    with open('./content.js', 'w', encoding='utf-8') as f:
        f.write(f'content="{contentStr}";')

    with open('./ts.js', 'w', encoding='utf-8') as f:
        f.write(scriptStr)

    with open('./cd.js', 'w', encoding='utf-8') as f:
        f.write(js_code)

    logger.info('[cookie] content.js / ts.js / cd.js 保存成功')

    # 获取第一次 cookies
    raw_cookies = {}
    try:
        raw_cookies = res.cookies.get_dict()
    except:
        raw_cookies = {}

    # 运行 Node 得到加密 Cookie
    try:
        result = subprocess.run(["node", "env.js"], capture_output=True, text=True)
        dynamic_token = result.stdout.strip()
    except Exception as e:
        logger.error(f"Node env.js 执行失败：{e}")
        dynamic_token = ""

    if dynamic_token:
        raw_cookies["924omrTVcFchP"] = dynamic_token

    logger.info(f"[cookie] 最终 Cookie：{raw_cookies}")

    return raw_cookies


# =====================================================================
# Scrapy Spider
# =====================================================================
class DataSpider(CrawlSpider):
    name = 'policy_fgw_hubei'
    allowed_domains = ['fgw.hubei.gov.cn']
    _from = '湖北发改委'
    category = "政策"

    # ================================
    # infoes 你的原始配置（完全保留）
    # ================================
    infoes = [
        # {
        #     'url': 'https://fgw.hubei.gov.cn/gzjj/dtyw/fgyw/index.shtml',
        #     'label': "发改要闻",
        #     'detail_xpath': '//ul[@class="list-t border6"]/li',
        #     'url_xpath': './a/@href',
        #     'title_xpath': './a/@title',
        #     'publish_time_xpath': './span',
        #     'body_xpath': '//div[@class="detail"]',
        #     'total': 553,
        #     'page': 1,
        #     'base_url': 'https://fgw.hubei.gov.cn/gzjj/dtyw/fgyw/index_{}.shtml'
        # },
        # {
        #     'url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgg/index.shtml',
        #     'label': "通知公告;公告",
        #     'detail_xpath': '//ul[@class="list-t border6"]/li',
        #     'url_xpath': './a/@href',
        #     'title_xpath': './a/@title',
        #     'publish_time_xpath': './span',
        #     'body_xpath': '//div[@class="detail"]',
        #     'total': 21,
        #     'page': 1,
        #     'base_url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgg/index_{}.shtml'
        # },
        {
            'url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgs/index.shtml',
            'label': "通知公告;公示",
            'detail_xpath': '//ul[@class="list-t border6"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="detail"]',
            'total': 21,
            'page': 1,
            'base_url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgs/index_{}.shtml'
        },
        {
            'url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgs/index.shtml',
            'label': "通知公告;通知",
            'detail_xpath': '//ul[@class="list-t border6"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './span',
            'body_xpath': '//div[@class="detail"]',
            'total': 62,
            'page': 1,
            'base_url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgs/index_{}.shtml'
        },
        {
            'url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/tzxm/index.shtml',
            'label': "省级数据;投资项目",
            'detail_xpath': '//ul[@class="list-t border6"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './a/b',
            'body_xpath': '//div[@class="detail"]',
            'total': 8,
            'page': 1,
            'base_url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/tzxm/index_{}.shtml'
        },
        {
            'url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/zdxm/index.shtml',
            'label': "省级数据;重点项目",
            'detail_xpath': '//ul[@class="list-t border6"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './a/b',
            'body_xpath': '//div[@class="detail"]',
            'total': 5,
            'page': 1,
            'base_url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/zdxm/index_{}.shtml'
        },
        {
            'url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/jgkb/index.shtml',
            'label': "省级数据;价格快报",
            'detail_xpath': '//ul[@class="list-t border6"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './a/b',
            'body_xpath': '//div[@class="detail"]',
            'total': 200,
            'page': 1,
            'base_url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/jgkb/index_{}.shtml'
        },
        {
            'url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/nyjs/index.shtml',
            'label': "省级数据;能源建设",
            'detail_xpath': '//ul[@class="list-t border6"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './a/b',
            'body_xpath': '//div[@class="detail"]',
            'total': 16,
            'page': 1,
            'base_url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/nyjs/index_{}.shtml'
        },
        {
            'url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/qt/index.shtml',
            'label': "省级数据;其他",
            'detail_xpath': '//ul[@class="list-t border6"]/li',
            'url_xpath': './a/@href',
            'title_xpath': './a/@title',
            'publish_time_xpath': './a/b',
            'body_xpath': '//div[@class="detail"]',
            'total': 8,
            'page': 1,
            'base_url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/qt/index_{}.shtml'
        },
        {
            'url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/gdsj/index.shtml',
            'label': "省级数据;归档数据",
            'detail_xpath': '//ul[@class="list-t border6"]/li',
            'url_xpath': './a/@href',

            'title_xpath': './a/@title',
            'publish_time_xpath': './a/b',
            'body_xpath': '//div[@class="detail"]',
            'total': 8,
            'page': 1,
            'base_url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/gdsj/index_{}.shtml'
        },
    ]

    # ==========================================================
    # Scrapy 启动时自动执行：获取一次 Cookie
    # ==========================================================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        logger.info("正在初始化湖北发改委 Cookie...")
        self.base_cookie = get_valid_cookies(
            "https://fgw.hubei.gov.cn/gzjj/dtyw/fgyw/index.shtml"
        )
        logger.info(f"[scrapy] 启动 Cookie：{self.base_cookie}")

    # ==========================================================
    # 1. 列表页
    # ==========================================================
    def start_requests(self):
        for info in self.infoes:
            url = info['url']
            yield scrapy.Request(
                url=url,
                callback=self.parse_item,
                cookies=self.base_cookie,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    def parse_item(self, response):
        meta = response.meta

        detail_xpath = meta['detail_xpath']
        url_xpath = meta['url_xpath']
        title_xpath = meta['title_xpath']
        publish_time_xpath = meta['publish_time_xpath']
        body_xpath = meta['body_xpath']
        page = meta['page']
        total = meta['total']
        base_url = meta['base_url']

        # 遍历列表
        for ex_url in response.xpath(detail_xpath):
            url = response.urljoin(ex_url.xpath(url_xpath).get())
            if url.endswith('.pdf'):
                continue

            title = ''.join(ex_url.xpath(title_xpath).getall())
            publish_time = ''.join(
                ex_url.xpath(f'string({publish_time_xpath})').get()
            ).replace('(', '').replace(')', '').strip()

            new_meta = {
                "label": meta['label'],
                "title": title,
                'publish_time': publish_time,
                'body_xpath': body_xpath,
            }

            yield scrapy.Request(
                url=url,
                callback=self.parse_detail,
                cookies=self.base_cookie,
                meta=new_meta,
                dont_filter=True
            )

        # 翻页
        if page < total:
            page += 1
            next_url = base_url.format(page)

            meta['page'] = page
            yield scrapy.Request(
                url=next_url,
                callback=self.parse_item,
                cookies=self.base_cookie,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

    # ==========================================================
    # 2. 详情页
    # ==========================================================
    def parse_detail(self, response):
        meta = response.meta

        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.request.url

        body_xpath = meta['body_xpath']
        title = meta['title']

        publish_time = (
                meta.get('publish_time') or
                ''.join(response.xpath('//publishtime/text()').getall()).strip() or
                ''.join(re.findall(r'发布日期.*?(\d{4}-\d{2}-\d{2})', response.text))
        )

        label = meta['label']

        author = (
                response.xpath('//meta[@name="Author"]/@content').get() or
                ''.join(re.findall(r'发布机构：</strong><span>(.*?)</span></li>', response.text)) or
                ''.join(re.findall(r'>信息来源：(.*?)</', response.text))
        )

        attachment_urls = response.xpath(
            '//p[contains(@class, "insertfileTag")]//a | '
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or contains(@href, ".docx") or '
            'contains(@href, ".xls") or contains(@href, ".xlsx") or contains(@href, ".wps") or '
            'contains(@href, ".zip") or contains(@href, ".rar")]'
        )

        images = [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').getall()]
        attachments = get_attachment(attachment_urls, url, self._from)

        yield DataItem({
            "_id": md5(f'{method}{url}{body}'.encode('utf-8')).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            'spider_from': self._from,
            'label': label,
            'title': title,
            'author': author,
            'publish_time': publish_time,
            'body_html': ' '.join(response.xpath(body_xpath).getall()),
            "content": ' '.join(response.xpath(f'{body_xpath}//text()').getall()),
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
