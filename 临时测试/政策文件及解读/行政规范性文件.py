import requests
from lxml import etree

headers = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Length": "0",
    "Origin": "https://sthjt.zj.gov.cn",
    "Pragma": "no-cache",
    "Referer": "https://sthjt.zj.gov.cn/module/xxgk/tree.jsp?divid=div1229106886&area=&rootName=&standardXxgk=1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    "cod": "148.79700.79701.20460",
    "arialoadData": "false",
    "_gscu_2050250814": "62135028hgky0712",
    "_gscbrs_2050250814": "1",
    "_gscs_2050250814": "62135028nv53zk12|pv:2",
    "SERVERID": "a6d2b4ba439275d89aa9b072a5b72803|1762135413|1762135027"
}
url = "https://sthjt.zj.gov.cn/module/xxgk/search.jsp"
infotypeId = {
    "上级文件": "B001A012",
    "国家法律法规": "B001A015",
    "地方性法规规章": "B001A013",
    "政府规章": "B001A014",
    "政策解读": "B001A011",
    "本机关其他政策文件": "B001AC001",
    "行政规范性文件": "B001G001"
}
for infotypename, infotypeid in infotypeId.items():
    for page in range(1, 11):
        params = {
            "divid": "div1229106886",
            "infotypeId": infotypeid,
            "jdid": "1756",
            "area": "",
            "sortfield": "",
            "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
            "standardXxgk": "1",
            "currpage": page
        }
    response = requests.post(url, headers=headers, cookies=cookies, params=params)

    html = response.text
    tree = etree.HTML(html)

    # 提取所有政策标题和链接
    links = tree.xpath('//div[@class="zfxxgk_zdgkc"]//ul/li')
    for a in links:
        title = a.xpath('./a/@title')[0]
        href = a.xpath('./a/@href')[0]
        publish_time = a.xpath('./b')[0]
        print(title, href,publish_time)
