import requests
from lxml import etree

# =====================================================
# 1. 请求配置（⚠️ 保留你原来的所有参数）
# =====================================================

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090a1b) XWEB/14185 Flue",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/wxpic,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "cache-control": "max-age=0",
    "x-wechat-key": "daf9bdc5abc4e8d09b5d51079168fe45e4b537ec5afb5d354db6f19350078490e7b297613e1bc6163cd056fd0ceb2fecbe48cd25f0eaa35ad7c59b09844165d8fbead6b3fa1cf88803a52a78ed85ca0a418a1c7cf1c1a676df6b5927a3bbe17a5b2a833705050104f4de0660c9a1e6eeac95b6e063f1232a7bd867453d4434b2",
    "x-wechat-uin": "MTk3MTgyODEzOQ%3D%3D",
    "exportkey": "n_ChQIAhIQqQmjT5XG8cuLvgKn8orK2xLRAQIE97dBBAEAAAAAALHGCzO3hfEAAAAOpnltbLcz9gKNyK89dVj0rGS4H7EUrVKs4XCJpUiKK7jgKZhh%2B20V7H5KqY%2BF%2FE%2B0nh%2BemdnyD%2BXdxEMAqm0WvPiZb7xbhMAqji8Klq0F%2Fcs0qPTM8rpjUq0xu7mqQ%2BHvgk1o%2FKQg1nQTqJjAr8eKHVXaTbRe3Kk1%2F1R1mgrxnoy8ogMsXJQij2MMY44mkLt1QZwPUt%2FUDJp5a0PWxxyeB6vjxNtiEjA6THNzK7uiv2h%2FkSmKoszXZldi",
    "upgrade-insecure-requests": "1",
    "referer": "https://mp.weixin.qq.com/",
    "accept-language": "zh-CN,zh;q=0.9",
}

cookies = {
    "wxtokenkey": "777",
    "wxuin": "1971828139",
    "devicetype": "Windows11x64",
    "version": "63090a1b",
    "lang": "zh_CN",
    "appmsg_token": "1352_cn%2FKJn5YnRD%2FKtdChyJeC4EtGjJf8mYeuOrHJs3RgGM2Ie3E4yrH2biwpDVh-XBpTitnSX9zWzBeB3bh",
    "pass_ticket": "3XOzYXUrhVm8MSmzoh4dGTgEfC7TOycfwGi0s9yYaVky3iFWoxpwjVyqHiaOh+4r",
    "wap_sid2": "CKvrnqwHEooBeV9ITUVKWllJRkFZYzU0dlZkTl9oOHBpYzRBeEVxNjZmTjZxODhFOHNzY0s5OHlyc0NETjg3ZTAzbklsWjdnVXgzNjJiN0RRMDR1U3FXcVZSTkRTVUZTVG1QSm1ZcWpSY1RvX3NIY3Z4QjNfVXMzRVBzVEZQZmVKRkZ2UHRVVkE4UEx5WVRBQUF+MJTxgsoGOA1AAQ==",
}

url = "https://mp.weixin.qq.com/s"

params = {
    "__biz": "MzU5NTEzODg0NQ==",
    "mid": "2247582545",
    "idx": "2",
    "sn": "3d1f160a4b9f49016ce85fbfedfb45be",
    "chksm": "ff678af88296ccbe0b408a34c1672342825f0ffc551551a567e410a0851c8a827e73af5bba4e",
    "scene": "126",
    "sessionid": "1765849134",
    "subscene": "7",
    "clicktime": "1765849235",
    "enterid": "1765849235",
    "key": "daf9bdc5abc4e8d09b5d51079168fe45e4b537ec5afb5d354db6f19350078490e7b297613e1bc6163cd056fd0ceb2fecbe48cd25f0eaa35ad7c59b09844165d8fbead6b3fa1cf88803a52a78ed85ca0a418a1c7cf1c1a676df6b5927a3bbe17a5b2a833705050104f4de0660c9a1e6eeac95b6e063f1232a7bd867453d4434b2",
    "ascene": "0",
    "uin": "MTk3MTgyODEzOQ==",
    "devicetype": "Windows 11 x64",
    "version": "63090a1b",
    "lang": "zh_CN",
    "countrycode": "CN",
    "exportkey": "n_ChQIAhIQqQmjT5XG8cuLvgKn8orK2xLRAQIE97dBBAEAAAAAALHGCzO3hfEAAAAOpnltbLcz9gKNyK89dVj0rGS4H7EUrVKs4XCJpUiKK7jgKZhh+20V7H5KqY+F/E+0nh+emdnyD+XdxEMAqm0WvPiZb7xbhMAqji8Klq0F/cs0qPTM8rpjUq0xu7mqQ+Hvgk1o/KQg1nQTqJjAr8eKHVXaTbRe3Kk1/1R1mgrxnoy8ogMsXJQij2MMY44mkLt1QZwPUt/UDJp5a0PWxxyeB6vjxNtiEjA6THNzK7uiv2h/kSmKoszXZldi",
    "acctmode": "0",
    "pass_ticket": "Bgc/FtFXeOyncIVUEPaipsPJn+p/SIEDFuZLDWCi2H83R/InDzofKwTGyW3vQFA/",
    "wx_header": "1",
}

# =====================================================
# 2. 请求页面
# =====================================================

response = requests.get(
    url,
    headers=headers,
    cookies=cookies,
    params=params,
    timeout=20
)
response.raise_for_status()

# =====================================================
# 3. 解析 HTML
# =====================================================

html = etree.HTML(response.text)

# 正文节点
content_nodes = html.xpath('//*[@id="js_content"]')
if not content_nodes:
    raise RuntimeError("未获取到 js_content，可能 key/exportkey 已失效")

content = content_nodes[0]

# =====================================================
# 4. 提取发布时间
# =====================================================

publish_time_nodes = html.xpath('//*[@id="publish_time"]/text()')
publish_time = publish_time_nodes[0].strip() if publish_time_nodes else ""

# =====================================================
# 5. 提取正文图片
# =====================================================

img_urls = content.xpath('.//img/@data-src')

# =====================================================
# 6. 输出结果
# =====================================================

print("发布时间:", publish_time)
print("图片数量:", len(img_urls))

for i, u in enumerate(img_urls):
    print(i, u)
