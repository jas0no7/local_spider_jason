import requests
import json


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b) XWEB/8555",
    "Content-Type": "application/json",
    "X-Channel-ID": "70001",
    "csecuuid": "e26ee4f48e974069280e2701cae8908a",
    "mtgsig": "{\"a1\":\"1.2\",\"a2\":1761874120991,\"a3\":\"1761873461327KUICOUU60e593ce0a815b08d658526270cd17d61432\",\"a4\":\"e97f0aea9a342f64ea0a7fe9642f349af59b9ede91b4aa44\",\"a5\":\"b+yYpmWL3IF7h8rKBUJEanulW/DWl0W/crPQXCvYStFVI98n1Ruso1O5AessgQ++uS34UCyJdgizwghOTRrAJ6Kj70YtUAbGMZk33RIAxCo/Mbb+lOnHlu2sV2YX6isXNZg0a5g9xD7ONGaSq+7rxgWZ1tlU3l0cpOs/DnDm70Pfo/BccQIcgcXnLJzVJ4rSw5Q9qttpNkZYIuOgPzKecp4x/pJ0K/mNM1LU5kI=\",\"a6\":\"w1.3VNHzXYQE7QNrtL024oztPkc8iq/j5IMnurOKxTzkxb7rxmuic/Sbul/D+dsILxBjDMB/usmMfkfz39x1Rz6d3V9TbXXyFQnmMs7F2OUSRyu2kMifjP1iwPGIzosFdKrlNcTaux9DKasROOb9ywDQxEhD4nACInRu0/HUMVBrnw9a1D2A4O2ZOMNw4hjuLee5yApT8n1+UW72X8Jn//Q53VFX90icwi9E47akKv5QIrLt+vKvcvk3HGH2cwdzaxCGXrO28o/H2TzlMJtMNm1JYxXLEXbKe1W9zH0A5siNSKZU0nI4t+bf2fUZRmW1Du3yUci4hLZC+vfViZ8WOBxrMDaXNjFK9xit8nItowFQUKhLM1WaQLaWgzOov+MU8UYjWgMUsp5/F85zI7b3LJeExZV/Js7dbtq7OIGhYWLkzJdynTog8Z8x1qNIwxLFud2PI6HMTy3HNuqGFXY0fRpOvaxH6wxBY3XRXUYgzTXsiczKKAoAUGkVds+/R/q53t15\",\"a7\":\"wxdbb4c5f1b8ee7da1\",\"x0\":3,\"d1\":\"674be12dd7f7143c51eb912f2ed4a197\"}",
    "xweb_xhr": "1",
    "X-Requested-With": "wxapp",
    "x-wxa-page": "pages/showsubs/order/confirm",
    "uuid": "e26ee4f48e974069280e2701cae8908a",
    "x-wxa-referer": "pages/showsubs/ticket-level/v2/index",
    "x-wxa-query": "%7B%22performance_id%22%3A%22438528%22%2C%22ticket_id%22%3A%2226761318%22%2C%22_isFromConfirmOrder%22%3A1%7D",
    "version": "wallet-v6.11.13",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wxdbb4c5f1b8ee7da1/1711/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
url = "https://wx.maoyan.com/maoyansh/myshow/ajax/tx/unifiedInfo"
params = {
    "wxOpenId": "o31Py0KZtXp9OCzcUblfe09sUmVA",
    "sellChannel": "7",
    "token": "MY_S_pquvI7M3IOlE2z9i-ShV4a65kAAAAwS3SxpiR5qvJsaT4kwhLVdB5ZcQF9i58s7hEXXnS10oIxyGmQv_nOwm768-_zAWGKAAAAwAAAAAEB",
    "clientPlatform": "1",
    "cityId": "59",
    "yodaReady": "wx",
    "csecappid": "wxdbb4c5f1b8ee7da1",
    "csecplatform": "3",
    "csecversionname": "wallet-v6.11.13",
    "csecversion": "1.4.0"
}
data = {
    "projectId": 438528,
    "showId": 3058717,
    "areaId": None,
    "ticketId": 26761318
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, params=params, data=data)

print(response.text)
print(response)