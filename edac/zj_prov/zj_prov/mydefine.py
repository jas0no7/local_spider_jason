import logging
import pickle
from datetime import datetime
from hashlib import md5
from json import dumps
from pathlib import Path
from random import uniform, choice, randint, sample
from time import sleep
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from redis import Redis, ConnectionPool
from scrapy.logformatter import LogFormatter
from scrapy.utils.project import get_project_settings
from scrapy import Request
# 替换原来的导入
from scrapy.utils.request import request_from_dict
# try:
#     from scrapy.utils.serialize import request_to_dict, request_from_dict
# except ImportError:
#     from scrapy.utils.request import request_to_dict, request_from_dict


from w3lib.url import canonicalize_url

logger = logging.getLogger(__name__)
settings = get_project_settings()

REDIS_181 = settings.get('REDIS_181')
MINIO = settings.get('MINIO')
PROXY = settings.get("PROXY")
KAFKA = settings.get("KAFKA")
REDIS_PROXY_DB = settings.get('REDIS_PROXY_DB')
REDIS_FILTER_DB = settings.get('REDIS_FILTER_DB')
minio_bucket_name = settings.get('BUCKET_NAME')
attachment_suffix = settings.get('ATTACHMENT_SUFFIX')
redis_filter_db = settings.get('REDIS_FILTER_DB')
minio_domain = settings.get('MINIO_DOMAIN')
minio_domain = f'{minio_domain}/' if not minio_domain.endswith('/') else minio_domain

_queue_key = settings.get('SCHEDULER_QUEUE_KEY')
_dupefilter_key = settings.get('SCHEDULER_DUPEFILTER_KEY')
_dupefilter_cls = settings.get('DUPEFILTER_CLASS')
_persist = settings.get('SCHEDULER_PERSIST')
_flush_on_start = settings.getbool('SCHEDULER_FLUSH_ON_START')
_idle_before_close = settings.getint('SCHEDULER_IDLE_BEFORE_CLOSE')


def get_now_date(fmt='%Y-%m-%d %H:%M:%S'):
    """
    获取当前时区时间
    :param fmt: 日期转字符串格式
    :return:
    """
    return datetime.now(tz=ZoneInfo(key='PRC')).strftime(fmt) if fmt else datetime.now(tz=ZoneInfo(key='PRC'))


def get_attachment(attachment_urls, url, spider_from):
    """
    附件
    :param attachment_urls:附件url：[xpath]或者[(url, name)]
    :param url: 页面的url 拼接
    :param spider_from: 站点名
    :return:
    """
    attachment = []
    dup = []
    for att in attachment_urls:
        if not isinstance(att, tuple):
            attachment_url = att.xpath('./@href').extract_first()
            attachment_name = att.xpath('.//text()').extract_first()
        else:
            attachment_url, attachment_name = att

        if not attachment_url or not attachment_name:
            continue

        suffix_url_1 = Path(urlparse(attachment_url).path).suffix
        suffix_url_2 = Path(attachment_url).suffix
        if f"{suffix_url_1}".lower() not in attachment_suffix and suffix_url_2 not in attachment_suffix and '.pdf' not in attachment_url:
            continue

        if f"{suffix_url_1}".lower() in attachment_suffix:
            suffix = suffix_url_1
        elif suffix_url_2 in attachment_suffix:
            suffix = suffix_url_2
        elif '.pdf' in attachment_url:
            suffix = '.pdf'
        else:
            continue

        value = md5(f'{attachment_url}{url}'.encode('utf-8')).hexdigest()
        attachment_name = f"{value}{suffix}"

        if not attachment_url.startswith('http'):
            attachment_url = urljoin(url, attachment_url)

        if not attachment_url.startswith('http'):
            continue

        # 去重 有些附件会重复
        if attachment_url in dup:
            continue
        dup.append(attachment_url)

        save_path = f'{spider_from}/{attachment_name}'
        attachment.append({
            'attachment_url': attachment_url,
            'attachment_name': attachment_name,
            'minio_url': f'{minio_domain}{minio_bucket_name}/{save_path}',
            'relative_path': f"/{minio_bucket_name}/{save_path}"
        })

    return attachment


