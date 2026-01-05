import time
import requests
from lxml import etree


BASE_URL = "https://jyt.zj.gov.cn"
LIST_API = "https://jyt.zj.gov.cn/module/jpage/dataproxy.jsp"

# =========================
# 不同栏目都放这里（后面你只加/改这一块）
# =========================
infoes = [
    {
        "label": "公告公示",
        "columnid": "1229266336",
        "unitid": "6258453",
        "referer": "https://jyt.zj.gov.cn/col/col1229266336/index.html?uid=6258453&pageNum=1",
    },
    {
        "label": "教育动态",
        "columnid": "1543974",
        "unitid": "4729348",
        "referer": "https://jyt.zj.gov.cn/col/col1543974/index.html?uid=4729348&pageNum=1",
    },
]

# =========================
# 公共请求头（Referer 每个栏目会覆盖）
# =========================

