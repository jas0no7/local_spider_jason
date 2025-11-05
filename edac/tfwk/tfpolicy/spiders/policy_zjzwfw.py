import copy
import json
from hashlib import md5
from time import time
from urllib.parse import urlencode
import scrapy
from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider
from ..items import DataItem
from ..mydefine import get_now_date, get_attachment


class DataSpider(CrawlSpider):
    name = 'policy_zjzwfw'
    allowed_domains = ['mapi.zjzwfw.gov.cn', 'zjzwfw.gov.cn']

    _from = "浙江政务服务网"

    dupefilter_field = {"batch": "20241206"}

    referer_base = "https://mapi.zjzwfw.gov.cn/web/mgop/gov-open/zj/2001941911/reserved/index.html"

    common_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://mapi.zjzwfw.gov.cn",
        "Pragma": "no-cache",
        "Referer": referer_base + "?",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "header_optimus_auth_request_token": "01fdaf34fd474896bab0a1aedddd835c",
    }

    mgop_url = "https://mapi.zjzwfw.gov.cn/h5/mgop"
    list_api = "mgop.gw.sjzj.zbcxqueryInstrumentHn"
    detail_api = "mgop.gw.sjzj.zbcxgetReportHtmlByCondition"
    ak = "udqmn52d+2001941911+elgttz"

    # 循环配置来自 for_xunhuan.py
    categories = {"年度": "N", "季度": "J", "月度": "Y"}
    n_categories = {
        "交通邮电": "1100", "人口": "0200", "价格": "1200", "其他社会活动": "2600", "农业": "1400",
        "固定资产投资和房地产": "1800", "国内贸易": "2000", "国民经济核算": "1300", "城市建设": "0500",
        "对外经济": "2100", "就业与工资": "0300", "居民住户": "2700", "居民收支": "1900", "工业": "1500",
        "建筑业": "1700", "教育": "2300", "数字化转型": "540617cec8d84ae7b09019d86dbc08a0",
        "文化体育卫生": "2500", "旅游": "2200", "服务业": "0400", "环境保护": "0600", "科技": "2400",
        "能源": "1600", "行政区划和自然资源": "0100", "财政": "0900", "金融": "1000"
    }
    j_categories = {
        "价格": "1200", "农业": "1400", "国民经济核算": "1300", "居民收支": "1900",
        "数字化转型": "540617cec8d84ae7b09019d86dbc08a0"
    }
    y_categories = {
        "价格": "1200", "固定资产投资和房地产": "1800", "国内贸易": "2000", "工业": "1500",
        "数字化转型": "540617cec8d84ae7b09019d86dbc08a0", "服务业": "0400", "能源": "1600"
    }

    def generate_sign(self, token: str, ak: str, api: str, ts: str, data: str) -> str:
        sign_str = f"token={token}&ak={ak}&api={api}&ts={ts}&data={data}"
        return md5(sign_str.encode('utf-8')).hexdigest().lower()

    def start_requests(self):
        """根据 categories / n/j/y_categories 组合构造 infoes 列表"""
        infoes = []
        for bgqb_name, bgqb_data in self.categories.items():
            if bgqb_name == "年度":
                for group_name, group_urn in self.n_categories.items():
                    # CHANGED: 携带 bgqb_name 与 group_name，不再生成 label
                    infoes.append({
                        "bgqb_name": bgqb_name,  # CHANGED
                        "group_name": group_name,  # CHANGED
                        "bgqb": bgqb_data,
                        "groupUrn": group_urn
                    })
            elif bgqb_name == "季度":
                for group_name, group_urn in self.j_categories.items():
                    infoes.append({
                        "bgqb_name": bgqb_name,  # CHANGED
                        "group_name": group_name,  # CHANGED
                        "bgqb": bgqb_data,
                        "groupUrn": group_urn
                    })
            else:
                for group_name, group_urn in self.y_categories.items():
                    infoes.append({
                        "bgqb_name": bgqb_name,  # CHANGED
                        "group_name": group_name,  # CHANGED
                        "bgqb": bgqb_data,
                        "groupUrn": group_urn
                    })

        # 发起请求
        for info in infoes:
            yield from self.request_list_page(
                page=1,
                pagerows=10,
                bgqb=info["bgqb"],
                group_urn=info["groupUrn"],
                bgqb_name=info["bgqb_name"],  # CHANGED
                group_name=info["group_name"]  # CHANGED
            )

    # CHANGED: 去掉 label 参数，改为传递 bgqb_name / group_name
    def request_list_page(self, page: int, pagerows: int, bgqb: str, group_urn: str, bgqb_name: str, group_name: str):
        post_data = {
            "data": [
                {"vtype": "pagination", "name": "pagerows", "data": pagerows},
                {"vtype": "pagination", "name": "totalrows", "data": 0},
                {"vtype": "pagination", "name": "page", "data": page},
                {"vtype": "pagination", "name": "sortName", "data": ""},
                {"vtype": "pagination", "name": "sortFlag", "data": ""}
            ]
        }

        payload = {
            "postData": json.dumps(post_data, separators=(',', ':')),
            "bh": "",
            "ddiInstance": "urn:ddi:ZJJCKSTAT:a463a4d9-806b-4fcc-8fc9-b43a8ee4298c:1",
            "groupUrn": group_urn,
            "studyUnitUrn": "",
            "instrumentSchemeUrn": "",
            "bgqb": bgqb,
            "projectId": "zj",
            "dqCode": "33"
        }

        data_str = json.dumps(payload, separators=(',', ':'))
        ts = str(int(time() * 1000))
        params = {"token": "", "ak": self.ak, "api": self.list_api, "ts": ts, "data": "null"}
        params["sign"] = self.generate_sign(**params)
        url = f"{self.mgop_url}?{urlencode(params)}"

        yield scrapy.Request(
            url=url,
            method='POST',
            body=data_str,
            headers=self.common_headers,
            callback=self.parse_list,
            meta={
                "proxy": None,
                "page": page,
                "pagerows": pagerows,
                "bgqb": bgqb,
                "groupUrn": group_urn,
                "bgqb_name": bgqb_name,  # CHANGED
                "group_name": group_name  # CHANGED
            },
            dont_filter=False,
        )

    def parse_list(self, response):
        page = response.meta.get('page', 1)
        pagerows = response.meta.get('pagerows', 10)
        bgqb = response.meta.get('bgqb')
        group_urn = response.meta.get('groupUrn')
        bgqb_name = response.meta.get('bgqb_name')  # CHANGED
        group_name = response.meta.get('group_name')  # CHANGED

        try:
            result = response.json()
            rows = (((result or {}).get("data") or {}).get("data") or [])[0]["data"]["rows"]
        except Exception:
            rows = []

        if not rows:
            return

        for row in rows:
            bs_item_urn = row.get("bsItemUrn")
            bgq = row.get("bgq")
            task_id = row.get("taskId")
            instrument_number = row.get("instrumentNumber")
            show_url = f"{self.common_headers['Referer']}#/wholeTableData/queryDetail?taskId={task_id}&bgq={bgq}&instrumentNumber={instrument_number}"

            yield from self.request_detail(
                bs_item_urn=bs_item_urn,
                bgq=bgq,
                dq_code="33",
                instrument_number=instrument_number,
                show_url=show_url,
                bgqb_name=bgqb_name,  # CHANGED
                group_name=group_name  # CHANGED
            )

        next_page = page + 1
        # CHANGED: 继续传递 bgqb_name / group_name
        yield from self.request_list_page(
            page=next_page,
            pagerows=pagerows,
            bgqb=bgqb,
            group_urn=group_urn,
            bgqb_name=bgqb_name,  # CHANGED
            group_name=group_name  # CHANGED
        )

    # CHANGED: 去掉 label 参数，改为传递 bgqb_name / group_name
    def request_detail(self, bs_item_urn: str, bgq: str, dq_code: str, instrument_number: str, show_url: str,
                       bgqb_name: str, group_name: str):
        post_data_detail = {
            "data": [
                {"vtype": "attr", "name": "bsItemUrn", "data": bs_item_urn},
                {"vtype": "attr", "name": "bgq", "data": bgq},
                {"vtype": "attr", "name": "dqCode", "data": dq_code},
                {"vtype": "attr", "name": "instrumentNumber", "data": instrument_number},
            ]
        }
        payload = {"postData": json.dumps(post_data_detail, separators=(',', ':'))}
        data_str = json.dumps(payload, separators=(',', ':'))
        ts = str(int(time() * 1000))
        params = {"token": "", "ak": self.ak, "api": self.detail_api, "ts": ts, "data": "null"}
        params["sign"] = self.generate_sign(**params)
        url = f"{self.mgop_url}?{urlencode(params)}"

        yield scrapy.Request(
            url=url,
            method='POST',
            body=data_str,
            headers=self.common_headers,
            callback=self.parse_detail,
            meta={
                "proxy": None,
                "show_url": show_url,
                "bgq": bgq,
                "bgqb_name": bgqb_name,  # CHANGED
                "group_name": group_name  # CHANGED
            },
            dont_filter=False,
        )

    def parse_detail(self, response):
        method = response.request.method
        req_body = response.request.body.decode('utf-8') if response.request.body else ''
        req_url = response.request.url

        show_url = response.meta.get('show_url')
        bgq = response.meta.get('bgq')
        bgqb_name = response.meta.get('bgqb_name')  # CHANGED
        group_name = response.meta.get('group_name')  # CHANGED

        try:
            result = response.json()
            data_nodes = (result.get("data") or {}).get("data") or []
        except Exception:
            data_nodes = []

        if not data_nodes or len(data_nodes) < 5:
            return

        publish_time = (data_nodes[0] or {}).get("data")
        title = (data_nodes[1] or {}).get("data")
        body_html = (data_nodes[4] or {}).get("data")

        if not body_html:
            return

        html = Selector(text=body_html)
        attachment_urls = html.xpath('//a')

        # CHANGED: 新增 category/theme；REMOVED: 'label'
        yield DataItem({
            # "_id": md5(f"{method}{req_url}{req_body}".encode('utf-8')).hexdigest(),
            # # 原来的：
            # # "_id": md5(f"{method}{req_url}{req_body}".encode('utf-8')).hexdigest(),
            #
            # # 改成：
            "_id": md5(f"{response.meta['bgq']}-{response.meta['group_name']}-{response.meta['show_url']}".encode('utf-8')).hexdigest(),

            "category": bgqb_name,  # CHANGED
            "theme": group_name,  # CHANGED
            "report_period": bgq,
            "url": show_url,
            'spider_from': self._from,
            'title': title,
            'author': "浙江省统计局",
            'publish_time': publish_time,
            'body_html': body_html,
            "content": ' '.join(html.xpath('//text()').extract()),
            "images": [response.urljoin(i) for i in html.xpath('//img/@src').extract()],
            "attachment": get_attachment(attachment_urls, show_url, self._from),
            "spider_date": get_now_date(),
            "spider_topic": "spider_zjzwfw_tabledata",
        })