class CustomLogFormatter(LogFormatter):
    """
    日志格式化 主要是为了在pipelines执行完成后禁止scrapy.core.scraper._itemproc_finished输出日志
    数据太多会查起来太麻烦了
    """

    def scraped(self, item, response, spider):
        # 检测item中部分关键字段
        required_keys = {'_id', 'url', 'spider_from', 'spider_date'}
        if not (item is None or all(key in item for key in required_keys)):
            return super().scraped(item, response, spider)


class MyRedis(object):
    """
    redis
    """

    def __init__(self, decode_responses: bool = True, db: int = 1):
        """
        :param decode_responses: 是否编码 scrapy使用时为False
        :param db: 0：代理 1：去重
        """
        connect = {
            "host": REDIS_181.get("host"),
            "port": REDIS_181.get("port"),
            "db": db,
            "max_connections": REDIS_181.get("max_connections"),
            "decode_responses": decode_responses
        }
        self.redis = Redis(connection_pool=ConnectionPool(**connect))

    def zset_zadd(self, key: str, value: dict):
        """
        添加value到key中
        :param key:
        :param value:
        :return:
        """
        return self.redis.zadd(key, value)

    def zset_zcard(self, key: str):
        """
        获取key的元素数量
        :param key: key
        :return:
        """
        return self.redis.zcard(key)

    def pipeline(self):
        """
        返回 pipeline 对象
        :return:
        """
        return self.redis.pipeline()

    def string_keys(self, key: str) -> list:
        """
        查找所有满足条件的key
        :param key:
        :return:
        """
        return self.redis.keys(key)

    def redis_del(self, key: str):
        """
        删除key
        :param key: 要删除的key
        :return:
        """
        return self.redis.delete(key)

    def create(self, key, capacity=10000000, **kwargs):
        """
        创建过滤器
        :param key: redis中的key
        :param capacity: 创建的过滤器的初始大小
        :return:
        """
        if not self.redis.exists(key):
            self.redis.cf().create(key, capacity)
            return True
        return False

    def add(self, key, value, **kwargs):
        """
        添加 存在则跳过
        :param key: redis中的key
        :param value: 添加的值
        :return:
        """
        return self.redis.cf().addnx(key, value)

    def exists(self, key, value, **kwargs):
        """
        在 key 中是否存在 value
        :param key:
        :param value:
        :return:
        """
        return self.redis.cf().exists(key, value)

    def delete(self, key: str, value: str):
        """
        在 key 中删除 value
        :param key:
        :param value:
        :return:
        """
        return self.redis.cf().delete(key, value)


class ProxyPool(MyRedis):
    """
    代理 ip
    """

    def __init__(self, db: int = REDIS_PROXY_DB):
        self._proxy_key = PROXY.get("key")
        # 用户名密码
        self._ip_user = PROXY.get("user")
        self._ip_passwd = PROXY.get("passwd")
        # 替换键
        self._replace = f'{self._proxy_key}:'
        super().__init__(db=db)

    def get_proxy(self) -> dict:
        """
        redis 代理池中获取代理
        :return:
        """
        # 获取所有的key
        while True:
            _key = self.string_keys(f"{self._proxy_key}*")
            if not _key:
                logger.info('目前可用代理ip为空, 等待重新获取')
                sleep(uniform(10, 20))
                continue

            ip_port_key = choice(_key)
            ip_port = ip_port_key.replace(self._replace, '')

            return {
                "username": self._ip_user,
                "password": self._ip_passwd,
                "ip_port": ip_port
            }


class MyKafka(object):
    """
    kafka生产者和消费者的父类 公共方法
    """

    def __init__(self, bootstrap_servers=None):
        bootstrap_servers = bootstrap_servers or KAFKA.get("bootstrap_servers")
        self.admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)

    def create_topics(self, topic_names: list, partitions: int = 3, replication_factor: int = 3, retention_ms: int = 31536000000, max_message_bytes: int = 5242880):
        """
        新建topic
        :param topic_names: topic名称 ['news-bjx', 'news-gmw']
        :param partitions: 分区数 默认3
        :param replication_factor: 副本数 默认3
        :param retention_ms: 过期时间(毫秒) 默认365天
        :param max_message_bytes: 消息大小 默认5M：5 * 1024 * 1024
        :return:
        """
        topic_configs = {
            'cleanup.policy': 'delete',
            'retention.ms': retention_ms,
            'max.message.bytes': max_message_bytes
        }
        topics = [NewTopic(name=topic_name, num_partitions=partitions, replication_factor=replication_factor, topic_configs=topic_configs) for topic_name in topic_names]
        self.admin_client.create_topics(new_topics=topics, validate_only=False)

    def topics_list(self) -> list:
        """
        获取所有的topic
        :return:
        """
        return self.admin_client.list_topics()


