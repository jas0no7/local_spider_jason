# !/usr/bin/env python
# _*_ coding: utf-8 _*_

"""公共方法
"""

from base64 import b64encode, decodebytes
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, datetime
from functools import wraps
from hashlib import md5
from hmac import new as hmac_new
from inspect import currentframe
from json import dumps
from pathlib import Path
from queue import Queue
from random import uniform, choice, randint, sample
import sqlite3
from string import Formatter
import threading
from time import sleep
from zoneinfo import ZoneInfo

try:
    from loguru import logger  # type: ignore
except Exception:  # pragma: no cover
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    class _CompatLogger:
        def debug(self, msg, *args, **kwargs):
            logging.getLogger("spider").debug(str(msg))

        def info(self, msg, *args, **kwargs):
            logging.getLogger("spider").info(str(msg))

        def success(self, msg, *args, **kwargs):
            logging.getLogger("spider").info(str(msg))

    logger = _CompatLogger()

try:
    from Crypto.Cipher import AES, DES, DES3  # type: ignore
    from Crypto.Util.Padding import pad, unpad  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    try:
        from Cryptodome.Cipher import AES, DES, DES3  # type: ignore
        from Cryptodome.Util.Padding import pad, unpad  # type: ignore
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError("缺少加密依赖：请安装 `pycryptodome` 或 `pycryptodomex`") from e

import config

formatter = Formatter()


def try_except(return_value=None, is_log=False, logger_info=None):
    """
    异常装饰器
    :param return_value: 返回的值
    :param is_log: 是否开启日志
    :param logger_info: 日志内容
    :return:
    """

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            pop_is_log = kwargs.pop('is_log', is_log)
            logger_value = kwargs.pop('logger_info', logger_info) or '未定义日志输出'
            fields = [field_name for _, field_name, _, _ in formatter.parse(logger_value) if field_name]
            if not fields:
                logger_value = logger_value
            elif set(fields).issubset(kwargs.keys()):
                logger_value = logger_value.format(**kwargs)
            else:
                logger_value = '缺少参数, 日志格式化失败'

            frame = currentframe().f_back
            lineno = frame.f_lineno
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name
            function = "__main__" if function == "<module>" else function

            try:
                return_value_true = func(*args, **kwargs)
                if pop_is_log:
                    logger.success(f'调用文件: {filename} | 调用方法名: {function} | 调用方法行号: {lineno} | 提示消息: {logger_value} 成功')

                return return_value_true
            except Exception as e:
                logger.debug(f'调用文件: {filename} | 调用方法名: {function} | 调用方法行号: {lineno} | 提示消息: {logger_value} 失败, 异常: {e}')
                return return_value

        return inner

    return decorator


class MyKafkaProducer(object):
    """
    kafka 生产者
    """

    def __init__(self, max_request_size: int = 5242880):
        try:
            from kafka import KafkaProducer  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("kafka-python 未安装或不可用") from e

        bootstrap_servers = config.KAFKA.get("bootstrap_servers")
        # 连接生产者
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: dumps(v, ensure_ascii=False).encode('utf-8'),
            max_request_size=max_request_size,
            api_version=config.KAFKA.get("api_version", (2, 7))
        )

    def send(self, topic, value, key=None):
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
            logger.success(f'发送成功: {value}')

    def close(self):
        """
        关闭
        :return:
        """
        try:
            self.producer.close()
        except:
            pass


