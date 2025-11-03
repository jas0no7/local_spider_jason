import requests


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
    "cod": "148.79700.79701.46047",
    "arialoadData": "false",
    "_gscu_2050250814": "62135028hgky0712",
    "_gscbrs_2050250814": "1",
    "_gscs_2050250814": "62135028nv53zk12|pv:2",
    "SERVERID": "a6d2b4ba439275d89aa9b072a5b72803|1762135500|1762135027"
}
url = "https://sthjt.zj.gov.cn/module/xxgk/search.jsp"
params = {
    "divid": "div1229106886",
    "infotypeId": "B001A011",
    "jdid": "1756",
    "area": "",
    "sortfield": "",
    "requestUrl": "https://sthjt.zj.gov.cn/col/col1229116546/index.html",
    "standardXxgk": "1"
}#政策解读
response = requests.post(url, headers=headers, cookies=cookies, params=params)

print(response.text)
print(response)