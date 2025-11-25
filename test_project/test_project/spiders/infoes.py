infoes = [
    {
        'url': 'https://gxt.jiangsu.gov.cn/col/col80181/index.html',
        'params': {"page": 1},               # 使用 page
        'label': "统计信息",
        'body_xpath': '//*[@id="Zoom"]',
        'total': 9,
        'page': 1,
        'base_url': 'https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp'
    },
    {
        'url': 'https://gxt.jiangsu.gov.cn/col/col89736/index.html',
        'params': {"page": 1},
        'label': "政策文件",
        'body_xpath': '//*[@id="Zoom"]',
        'total': 7,
        'page': 1,
        'base_url': 'https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp'
    },
    {
        'url': 'https://gxt.jiangsu.gov.cn/col/col80179/index.html',
        'params': {"page": 1},
        'label': "政策解读",
        'body_xpath': '//*[@id="Zoom"]',
        'total': 5,
        'page': 1,
        'base_url': 'https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp'
    },
    {
        'url': 'https://gxt.jiangsu.gov.cn/col/col83658/index.html',
        'params': {"page": 1},             # ❗省级政策分页也是 page
        'label': "省级政策",
        'body_xpath': '//*[@id="Zoom"]',
        'total': 63,                       # 根据 totalRecord=62，我写成 63
        'page': 1,
        'base_url': 'https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp'
    },
    {
        'url': 'https://gxt.jiangsu.gov.cn/col/col80181/index.html',
        'params': {"page": 1},
        'label': "数据统计 · 统计信息",
        'body_xpath': '//*[@id="Zoom"]',
        'total': 9,
        'page': 1,
        'base_url': 'https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp'
    },
    {
        'url': 'https://gxt.jiangsu.gov.cn/col/col80182/index.html',
        'params': {"page": 1},
        'label': "工作动态",
        'body_xpath': '//*[@id="Zoom"]',
        'total': 20,    # 你要让我查我也能查
        'page': 1,
        'base_url': 'https://gxt.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp'
    }
]