class MyThreadPoolExecutor(ThreadPoolExecutor):
    """
    线程池 限制队列大小 减少内存使用
    """

    def __init__(self, max_workers: int = 5, *args, **kwargs):
        super(MyThreadPoolExecutor, self).__init__(max_workers=max_workers, *args, **kwargs)
        self._work_queue = Queue(max_workers * 2)


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

    def chrome_browser_version(self):
        """
        谷歌浏览器版本
        :return:
        """
        return f'{randint(80, self.chrome_max_version)}.0.{randint(1000, 9000)}.{randint(10, 200)}'

    def firefox_browser_version(self):
        """
        火狐浏览器版本
        :return:
        """
        return {
            'build_version': f'{randint(50, self.firefox_max_version)}.0',
            'geckotrail': datetime.fromtimestamp(randint(1577808000, int(get_now_date(fmt=None).timestamp()))).strftime('%Y%m%d')
        }

    def get_edge_browser_version(self):
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

    def get_android_chrome_build(self):
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

    def win_firefox(self):
        info = self.firefox_browser_version()
        return f'Mozilla/5.0 (Windows NT {choice(self.win_version)}; {choice(self.win_cpu)}; rv:{info.get("build_version")}) Gecko/{info.get("geckotrail")} Firefox/{info.get("build_version")}'

    def win_chrome(self):
        return f'Mozilla/5.0 (Windows NT {choice(self.win_version)}; {choice(self.win_cpu)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_browser_version()} Safari/537.36'

    def win_edge(self):
        info = self.get_edge_browser_version()
        return f'Mozilla/5.0 (Windows NT {choice(self.win_version)}; {choice(self.win_cpu)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{info.get("build_version")} Safari/537.36 Edg/{info.get("edge_build_version")}'

    def mac_firefox(self):
        info = self.firefox_browser_version()
        return f'Mozilla/5.0 (Macintosh; Intel Mac OS X {randint(10, 12)}.{randint(0, 15)}.{randint(0, 12)}; rv:{info.get("build_version")}) Gecko/{info.get("geckotrail")} Firefox/{info.get("build_version")}'

    def mac_chrome(self):
        mac_chrome_version = f"{randint(10, 12)}.{randint(0, 15)}.{randint(0, 12)}".replace(".", "_")
        return f'Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_chrome_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_browser_version()} Safari/537.36'

    def mac_edge(self):
        mac_edge_version = f"{randint(10, 12)}.{randint(0, 15)}.{randint(0, 12)}".replace(".", "_")
        return f'Mozilla/5.0 (Macintosh; Intel Mac OS X {mac_edge_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.get_edge_browser_version().get("build_version")} Safari/537.36 Edg/{self.get_edge_browser_version().get("edge_build_version")}'

    def linux_firefox(self):
        info = self.firefox_browser_version()
        return f'Mozilla/5.0 (X11; {choice(self.linux_version)} {choice(self.linux_cpu)}) Gecko/{info.get("geckotrail")} Firefox/{info.get("build_version")}'

    def linux_chrome(self):
        return f'Mozilla/5.0 (X11; {choice(self.linux_version)} {choice(self.linux_cpu)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_browser_version()} Safari/537.36'

    def linux_edge(self):
        info = self.get_edge_browser_version()
        return f'Mozilla/5.0 (X11; {choice(self.linux_version)} {choice(self.linux_cpu)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{info.get("build_version")} Safari/537.36 Edg/{info.get("edge_build_version")}'

    @staticmethod
    def ios():
        return f'Mozilla/5.0 (iPhone; CPU iPhone OS {randint(10, 15)}_{randint(0, 10)}_{randint(0, 10)} like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{randint(9, 15)}.{randint(0, 10)}.{randint(0, 10)} Mobile/15E148 Safari/604.1'

    def android_firefox(self):
        info = self.firefox_browser_version()
        return f'Mozilla/5.0 (Android {randint(7, 12)}.{randint(0, 1)}.{randint(0, 1)}; Mobile; rv:{self.firefox_browser_version().get("build_version")}) Gecko/{info.get("geckotrail")} Firefox/{info.get("build_version")}'

    def android_chrome(self):
        return f'Mozilla/5.0 (Linux; Android {randint(7, 12)}.{randint(0, 1)}.{randint(0, 1)}; {self.get_android_chrome_build()}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_browser_version()} Mobile Safari/537.36'

    def random(self):
        func = [
            self.win_chrome,
            self.win_firefox,
            self.win_edge,
            self.mac_edge,
            self.mac_chrome,
            self.mac_firefox,
            self.linux_edge,
            self.linux_chrome,
            self.linux_firefox,
            self.ios,
            self.android_chrome,
            self.android_firefox
        ]
        return choice(func)()

    def random_pc(self):
        func = [
            self.win_chrome,
            self.win_firefox,
            self.win_edge,
            self.linux_edge,
            self.linux_chrome,
            self.linux_firefox,
            self.mac_edge,
            self.mac_chrome,
            self.mac_firefox,
        ]
        return choice(func)()

    def random_win(self):
        return choice([
            self.win_chrome,
            self.win_firefox,
            self.win_edge
        ])()

    def random_mac(self):
        return choice([
            self.mac_edge,
            self.mac_chrome,
            self.mac_firefox
        ])()

    def random_linux(self):
        return choice([
            self.linux_edge,
            self.linux_chrome,
            self.linux_firefox
        ])()

    def random_mobile(self):
        func = [
            self.ios,
            self.android_firefox,
            self.android_chrome
        ]
        return choice(func)()

    def random_android(self):
        func = [
            self.android_firefox,
            self.android_chrome
        ]
        return choice(func)()


