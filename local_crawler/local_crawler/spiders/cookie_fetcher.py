import subprocess
from curl_cffi import requests
from lxml import etree
from loguru import logger


class CookieFetcher:
    """
    负责生成湖北省生态环境厅 412 防火墙 Cookie 的工具类。
    Spider 或 DownloaderMiddleware 调用此类来获取最新 Cookie。
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

    # ==========================================================
    # 生成可用 Cookie
    # ==========================================================
    def fetch(self, url):
        logger.info(f"[CookieFetcher] 开始获取 cookies：{url}")

        # -------------------------------
        # 1. 第一次 GET（触发跳转）
        # -------------------------------
        r1 = self.session.get(url, headers=self.base_headers)
        logger.info(f"[CookieFetcher] 第一次访问状态：{r1.status_code}")

        tree = etree.HTML(r1.text)

        # -------------------------------
        # 2. 解析 3 个 JS 文件
        # -------------------------------
        content_str = tree.xpath('//meta[2]/@content')[0]
        script1 = tree.xpath('//script[1]/text()')[0]
        script2_url = "https://sthjt.hubei.gov.cn" + tree.xpath('//script[2]/@src')[0]

        js_code = self.session.get(script2_url, headers=self.base_headers).text

        # 写入 JS 文件供 env.js 使用
        with open('./content.js', 'w', encoding='utf-8') as f:
            f.write(f'content="{content_str}";')

        with open('./ts.js', 'w', encoding='utf-8') as f:
            f.write(script1)

        with open('./cd.js', 'w', encoding='utf-8') as f:
            f.write(js_code)

        logger.info("[CookieFetcher] content.js / ts.js / cd.js 写入完毕")

        # -------------------------------
        # 3. 基础 cookie
        # -------------------------------
        try:
            cookies = r1.cookies.get_dict()
        except:
            cookies = {}
            for c in str(r1.cookies).split(";"):
                if "=" in c:
                    k, v = c.strip().split("=", 1)
                    cookies[k] = v

        # -------------------------------
        # 4. Node env.js 生成最终 Cookie
        # -------------------------------
        logger.info("[CookieFetcher] 调用 Node env.js 生成最终 cookie")
        result = subprocess.run(
            ['node', 'env.js'],
            capture_output=True,
            text=True
        )

        val = result.stdout.strip()

        if not val:
            logger.error("错误：env.js 没有输出 cookie 值！")
        else:
            cookies["924omrTVcFchP"] = val

        logger.info(f"[CookieFetcher] 最终 cookies: {cookies}")

        return cookies
