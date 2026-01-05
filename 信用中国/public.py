from random import choice
from time import sleep
from random import uniform
import config
from loguru import logger


class ProxyPool(object):
    """
    代理 ip（无 Redis 版本：内存代理池）
    """

    def __init__(self, proxies=None):
        """
        :param proxies: 可选，代理列表，形如：
                        ["1.2.3.4:8080", "5.6.7.8:3128"]
                        或者 [{"ip_port": "1.2.3.4:8080"}, ...] 也行（下面做了兼容）
        """
        proxy_params = config.PROXY
        self._proxy_key = proxy_params.get("key")  # 仍保留字段，避免你别处引用
        self._ip_user = proxy_params.get("user")
        self._ip_passwd = proxy_params.get("passwd")

        # 1) 优先使用外部传入
        # 2) 否则尝试从 config.PROXY 里拿（你可以把代理列表放到 config.PROXY["ips"]）
        proxies = proxies if proxies is not None else proxy_params.get("ips", [])

        # 兼容几种格式：["ip:port"] / [{"ip_port":"ip:port"}] / [{"ip":"", "port":""}]
        self._proxies = self._normalize(proxies)

    def _normalize(self, proxies):
        normalized = []
        for p in proxies or []:
            if isinstance(p, str):
                normalized.append(p.strip())
            elif isinstance(p, dict):
                if "ip_port" in p and p["ip_port"]:
                    normalized.append(str(p["ip_port"]).strip())
                elif "ip" in p and "port" in p and p["ip"] and p["port"]:
                    normalized.append(f'{p["ip"]}:{p["port"]}'.strip())
        # 去重 + 过滤空值
        normalized = [x for x in dict.fromkeys(normalized) if x]
        return normalized


    def string_keys(self, key, **kwargs):
        """
        兼容旧接口：以前是 redis.keys()。
        现在不做 key 查找，直接返回当前内存里的所有代理“键”。
        """
        # 如果你确实还想按 key 做过滤（例如 key="xxx*"），可以在这里加简单匹配
        return list(self._proxies)

    def add_proxies(self, proxies):
        """动态追加代理"""
        new_items = self._normalize(proxies)
        if new_items:
            self._proxies = list(dict.fromkeys(self._proxies + new_items))

    def remove_proxy(self, ip_port: str):
        """移除不可用代理"""
        ip_port = (ip_port or "").strip()
        if not ip_port:
            return
        self._proxies = [p for p in self._proxies if p != ip_port]

    def get_proxy(self):
        """
        获取代理（随机）
        :return: {"http": "...", "https": "..."}
        """
        while True:
            if not self._proxies:
                logger.info("目前可用代理ip为空, 等待重新获取/注入")
                sleep(uniform(10, 20))
                continue

            ip_port = choice(self._proxies)
            auth = ""
            if self._ip_user and self._ip_passwd:
                auth = f"{self._ip_user}:{self._ip_passwd}@"

            # 你的原逻辑：http/https 都用 http://
            proxy_url = f"http://{auth}{ip_port}"
            return {"http": proxy_url, "https": proxy_url}