class ProxyPool(object):
    """
    代理 ip
    """

    def __init__(self, connect_info: dict = None):
        connect_info = connect_info or config.REDIS_PROXY_181
        try:
            from redis import Redis, ConnectionPool  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("redis 未安装或不可用，无法使用 ProxyPool") from e

        connect = {
            "host": connect_info.get("host"),
            "port": connect_info.get("port"),
            "db": connect_info.get("db"),
            "max_connections": connect_info.get("max_connections"),
            "decode_responses": True
        }
        self.redis = Redis(connection_pool=ConnectionPool(**connect))

        proxy_params = config.PROXY
        self._proxy_key = proxy_params.get("key")
        # 用户名密码
        self._ip_user = proxy_params.get("user")
        self._ip_passwd = proxy_params.get("passwd")
        # 替换键
        self._replace = f'{self._proxy_key}:'

    @try_except(return_value=[], is_log=False, logger_info='查找所有满足 {key} 条件的key')
    def string_keys(self, key, **kwargs):
        """
        查找所有满足条件的key
        :param key:
        :return:
        """
        return self.redis.keys(key)

    def get_proxy(self):
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
                "http": f"http://{self._ip_user}:{self._ip_passwd}@{ip_port}",
                "https": f"http://{self._ip_user}:{self._ip_passwd}@{ip_port}"
            }


class MyCrypto(object):
    """
    加密解密 如 aes des 等
    """

    @try_except(return_value='', is_log=True, logger_info='AES/CBC加密 {text}')
    def aes_cbc_encrypt(self, key: str, iv: str, text: str, style='pkcs7', **kwargs) -> str:
        """
        AES CBC 加密
        :param key: 加密的key
        :param iv: 加密的偏移向量
        :param text: 加密的文本
        :param style: 填充方式
        :return:
        """
        if style == 'NoPadding':
            length = 16
            count = len(text.encode('utf-8'))
            if count % length != 0:
                add = length - (count % length)
            else:
                add = 0
            enc_data = text + ('\0' * add)
            encryptedbytes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8')).encrypt(enc_data.encode('utf-8'))
        else:
            encryptedbytes = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8')).encrypt(pad(text.encode('utf-8'), AES.block_size))
        return b64encode(encryptedbytes).decode('utf-8')

    @try_except(return_value='', is_log=True, logger_info='HMAC/MD5加密 {text}')
    def hmac_md5(self, key: str, text: str, **kwargs) -> str:
        """
        hmac md5 加密
        :param key: 加密key
        :param text: 需要加密的文本
        :return:
        """
        return hmac_new(key.encode('utf-8'), text.encode('utf-8'), md5).hexdigest()

    @try_except(return_value='', is_log=True, logger_info='DES3/CBC解密 {text}')
    def des3_cbc_decrypt(self, key: str, iv: str, text: str, **kwargs) -> str:
        """
        DES3 CBC 解密
        :param key: 解密的key
        :param iv: 解密的偏移向量
        :param text: 需要解密的文本
        :return:
        """
        _decrypted = DES3.new(key.encode('utf-8'), DES3.MODE_CBC, iv[:8].encode('utf-8')).decrypt(decodebytes(text.encode('utf-8')))
        return unpad(_decrypted, DES3.block_size).decode('utf-8')

    @try_except(return_value='', is_log=True, logger_info='DES/CBC加密 {text}')
    def des_cbc_encryt(self, key: str, iv: str, text: str, **kwargs) -> str:
        """
        DES CBC 加密
        :param key: 加密的key
        :param iv: 加密的偏移向量
        :param text: 加密文本
        :return:
        """
        res = DES.new(key[:8].encode('utf-8'), DES.MODE_CBC, iv[:8].encode('utf-8')).encrypt(pad(text.encode('utf-8'), DES.block_size, style='pkcs7'))
        return b64encode(res).decode('utf-8')

    @try_except(return_value='', is_log=True, logger_info='AES/CBC解密 {text}')
    def aes_cbc_decrypt(self, key: str, iv: str, text: str, style='pkcs7', **kwargs) -> str:
        """
        AES ECB 解密
        :param key: 解密的key
        :param iv: 解密的偏移向量
        :param text: 需要解密的文本
        :param style: 填充方式
        :return:
        """
        _decrypted = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8')).decrypt(decodebytes(text.encode('utf-8')))
        if style == 'NoPadding':
            return _decrypted.decode('utf-8')
        else:
            return unpad(_decrypted, AES.block_size).decode('utf-8')


