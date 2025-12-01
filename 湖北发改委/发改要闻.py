infoes = [
    {
        'url': 'https://fgw.hubei.gov.cn/gzjj/dtyw/fgyw/index.shtml',
        'label': "发改要闻",
        'detail_xpath': '//ul[@class="list-t border6"]/li',
        'url_xpath': './a/@href',
        'title_xpath': './a/@title',
        'publish_time_xpath': './span',
        'body_xpath': '//div[@class="detail"]',
        'total': 553,
        'page': 1,
        'base_url': 'https://fgw.hubei.gov.cn/gzjj/dtyw/fgyw/index_{}.shtml'
    },
    {
        'url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgg/index.shtml',
        'label': "通知公告;公告",
        'detail_xpath': '//ul[@class="list-t border6"]/li',
        'url_xpath': './a/@href',  # ../../../fbjd/zc/zcwj/gg/202506/t20250626_5707084.shtml
        'title_xpath': './a/@title',
        'publish_time_xpath': './span',
        'body_xpath': '//div[@class="detail"]',
        'total': 21,
        'page': 1,
        'base_url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgg/index_{}.shtml'
    },
    {
        'url': 'https://fgw.hubei.gov.cn/gzjj/tzgg/wjgs/index.shtml',
        'label': "通知公告;公示",
        'detail_xpath': '//ul[@class="list-t border6"]/li',
        'url_xpath': './a/@href',  # ../../../fbjd/zc/zcwj/gg/202506/t20250626_5707084.shtml
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
        'url_xpath': './a/@href',  # ../../../fbjd/zc/zcwj/gg/202506/t20250626_5707084.shtml
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
        'url_xpath': './a/@href',  # ./202510/t20251022_5796016.shtml
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
        'url_xpath': './a/@href',  # ./202510/t20251022_5796016.shtml
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
        'url_xpath': './a/@href',  # ./202510/t20251022_5796016.shtml
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
        'url_xpath': './a/@href',  # ./202510/t20251022_5796016.shtml
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
        'url_xpath': './a/@href',  # ./202510/t20251022_5796016.shtml
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
        'url_xpath': './a/@href',  # ./202510/t20251022_5796016.shtml
        'title_xpath': './a/@title',
        'publish_time_xpath': './a/b',
        'body_xpath': '//div[@class="detail"]',
        'total': 8,
        'page': 1,
        'base_url': 'https://fgw.hubei.gov.cn/fgjj/sjsfg/sjfx/lx/gdsj/index_{}.shtml'
    },
]
