# -*- coding: utf-8 -*-
import copy
import re
import subprocess
from hashlib import md5
from pathlib import Path
from urllib.parse import urljoin

from lxml import etree

import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.utils.project import get_project_settings

from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


def _get_http_session():
    """Prefer curl_cffi.requests; fallback to requests if unavailable."""
    try:
        from curl_cffi import requests as _requests
    except Exception:  # pragma: no cover
        import requests as _requests
    return _requests.Session(), _requests


class DataSpider(CrawlSpider):
    name = "news_fgw_gansu"
    allowed_domains = ["gansu.gov.cn"]

    _from = "甘肃省发展和改革委员会"
    category = "新闻"
    dupefilter_field = {"batch": "20251112"}

    # RS6 target
    base_url = "https://www.gansu.gov.cn"
    first_url = (
        "https://www.gansu.gov.cn/common/search/77b4ad617c73434dba6491e1de8a615a"
    )
    DOWNLOADER_MIDDLEWARES = {
        'tfpolicy.middlewares.DownloaderMiddleware': None,
    }

    # Headers used when requesting list/detail via session
    headers = {
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Referer": "https://www.gansu.gov.cn/gsszf/gsyw/common_noleftlist.shtml",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        ),
        "X-Requested-With": "XMLHttpRequest",
    }

    def start_requests(self):
        """Bootstrap cookies via RS6 flow, paginate list, and yield detail requests."""
        session, requests_mod = _get_http_session()
        session.headers.update(self.headers)

        resp = session.get(self.first_url, timeout=15)
        cookies = self._build_rs6_cookies(resp, session, requests_mod)

        page_url = self.first_url
        max_pages = 2
        for _page in range(1, max_pages + 1):
            html = self._get_html(session, page_url, cookies)
            if not html:
                break

            # ✅ yield 出所有详情请求
            for req in self._parse_and_dispatch_detail(html, cookies):
                yield req

            next_url = self._parse_next_link(html)
            if not next_url:
                break
            page_url = next_url

    def _parse_next_link(self, html):
        tree = etree.HTML(html)
        next_link = tree.xpath('//a[@class="next"]/@href')
        return urljoin(self.base_url, next_link[0]) if next_link else None

    # --------------------------- helpers ---------------------------
    def _build_rs6_cookies(self, response, session, requests_mod):
        """Extract inline and external JS, write to root, run env.js to get cookie."""
        root_dir = Path(__file__).resolve().parents[2]
        env_js = root_dir / "env.js"
        ts_js = root_dir / "ts.js"
        cd_js = root_dir / "cd.js"
        content_js = root_dir / "content.js"

        cookies = {}
        try:
            cookies.update(response.cookies.get_dict() or {})
        except Exception:
            pass

        try:
            tree = etree.HTML(response.text)
            content_str = tree.xpath('//meta[2]/@content')
            script_inline = tree.xpath('//script[1]/text()')
            script_src = tree.xpath('//script[2]/@src')

            if content_str:
                content_js.write_text(f'content="{content_str[0]}";', encoding="utf-8")
            if script_inline:
                ts_js.write_text(script_inline[0], encoding="utf-8")
            if script_src:
                js_code = session.get(urljoin(self.base_url, script_src[0]), headers=self.headers, timeout=15).text
                cd_js.write_text(js_code, encoding="utf-8")

            # compute cookie via node
            if env_js.exists():
                result = subprocess.run(
                    ["node", str(env_js)], capture_output=True, text=True, cwd=str(root_dir), timeout=30
                )
                ck = (result.stdout or "").strip()
                if ck:
                    cookies["4hP44ZykCTt5P"] = ck
        except Exception:
            pass

        return cookies

    def _get_html(self, session, url, cookies):
        try:
            res = session.get(url, headers=self.headers, cookies=cookies, timeout=15)
            if res.status_code == 200:
                return res.text
        except Exception:
            return None
        return None

    def _parse_and_dispatch_detail(self, html, cookies):
        tree = etree.HTML(html)

        titles = [t.strip() for t in tree.xpath('//div[@class="title"]/a/text()') if t.strip()]
        detail_urls = [urljoin(self.base_url, u) for u in tree.xpath('//div[@class="title"]/a/@href')]
        publish_times = [t.strip() for t in tree.xpath('//div[@class="date"]/text()') if t.strip()]

        for title, detail_url, pub_time in zip(titles, detail_urls, publish_times):
            meta = {
                "label": "甘肃要闻",
                "title": title,
                "publish_time": pub_time,
                "cookies": cookies,
                # reasonable defaults for gansu.gov.cn articles
                "body_xpath": (
                    '//div[@class="main"] | '
                    '//div[@class="content"] | '
                    '//div[contains(@class, "TRS_Editor")]'
                ),
            }

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta=copy.deepcopy(meta),
                cookies=cookies,
                dont_filter=True,
            )

        next_link = tree.xpath('//a[@class="next"]/@href')
        return urljoin(self.base_url, next_link[0]) if next_link else None

    # --------------------------- parsers ---------------------------
    def parse_detail(self, response):
        _meta = response.meta

        method = response.request.method
        body = response.request.body.decode("utf-8") if response.request.body else ""
        url = response.request.url
        title = _meta.get("title")
        publish_time = _meta.get("publish_time")
        label = _meta.get("label")
        body_xpath = _meta.get("body_xpath")

        author = (
            response.xpath('//meta[@name="Author"]/@content').get()
            or ''.join(re.findall(r'信息来源[:：]\s*(.*?)<', response.text))
            or ''.join(re.findall(r'来源[:：]\s*(.*?)<', response.text))
        )

        body_html = ' '.join(response.xpath(body_xpath).extract())
        content = ' '.join(response.xpath(f'{body_xpath}//text()').extract())

        attachment_urls = response.xpath(
            '//a[contains(@href, ".pdf") or contains(@href, ".doc") or '
            'contains(@href, ".docx") or contains(@href, ".xls") or '
            'contains(@href, ".xlsx") or contains(@href, ".zip") or '
            'contains(@href, ".rar")]'
        )

        images = [response.urljoin(i) for i in response.xpath(f'{body_xpath}//img/@src').extract()]
        attachments = get_attachment(attachment_urls, url, self._from)

        yield DataItem({
            "_id": md5(f"{method}{url}{body}".encode("utf-8")).hexdigest(),
            "url": url,
            "spider_topic": settings.get("KAFKA_TOPIC", {}).get(self.name),
            "spider_from": self._from,
            "label": label,
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachment": attachments,
            "spider_date": get_now_date(),
            "category": self.category
        })