class MyRedis(object):
    """
    redis
    """

    def __init__(self, connect_info: dict = None):
        """
        :param connect_info: 连接redis参数
        """
        connect_info = connect_info or config.REDIS_FILTER_181
        try:
            from redis import Redis, ConnectionPool  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("redis 未安装或不可用，无法使用 MyRedis") from e

        connect = {
            "host": connect_info.get("host"),
            "port": connect_info.get("port"),
            "db": connect_info.get("db"),
            "max_connections": connect_info.get("max_connections"),
            "decode_responses": True
        }
        self.redis = Redis(connection_pool=ConnectionPool(**connect))

    @try_except(return_value=None, is_log=True, logger_info='查找 {key} 的值')
    def string_get(self, key, **kwargs):
        """
        查找key的值
        :param key:
        :return:
        """
        return self.redis.get(key)

    @try_except(return_value=False, is_log=True, logger_info='设置 {name} 的值 {value} 并设置过期时间 {expire_time}')
    def string_setex(self, name, expire_time, value='', **kwargs):
        """
        设置name的值value并设置过期时间expire_time
        :param name: key
        :param expire_time: 过期时间
        :param value: 值 默认为空
        :return:
        """
        self.redis.setex(name, expire_time, value)

    @try_except(return_value=False, is_log=True, logger_info='创建初始容量为 {capacity} 的过滤器 {key}')
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

    @try_except(return_value=False, is_log=True, logger_info='在过滤器 {key} 中添加 {value}')
    def add(self, key, value, **kwargs):
        """
        添加 存在则跳过
        :param key: redis中的key
        :param value: 添加的值
        :return:
        """
        return self.redis.cf().addnx(key, value)

    @try_except(return_value=0, is_log=True, logger_info='查找过滤器 {key} 中是否存在 {value}')
    def exists(self, key, value, **kwargs):
        """
        在 key 中是否存在 value
        :param key:
        :param value:
        :return:
        """
        return self.redis.cf().exists(key, value)


def get_now_date(fmt='%Y-%m-%d %H:%M:%S'):
    """
    获取当前时区时间
    :param fmt: 日期转字符串格式
    :return:
    """
    return datetime.now(tz=ZoneInfo(key='PRC')).strftime(fmt) if fmt else datetime.now(tz=ZoneInfo(key='PRC'))