class MyKafkaProducer(MyKafka):
    """
    kafka 生产者
    """

    def __init__(self, max_request_size: int = 5242880):
        bootstrap_servers = KAFKA.get("bootstrap_servers")
        # 连接生产者
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: dumps(v, ensure_ascii=False).encode('utf-8'),
            max_request_size=max_request_size,
            api_version=KAFKA.get("api_version", (2, 7))
        )
        super().__init__(bootstrap_servers=bootstrap_servers)

    def send(self, topic: str, value: dict, key=None):
        """
        发送数据到kafka
        :param topic: 主题
        :param value: 发送到kafka的数据
        :param key: 消息key
        :return:
        """
        if key is not None:
            key = key.encode('utf-8')
        try:
            self.producer.send(topic=topic, value=value, key=key)
            self.producer.flush(timeout=5)
        except Exception as e:
            logger.debug(f'发送失败: {e}')
        else:
            logger.info(f'发送成功: {value}')

    def close(self):
        """
        关闭
        :return:
        """
        try:
            self.producer.close()
        except:
            pass


class UserAgent(object):
    """
    随机生成user-agent
    """

    def __init__(self):
        self.win_version = ["6.1", "6.2", "6.3", "10.0"]
        self.linux_version = ["Linux", "Ubuntu; Linux"]
        self.win_cpu = ['Win64; x64', 'WOW64']
        self.linux_cpu = ['i686', 'x86_64', 'i686 on x86_64']
        self.android_cpu = ['armv7l', 'armv8l']
        self.chrome_max_version = 125
        self.firefox_max_version = 125
        self.edge_max_version = 125
        self.uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.digits = '0123456789'
        self.all = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def chrome_browser_version(self) -> str:
        """
        谷歌浏览器版本
        :return:
        """
        return f'{randint(80, self.chrome_max_version)}.0.{randint(1000, 9000)}.{randint(10, 200)}'

    def firefox_browser_version(self) -> dict:
        """
        火狐浏览器版本
        :return:
        """
        return {
            'build_version': f'{randint(50, self.firefox_max_version)}.0',
            'geckotrail': datetime.fromtimestamp(randint(1577808000, int(get_now_date(fmt=None).timestamp()))).strftime('%Y%m%d')
        }

    def get_edge_browser_version(self) -> dict:
        """
        edge版本
        :return:
        """
        build_version_1 = randint(80, self.edge_max_version)
        build_version_2 = randint(1000, 5000)
        build_version_3 = randint(10, 200)

        return {
            'build_version': f'{build_version_1}.0.{build_version_2}.{build_version_3}',
            'edge_build_version': f'{build_version_1}.0.{randint(1000, build_version_2)}.{randint(10, build_version_3)}',
        }

    def get_android_chrome_build(self) -> str:
        """
        安卓 chrome
        :return:
        """
        smartphone = [
            {
                'brand': 'HUAWEI',
                'family': f'{"".join(sample(self.uppercase, 3))}-{"".join(sample(self.uppercase, 2))}{randint(10, 99)}',
            },
            {
                'brand': 'honor',
                'family': f'{"".join(sample(self.uppercase, 3))}-{"".join(sample(self.uppercase, 2))}{randint(10, 99)}',
            },
            {
                'brand': 'samsung',
                'family': f'SM-{"".join(sample(self.all, 5))}{choice(["", " Pro", " Note", " Ultra", " Max"])}',
                'model': f'{"".join(sample(self.all, 5))}',
            },
            {
                'brand': 'OPPO',
                'family': f'OPPO {choice(self.uppercase)}{randint(8, 15)}{choice(["", " Pro", " Note", " Ultra", " Max"])}',
                'model': f'{"".join(sample(self.all, 6))}',
            },
            {
                'brand': 'xiaomi',
                'family': f'MI {randint(6, 12)}{choice(["", " Pro", " Note", " Ultra", " Max"])}',
                'model': f'{"".join(sample(self.all, 6))}',
            },
            {
                'brand': 'vivo',
                'family': f'vivo {choice(self.uppercase)}{randint(8, 99)}{choice(["", " Pro", " Note", " Ultra", " Max"])}',
                'model': f'{"".join(sample(self.all, 6))}',
            },
            {
                'brand': 'redmi',
                'family': f'Redmi {choice(self.uppercase)}{randint(8, 99)}{choice(["", " Pro", " Note", " Ultra", " Max"])}',
                'model': f'{"".join(sample(self.all, 6))}',
            },
        ]
        info = choice(smartphone)
        if info.get('brand').lower() in ['huawei', 'honor']:
            return f"{info.get('family')} Build/{info.get('brand').upper()}{info.get('family')}"
        else:
            return f"{info.get('family')} Build/{info.get('model')}"

    def win_firefox(self) -> str:
        info = self.firefox_browser_version()
        return f'Mozilla/5.0 (Windows NT {choice(self.win_version)}; {choice(self.win_cpu)}; rv:{info.get("build_version")}) Gecko/{info.get("geckotrail")} Firefox/{info.get("build_version")}'

    def win_chrome(self) -> str:
        return f'Mozilla/5.0 (Windows NT {choice(self.win_version)}; {choice(self.win_cpu)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_browser_version()} Safari/537.36'

    def win_edge(self) -> str:
        info = self.get_edge_browser_version()
        return f'Mozilla/5.0 (Windows NT {choice(self.win_version)}; {choice(self.win_cpu)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{info.get("build_version")} Safari/537.36 Edg/{info.get("edge_build_version")}'

    def android_firefox(self) -> str:
        info = self.firefox_browser_version()
        return f'Mozilla/5.0 (Android {randint(7, 12)}.{randint(0, 1)}.{randint(0, 1)}; Mobile; rv:{self.firefox_browser_version().get("build_version")}) Gecko/{info.get("geckotrail")} Firefox/{info.get("build_version")}'

    def android_chrome(self) -> str:
        return f'Mozilla/5.0 (Linux; Android {randint(7, 12)}.{randint(0, 1)}.{randint(0, 1)}; {self.get_android_chrome_build()}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_browser_version()} Mobile Safari/537.36'

    def random_win(self) -> str:
        return choice([
            self.win_chrome,
            self.win_firefox,
            self.win_edge
        ])()

    def random_android(self) -> str:
        func = [
            self.android_firefox,
            self.android_chrome
        ]
        return choice(func)()


