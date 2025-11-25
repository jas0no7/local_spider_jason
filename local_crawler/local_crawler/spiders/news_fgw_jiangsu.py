import copy
import re
import scrapy
from hashlib import md5
from lxml import etree


class JiangsuEnvSpider(scrapy.Spider):
    name = "news_fgw_jiangsu"
    allowed_domains = ["fzggw.jiangsu.gov.cn"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        # 添加必要的 Headers
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "application/xml, text/xml, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://fzggw.jiangsu.gov.cn",
            "Pragma": "no-cache",
            "Referer": "https://fzggw.jiangsu.gov.cn/col/col282/index.html?uid=423656&pageNum=3",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
    }

    _from = "江苏省发展和改革委员会"

    # 配置信息
    infoes = [
        {
            "url": "https://fzggw.jiangsu.gov.cn/module/web/jpage/dataproxy.jsp",
            "label": "发改要闻",
             "columnid": "282",
            "unitid": "423656",
            "webid": "3",
            "path": "/",
            "appid": "1",
            "sourceContentType": "1",
            "webname": "江苏省发展和改革委员会",
            "permissiontype": "0",
            # 详情页内容提取规则
            "body_xpath": "//div[contains(@class, 'bt-content')]",  # 你指定的 xpath
            "total_pages": 16,  # 对应你原代码中的 MAX_PAGE
            "perpage": 10,
            "page": 1


        }
    ]

    def start_requests(self):
        for info in self.infoes:
            # 计算第一页的分页参数
            start = (info["page"] - 1) * info["perpage"] + 1
            end = info["page"] * info["perpage"]

            # 构造 FormData (params 和 data 在 requests 中是分开的，但在 dataproxy.jsp 中通常都作为表单参数提交)
            formdata = {
                "col": "1",
                "appid": info["appid"],
                "webid": info["webid"],
                "path": info["path"],
                "columnid": info["columnid"],
                "sourceContentType": info["sourceContentType"],
                "unitid": info["unitid"],
                "webname": info["webname"],
                "permissiontype": info["permissiontype"],
                "startrecord": str(start),
                "endrecord": str(end),
                "perpage": str(info["perpage"])
            }

            yield scrapy.FormRequest(
                url=info["url"],
                formdata=formdata,
                callback=self.parse_list,
                meta=copy.deepcopy(info),
                dont_filter=True
            )

    def parse_list(self, response):
        meta = response.meta
        page = meta["page"]
        total_pages = meta["total_pages"]
        perpage = meta["perpage"]

        # 判断是否无数据
        if b"<record><![CDATA[" not in response.body:
            self.logger.info("无更多数据，停止循环")
            return

        try:
            # 解析 XML
            # Scrapy response.text 可能包含编码问题，这里直接用 body 解析更安全，或者确保 encoding
            xml_text = response.text
            root = etree.fromstring(xml_text.encode('utf-8'))
            records = root.xpath('//record')

            for record in records:
                cdata_content = record.text
                if not cdata_content:
                    continue

                # 解析 CDATA 中的 HTML 片段
                html_element = etree.fromstring(cdata_content)

                # 提取链接和标题
                a_tag = html_element.xpath('.//a')[0]
                title = a_tag.get('title')
                partial_url = a_tag.get('href')

                # 提取时间
                span_tag = html_element.xpath('.//span')[0]
                publish_time = span_tag.text

                if not partial_url:
                    continue

                # 拼接完整 URL
                if partial_url.startswith("http"):
                    url = partial_url
                else:
                    url = f'https://fzggw.jiangsu.gov.cn{partial_url}'

                # 过滤掉非详情页链接（如 pdf 直接下载）
                if url.lower().endswith(".pdf"):
                    continue

                detail_meta = {
                    "label": meta["label"],
                    "title": title,
                    "publish_time": publish_time,
                    "body_xpath": meta["body_xpath"]
                }

                yield scrapy.Request(
                    url=url,
                    callback=self.parse_detail,
                    meta=detail_meta,
                    dont_filter=True
                )

        except Exception as e:
            self.logger.error(f"解析列表页 XML 失败: {e}")

        # 翻页逻辑
        if page < total_pages:
            page += 1
            meta["page"] = page

            start = (page - 1) * perpage + 1
            end = page * perpage

            # 重新构造下一页的 FormData
            formdata = {
                "col": "1",
                "appid": meta["appid"],
                "webid": meta["webid"],
                "path": meta["path"],
                "columnid": meta["columnid"],
                "sourceContentType": meta["sourceContentType"],
                "unitid": meta["unitid"],
                "webname": meta["webname"],
                "permissiontype": meta["permissiontype"],
                "startrecord": str(start),
                "endrecord": str(end),
                "perpage": str(perpage)
            }

            yield scrapy.FormRequest(
                url=meta["url"],
                formdata=formdata,
                callback=self.parse_list,
                meta=copy.deepcopy(meta),
                dont_filter=True
            )

    def parse_detail(self, response):
        """
        完全复用模板的 parse_detail 逻辑
        """
        meta = response.meta
        url = response.url
        title = meta["title"]

        # 时间清洗逻辑：优先使用列表页时间，如果为空则从正文或源码中正则提取
        publish_time = meta.get("publish_time")
        if not publish_time:
            publish_time = "".join(response.xpath("//publishtime/text()").getall()).strip() or \
                           "".join(re.findall(r"发布日期.*?(\d{4}-\d{2}-\d{2})", response.text))

        body_xpath = meta["body_xpath"]

        # 获取正文 HTML
        body_html = " ".join(response.xpath(body_xpath).getall())

        # 获取纯文本内容 (对应你原代码中的 text 提取逻辑)
        content = " ".join(response.xpath(f"{body_xpath}//text()").getall()).strip()

        # 提取图片
        images = [
            response.urljoin(i)
            for i in response.xpath(f"{body_xpath}//img/@src").getall()
        ]

        # 提取附件
        attachments = [
            response.urljoin(a.xpath("./@href").get())
            for a in response.xpath(
                '//a[contains(@href, ".pdf") or contains(@href, ".doc") '
                'or contains(@href, ".docx") or contains(@href, ".xls") '
                'or contains(@href, ".xlsx") or contains(@href, ".zip") '
                'or contains(@href, ".rar")]'
            )
        ]

        yield {
            "_id": md5(f"{url}{title}".encode("utf-8")).hexdigest(),
            "url": url,
            "label": meta["label"],
            "title": title,
            "publish_time": publish_time,
            "body_html": body_html,
            "content": content,
            "images": images,
            "attachments": attachments,
            "spider_from": self._from
        }