def scheduler(scheduler_info: list, replace_existing: bool = True):
    """
    Apscheduler 定时任务
    :param scheduler_info: 执行的任务信息
    :param replace_existing: 存在任务是否替换 True:替换
    :return:
    """
    try:
        from apscheduler.schedulers.background import BlockingScheduler  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("缺少 apscheduler 依赖，无法使用 scheduler()") from e

    blocking_scheduler = BlockingScheduler(timezone='Asia/Shanghai')

    # 记录任务是否已经过期
    run_list = []
    for info in scheduler_info:
        cron = info.get('cron')
        if 'trigger' not in cron:
            cron.update({
                "trigger": "cron"
            })

        trigger = cron.get('trigger')
        if info.get('is_now', False) and trigger in ["cron"]:
            cron.update({
                'next_run_time': get_now_date(fmt=None) + timedelta(seconds=5)
            })

        job_id = info.get('job_id')
        if not job_id:
            path = Path(info.get('file_path', '未知/未知'))
            job_id = f'spider_{path.parent.stem}_{path.stem}'

        _message = info.get('message')
        run_date = f'{cron.get("hour", "*")}:{cron.get("minute", "*")}:{cron.get("second", "*")}'
        end_date = cron.get('end_date')
        if end_date:
            _end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S") if isinstance(end_date, str) else end_date
            if _end_date < get_now_date(fmt=None):
                logger.info(f'定时任务 {job_id} 结束时间为 {_end_date.strftime("%Y-%m-%d %H:%M:%S")}, 不满足条件！')
                run_list.append(False)
                continue

        logger.info(f'等待定时任务中, {job_id} {_message} 运行时间为: {run_date}, 结束时间: {end_date}')
        run_list.append(True)
        blocking_scheduler.add_job(info.get('func'), id=job_id, args=info.get('args'), kwargs=info.get('kwargs'), replace_existing=replace_existing, **cron)

    # 如果全部过期就不用启用定时任务
    if any(run_list):
        blocking_scheduler.start()


_local_filter_lock = threading.Lock()
_local_filter_conn: sqlite3.Connection | None = None


def _get_local_filter_conn() -> sqlite3.Connection:
    """
    本地去重（替代 Redis CuckooFilter）：使用 SQLite 存储 md5 后的 key。
    """
    global _local_filter_conn
    if _local_filter_conn is not None:
        return _local_filter_conn

    out_dir = Path("./output")
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(out_dir / "charge_filter.sqlite3", timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("CREATE TABLE IF NOT EXISTS seen (k TEXT PRIMARY KEY)")
    conn.commit()
    _local_filter_conn = conn
    return conn


def charge_filter(value):
    """
    本地去重：存在返回 True，不存在则写入并返回 False。
    """
    digest = md5(value).hexdigest() if isinstance(value, bytes) else md5(value.encode("utf-8")).hexdigest()
    conn = _get_local_filter_conn()
    with _local_filter_lock:
        try:
            conn.execute("INSERT INTO seen(k) VALUES (?)", (digest,))
            conn.commit()
            return False
        except sqlite3.IntegrityError:
            return True


def date_interval(in_date=None, step=30):
    """
    批次 ---> 2022-07-20 10:25:08 --> 属于 20220720100000 批次
    :param in_date: 需要转换的日期
    :param step: 每隔多久分一个区间
    :return: 转换后的批次
    """
    date_date = datetime.strptime(in_date, '%Y-%m-%d %H:%M:%S') if in_date else datetime.now(tz=ZoneInfo(key='PRC'))
    return date_date.replace(minute=(date_date.minute // step) * step).strftime('%Y%m%d%H%M00')


def charge_kafka(item: dict):
    """
    兼容旧逻辑：不再写 Kafka，直接写本地 JSONL（./output/charge_kafka.jsonl）。
    """
    out_dir = Path("./output")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "charge_kafka.jsonl"
    line = dumps(item, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def current_week_monday(date_string: str = None, weekday: int = 1, week: int = 0):
    """
    获取date_string日期所在周的星期weekday的日期, 1:星期一 2: 星期二 3: 星期三 4: 星期四
    :param date_string: 是否使用消息提醒
    :param weekday: 是否使用消息提醒
    :param week: date_string后的第week周的weekday日期，如 2023-08-17后的第1周星期一的日期，就是下一周星期一的日期
    :return:
    """
    try:
        if date_string:
            try:
                from pandas import to_datetime  # type: ignore

                date = to_datetime(date_string)
            except Exception:
                # 兜底：尽量用标准库解析常见格式
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        date = datetime.strptime(date_string, fmt).replace(tzinfo=ZoneInfo(key="PRC"))
                        break
                    except Exception:
                        date = None
                if date is None:
                    date = datetime.fromisoformat(date_string).replace(tzinfo=ZoneInfo(key="PRC"))
        else:
            date = get_now_date(fmt=None)
    except Exception as e:
        logger.debug(f'传入日期 {date_string} 错误, 默认当前日期: {e}')
        date = get_now_date(fmt=None)

    return date - timedelta(days=date.weekday() - weekday + 1) + timedelta(weeks=week)