myredis = MyRedis(decode_responses=False, db=redis_filter_db)
myredis.create(key=_dupefilter_key, capacity=10000000)


def request_seen_define(url, method='GET', body='', add=True, **dupefilter_field) -> bool:
    """
    自己拼接
    :param method: 请求方式 get post
    :param url: 请求url
    :param body: 请求参数 post
    :param add: 不存在的时候是否添加 True：是 False：不添加
    :param dupefilter_field: 去重批次 为了以后的修改
    :return: 存在返回True 不存在返回False
    """
    dupefilter_field = f"{''.join(sorted([f'{v}' for v in dupefilter_field.values()]))}"
    fp = md5(f'{method.upper()}{url}{body}{dupefilter_field}'.encode('utf-8')).hexdigest()
    if myredis.exists(key=_dupefilter_key, value=fp):
        logger.info(f'已存在 {url}')
        return True
    if add:
        myredis.add(key=_dupefilter_key, value=fp)
    return False


def request_seen_del(request, **dupefilter_field):
    """
    删除去重
    :param request:
    :param dupefilter_field:
    :return:
    """
    fp = md5()
    fp.update(request.method.encode('utf-8'))
    fp.update(canonicalize_url(request.url).encode('utf-8'))
    fp.update(request.body or b'')
    dupefilter_field = f"{''.join(sorted([f'{v}' for v in dupefilter_field.values()]))}"
    fp.update(dupefilter_field.encode('utf-8'))
    fp = fp.hexdigest()
    myredis.delete(key=_dupefilter_key, value=fp)


