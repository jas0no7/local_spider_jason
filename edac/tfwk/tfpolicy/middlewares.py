# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from twisted.internet import error
from scrapy.core.downloader.handlers.http11 import TunnelError
import base64
import sys
from urllib.parse import urlparse, quote

from loguru import logger
from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.project import get_project_settings
from scrapy.utils.response import response_status_message
from scrapy.core.downloader.handlers.http11 import TunnelError
sys.path.append('..')
sys.path.append('../..')

from .mydefine import request_seen_del, ProxyPool, UserAgent

proxypool = ProxyPool()
ua = UserAgent()
settings = get_project_settings()
mobile_ua_host = settings.get('MOBILE_UA_HOST', [])
playwright_url = settings.get('PLAYWRIGHT_URL')


def add_request(request):
    """
    修改重试时的请求头
    :param request:
    :return: 修改后的header
    """
    url = request.url.strip()
    host = urlparse(url).hostname
    if host in mobile_ua_host:
        request.headers['User-Agent'] = ua.random_android()
    else:
        request.headers['User-Agent'] = ua.random_win()

    request.headers['Host'] = host
    request.headers["Upgrade-Insecure-Requests"] = "1"
    request.headers['Accept'] = "*/*"

    use_playwright = request.meta.get('use_playwright', False)
    use_proxy = request.meta.get('use_proxy', True)
    if use_playwright and not url.startswith(playwright_url):
        request._set_url(f"{playwright_url}{quote(url, safe=':/:.?')}")
        request.meta['old_request_url'] = url
        request.meta['old_method'] = request.method
        use_proxy = False

    if use_playwright and url.startswith(playwright_url):
        use_proxy = False

    if use_proxy:
        proxy = proxypool.get_proxy()
        request.meta['proxy'] = f"http://{proxy.get('ip_port')}"
        request.headers[b'Proxy-Authorization'] = b'Basic ' + base64.b64encode(f"{proxy.get('username')}:{proxy.get('password')}".encode('utf-8'))

    return request


class SpiderMiddleware:
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

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class DownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    @staticmethod
    def process_request(request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        add_request(request)
        return None

    @staticmethod
    def process_response(request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        if request.meta.get('use_playwright', False):
            old_request_url = request.meta.get('old_request_url')
            response._set_url(old_request_url)
            request._set_url(old_request_url)

        return response

    @staticmethod
    def process_exception(request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    @staticmethod
    def spider_opened(spider):
        spider.logger.info('Spider opened: %s' % spider.name)

from twisted.internet.error import (
    TimeoutError, DNSLookupError, ConnectionRefusedError,
    ConnectionDone, ConnectError, ConnectionLost, TCPTimedOutError
)

class MyRetryMiddleware(RetryMiddleware):
    """
    重试
    """
    EXCEPTIONS_TO_RETRY = (
        TimeoutError, DNSLookupError, ConnectionRefusedError,
        ConnectionDone, ConnectError, ConnectionLost, TCPTimedOutError,
        TunnelError
    )
    # EXCEPTIONS_TO_RETRY = (
    #     error.TimeoutError,
    #     error.DNSLookupError,
    #     error.ConnectionRefusedError,
    #     error.ConnectionDone,
    #     error.ConnectError,
    #     error.ConnectionLost,
    #     error.TCPTimedOutError,
    #     error.ResponseFailed,
    #     # error.PotentialDataLossError,
    #     TunnelError,
    # )
    def process_response(self, request, response, spider):
        request = add_request(request)
        if request.meta.get('dont_retry', False):
            return response

        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            logger.info(f'重试中间件, 响应处理: {reason}')
            return self._retry(request, reason, spider) or response

        retries = request.meta.get('retry_times', 0)
        if retries != 0:
            logger.success(f'终于请求成功了: {response.url}')

        if retries >= self.max_retry_times:
            # 重试后还是失败 则删除已经添加的去重的值 下次可以重新获取
            dupefilter_field = spider.dupefilter_field
            request_seen_del(request, **dupefilter_field)
            logger.success(f'重试次数太多, 删除 {request.url} 在过滤器中的值, 下次重新请求！')

        if request.meta.get('use_playwright', False):
            old_request_url = request.meta.get('old_request_url')
            response._set_url(old_request_url)
            request._set_url(old_request_url)

        return response

    def process_exception(self, request, exception, spider):
        retries = request.meta.get('retry_times', 0)
        request = add_request(request)
        if retries >= self.max_retry_times:
            # 重试后还是失败 则删除已经添加的去重的值 下次可以重新获取
            dupefilter_field = spider.dupefilter_field
            request_seen_del(request, **dupefilter_field)
            logger.success(f'重试次数太多, 删除 {request.url} 在过滤器中的值, 下次重新请求！')
        else:
            logger.info(f'重试中间件, 异常处理: 第 {retries + 1} 次出错, url: {request.url}, 异常: {exception}')
            if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
                return self._retry(request, exception, spider)
