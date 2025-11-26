# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import time
import subprocess

from scrapy import signals
from itemadapter import ItemAdapter

from curl_cffi import requests
from lxml import etree
from loguru import logger


class CookieFetcher:
    """
    专门用于获取湖北省生态环境厅站点的 Cookie。
    逻辑：
    1. 访问目标列表页，拿到页面里的 meta、script 等参数
    2. 写入 content.js / ts.js / cd.js
    3. 调用 node env.js 生成最终的 924omrTVcFchP
    4. 返回完整 cookies 字典
    """

    def __init__(self):
        self.session = requests.Session()
        self.base_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Referer": "https://sthjt.hubei.gov.cn/",
            "User-Agent": "Mozilla/5.0",
        }

    def fetch(self, url: str) -> dict:
        logger.info(f"开始获取 cookies，访问页面: {url}")

        r1 = self.session.get(url, headers=self.base_headers)
        logger.info(f"第一次访问状态码: {r1.status_code}")

        tree = etree.HTML(r1.text)

        # 解析 content，页面结构：meta[2] 的 content
        content_str_list = tree.xpath("//meta[2]/@content")
        if not content_str_list:
            logger.error("未找到 meta[2]/@content，cookie 生成可能失败")
            content_str = ""
        else:
            content_str = content_str_list[0]

        # 第一个内联 script
        script1_list = tree.xpath("//script[1]/text()")
        script1 = script1_list[0] if script1_list else ""

        # 第二个外联 script
        script2_src_list = tree.xpath("//script[2]/@src")
        if script2_src_list:
            script2_url = "https://sthjt.hubei.gov.cn" + script2_src_list[0]
            js_code = self.session.get(script2_url, headers=self.base_headers).text
        else:
            logger.error("未找到第二个 script 的 src，cookie 生成可能失败")
            js_code = ""

        # 写入三个 js 文件，供 env.js 使用
        with open("./content.js", "w", encoding="utf-8") as f:
            f.write(f'content="{content_str}";')
        with open("./ts.js", "w", encoding="utf-8") as f:
            f.write(script1)
        with open("./cd.js", "w", encoding="utf-8") as f:
            f.write(js_code)

        logger.info("cookie 生成相关 js 脚本写入成功")

        # 初始 cookies
        try:
            cookies = r1.cookies.get_dict()
        except Exception:
            cookies = {}
            for c in str(r1.cookies).split(";"):
                if "=" in c:
                    k, v = c.strip().split("=", 1)
                    cookies[k] = v

        # 通过 Node 运行 env.js，生成最终的 924omrTVcFchP
        result = subprocess.run(["node", "env.js"], capture_output=True, text=True)
        cookie_value = result.stdout.strip()

        if not cookie_value:
            logger.error("env.js 未返回 cookie 值，请检查 env.js 脚本")
        else:
            cookies["924omrTVcFchP"] = cookie_value

        logger.info(f"最终 cookies: {cookies}")
        return cookies


class LocalCrawlerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class LocalCrawlerDownloaderMiddleware:
    """
    下载中间件：
    1. 对湖北生态环境厅相关请求，自动注入 Cookie 和浏览器头
    2. 定期刷新 Cookie，避免跑到后面页面出现 412
    """

    def __init__(self):
        self.cookie_fetcher = CookieFetcher()
        self.cookies = {}
        self.last_cookie_time = 0
        # Cookie 过期时间（秒），你之前日志里大概 2 分钟左右开始 412，这里保守一点设 60 秒
        self.cookie_ttl = 60

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def _need_new_cookie(self) -> bool:
        now = time.time()
        return (not self.cookies) or (now - self.last_cookie_time > self.cookie_ttl)

    def _ensure_cookie(self, request, spider):
        """
        判断当前是否需要重新获取 cookie，如果需要则调用 CookieFetcher。
        """
        # 只对湖北生态环境厅站点启用
        need_cookie = False
        if "sthjt.hubei.gov.cn" in request.url:
            need_cookie = True
        if getattr(spider, "name", "") == "policy_sthjt_hubei":
            need_cookie = True

        if not need_cookie:
            return

        if self._need_new_cookie():
            logger.info("Cookie 不存在或已过期，开始重新获取")
            # 这里访问一个固定的页面用于生成 cookie（列表页即可）
            base_url = "https://sthjt.hubei.gov.cn/fbjd/zc/gfxwj/index.shtml"
            self.cookies = self.cookie_fetcher.fetch(base_url)
            self.last_cookie_time = time.time()

        # 给请求注入 Cookie
        request.cookies = self.cookies

        # 模拟浏览器 Header
        browser_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
        for k, v in browser_headers.items():
            # 不直接覆盖已有的头，如果已有就保留原值
            if k not in request.headers:
                request.headers[k] = v

        # Referer 自动处理
        if "Referer" not in request.headers:
            referer = request.meta.get("referer") or "https://sthjt.hubei.gov.cn/"
            request.headers["Referer"] = referer

    def process_request(self, request, spider):
        """
        每一个请求发出去之前都会经过这里。
        在这里统一处理 cookie 和 headers。
        """
        self._ensure_cookie(request, spider)
        return None

    def process_response(self, request, response, spider):
        """
        下载器返回 response 后经过这里。
        如果想在 412 时自动重试，可以在这里做。
        先保持简单：直接返回 response。
        """
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        return None

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