class Queue(object):
    """
    自定义请求队列
    """

    def __init__(self, spider):
        self.spider = spider
        self.key = _queue_key % {'spider': spider.name}

    def clear(self):
        """
        删除 队列
        :return:
        """
        myredis.redis_del(key=self.key)

    def __len__(self):
        """
        队列中的成员个数
        :return:
        """
        return myredis.zset_zcard(key=self.key)

    def push(self, request):
        """
        添加到队列
        :param request:
        :return:
        """
        # obj = request_to_dict(request, self.spider)
        obj = request.to_dict(spider=self.spider)
        data = pickle.dumps(obj, protocol=-1)
        score = -request.priority
        myredis.zset_zadd(key=self.key, value={data: score})

    def pop(self, timeout=0):
        """
        随机获取队列中的元素
        :param timeout:
        :return:
        """
        pipe = myredis.pipeline()
        pipe.multi()
        pipe.zrange(self.key, 0, 0).zremrangebyrank(self.key, 0, 0)
        results, count = pipe.execute()
        if results:
            obj = pickle.loads(results[0])
            return request_from_dict(obj,spider=self.spider)#, self.spider


class RFPDupeFilter(object):
    """
    自定义去重
    """

    def __init__(self, dupefilter_field, debug=False):
        self.debug = debug
        self.logdupes = True
        self.dupefilter_field = dupefilter_field

    @classmethod
    def from_settings(cls, _settings):
        return cls(_settings.get('DUPEFILTER_FIELD'))

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    @classmethod
    def from_spider(cls, spider):
        try:
            dupefilter_field = spider.dupefilter_field
        except:
            dupefilter_field = {}
        return cls(dupefilter_field=dupefilter_field, debug=False)

    def close(self, reason=''):
        self.clear()

    def log(self, request, spider):
        if self.debug:
            msg = "Filtered duplicate request: %(request)s"
            logger.debug(msg, {'request': request}, extra={'spider': spider})
        elif self.logdupes:
            msg = ("Filtered duplicate request %(request)s"
                   " - no more duplicates will be shown"
                   " (see DUPEFILTER_DEBUG to show all duplicates)")
            logger.debug(msg, {'request': request}, extra={'spider': spider})
            self.logdupes = False

    def request_seen(self, request):
        """
        去重
        :param request:
        :return: 存在返回True 不存在返回False
        """
        fp = md5()
        fp.update(request.method.encode('utf-8'))
        fp.update(canonicalize_url(request.url).encode('utf-8'))
        fp.update(request.body or b'')
        dupefilter_field = f"{''.join(sorted([f'{v}' for v in self.dupefilter_field.values()]))}"
        fp.update(dupefilter_field.encode('utf-8'))
        fp = fp.hexdigest()
        inserted = myredis.add(key=_dupefilter_key, value=fp)
        return not bool(inserted)

    @staticmethod
    def clear():
        myredis.redis_del(key=_dupefilter_key)


class Scheduler(object):
    """
    自定义调度器
    """

    def __init__(self, stats):
        self.persist = _persist
        self.flush_on_start = _flush_on_start
        self.idle_before_close = _idle_before_close
        self.stats = stats

    def __len__(self):
        return len(self.queue)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.stats)

    def open(self, spider):
        try:
            dupefilter_field = spider.dupefilter_field
        except:
            dupefilter_field = {}

        self.spider = spider
        self.queue = Queue(spider)
        self.df = RFPDupeFilter(dupefilter_field)

        if self.flush_on_start:
            self.flush()

        if len(self.queue):
            spider.log("Resuming crawl (%d requests scheduled)" % len(self.queue))

    def close(self, reason):
        if not self.persist:
            self.flush()

    def flush(self):
        self.df.clear()
        self.queue.clear()

    def enqueue_request(self, request):
        if not request.dont_filter and self.df.request_seen(request):
            self.df.log(request, self.spider)
            return False

        if self.stats:
            self.stats.inc_value('scheduler/enqueued/redis', spider=self.spider)

        self.queue.push(request)
        return True

    def next_request(self):
        block_pop_timeout = self.idle_before_close
        request = self.queue.pop(block_pop_timeout)

        if request and self.stats:
            self.stats.inc_value('scheduler/dequeued/redis', spider=self.spider)

        return request

    def has_pending_requests(self):
        return len(self) > 0

def get_content_fingerprint(title, content):
    data = (title + content).strip().encode('utf-8')
    return md5(data).hexdigest()
