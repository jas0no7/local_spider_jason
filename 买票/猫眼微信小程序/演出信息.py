import requests
import json


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b) XWEB/8555",
    "Content-Type": "application/json",
    "X-Channel-ID": "70001",
    "csecuuid": "e26ee4f48e974069280e2701cae8908a",
    "mtgsig": "{\"a1\":\"1.2\",\"a2\":1761874121303,\"a3\":\"1761873461327KUICOUU60e593ce0a815b08d658526270cd17d61432\",\"a4\":\"4ed987ee56902b7aee87d94e7a2b9056b9153879c33ea82f\",\"a5\":\"aiHukZOf/fI7h8QggOWLsNv2LV/wWr083C3BK9jiJRvuvVeNF0B6OyWJ6EIRzhupL4lzMu5mXyufegETtgApSu6XUgA7vx2EhpHC6V32MQ+2ElR+YUrHeZatG/SHTkuZzrGT2pxniaZQHQCg/HT5M9aZ0SEfPJ6CBaVehx7BOvtYSbMNewrAD7GVHpyqs1JzEgTaUKDYU9YNq+p5rVOWs9Y63ZdejLqnabKDdqu=\",\"a6\":\"w1.3oz8ZC570ISbm5BguazxAgLYmnpArfxiXmJcVBX63aqD5D50FVW5iEzgU05WhvyHO0C2z67HyZUwVXvyHWW3g3H5pdvuafZ2u6zibpK5Ek0sx+Q82D3OfkJJxpYcRytJo44G+GxGDxg8hGRen0B8svDtd32DmtiKzbRHNyDnLXDtxj25gLfNBuV/+8A/oISs6qFQ1vH80LPYL4Ctrgs++rtW6EdhjpffOnsKO24SMUm4ob9p58s5HIwIrfxdIdrDX4Ok9JPHU1TfrNkguj95ILc0teJJ6jnW9BnpmcxYzWXya/f7xRAU09pGiZX6+C4u8KYx/fdBvCInV6O8UM7QytZTQ/hLmU8UJSKeYk/lxXJtR6rpM4Ex6YaF0LVJxRLa+KQKlpzhhHqw93FVIg8ABZEQiebyjTIxoAlGIsXThPQbDUo+uKAMFITcU+uKgZ9J2ZlEam+0i4rkPozNt03Oim/XuDXLDOW6gJn1H4aUFG3uVe5fK5qvjXqqxA8TAw/dN\",\"a7\":\"wxdbb4c5f1b8ee7da1\",\"x0\":3,\"d1\":\"491e959ec4a1182ee9ec8b6a6ca41609\"}",
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
url = "https://wx.maoyan.com/maoyansh/myshow/ajax/tx/orderConfirm/queryProjectAggregateInfo"
params = {
    "token": "MY_S_pquvI7M3IOlE2z9i-ShV4a65kAAAAwS3SxpiR5qvJsaT4kwhLVdB5ZcQF9i58s7hEXXnS10oIxyGmQv_nOwm768-_zAWGKAAAAwAAAAAEB",
    "sellChannel": "7",
    "clientPlatform": "1",
    "cityId": "59",
    "yodaReady": "wx",
    "csecappid": "wxdbb4c5f1b8ee7da1",
    "csecplatform": "3",
    "csecversionname": "wallet-v6.11.13",
    "csecversion": "1.4.0"
}
data = {
    "projectId": "438528",
    "projectShowId": 3058717,
    "projectTicketId": 26761318,
    "benefitId": None
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, params=params, data=data)

print(response.text)
print(response)