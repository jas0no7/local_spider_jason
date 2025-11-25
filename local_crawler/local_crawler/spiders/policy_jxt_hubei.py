infoes = [
    {
        "url": "http://jxt.hubei.gov.cn/bmdt/jjyx/index.shtml",
        "label": "经济运行",
        "detail_xpath": "//ul[@class='list-b']/li",
        # 列表页每条的正文链接
        "url_xpath": ".//h4/a/@href",
        # 标题：用 h4 下的 a 标签文本
        "title_xpath": "string(.//h4/a)",
        # 发布日期：在 p class="date" 标签里，例如：“发布时间：2025-11-19...”
        "publish_time_xpath": ".//p[@class='date']",
        # 详情页正文（无法确定，暂使用常见值）
        "body_xpath": "//div[contains(@class,'TRS_UEDITOR')]",
        # createPageHTML(63, 0, "index", "shtml", ..., 435) => 总页数 63
        "total": 63,
        "page": 1,
        # 假设第二页开始是 index_1.shtml、index_2.shtml...
        "base_url": "http://jxt.hubei.gov.cn/bmdt/jjyx/index_{}.shtml",
    }
]
