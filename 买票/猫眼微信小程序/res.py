import requests


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a1b) XWEB/8555",
    "X-Channel-ID": "70001",
    "csecuuid": "e26ee4f48e974069280e2701cae8908a",
    "mtgsig": "{\"a1\":\"1.2\",\"a2\":1761873531439,\"a3\":\"1761873461327KUICOUU60e593ce0a815b08d658526270cd17d61432\",\"a4\":\"1e154e6d050338256d4e151e2538030542dccd2967e4ce2c\",\"a5\":\"lD4RbIhaBgF79QH69IBPC37VrSRTzfc6J/SGhOdb0+gLAwZqkubx0lQLwSwmYO8okxOqs4KLk1o6lCLyiorwLv4d/NVdvlyg+4Xh0x5zaRiaxXUEdhwMyCigmHotVGxbJ3OAPcbEYcpxIc6JQ+QUj8JUEG4xyPvsVoZaiEPxCWgt3YbO5YopLWl3+MkJM/5tDnogg6lBBYlaiWWtMqxo+r4nDzvKSCAJEmM/LpVC+KNc5e69II==\",\"a6\":\"w1.3+hVZY34WLS3njHO/fukb6+DGN/9sRHSA1guA+ZfsiyNu1p/pOa8iNSPewmOvpBfPajsHCIKlKKQLR0rLH0PIAnBNspa9IJqwF7Af2wkaq3e2GcLI+mLhUiMmmgrgOAODiufAUkKfxqLUgRBxSOKrkdgTpmSnWtJcfEG1tNLF0O4MxA2Smm75ldSHMW8UGbK+Owi4CeAcN3Hf/AIwzbQgM/fZxImYMIgG2Xe1CqPFth872NejmQcp6I2EDcFvmFyc/IPhmjykp5AoxSuDyUq52rx9c4tnHQq6pEJj1X8ako4n68S/VFi35E+qtdOd1apfm1Hbmp+aHjcq1rI09XAAXPQ8Xu5mYOY3cWNdjhG6bNoeuk0tLEO/INnhdX2zQiOq9GA2RwdfwfwfXYmFudtKt3HVFPu1lS2EzXIE4/oRSJxeImy2xySmtPdkAcm0ZEw7KAOgTLOVisHB3fRxgjuKq6kl8+NRxZlkstLkG8Gqd157GFCDavwmm9c0fbFHyKmq\",\"a7\":\"wxdbb4c5f1b8ee7da1\",\"x0\":3,\"d1\":\"8421b4746e8e875448ae16dfc19f016a\"}",
    "Content-Type": "application/json",
    "xweb_xhr": "1",
    "X-Requested-With": "wxapp",
    "x-wxa-page": "pages/showsubs/ticket-level/v2/index",
    "uuid": "e26ee4f48e974069280e2701cae8908a",
    "x-wxa-referer": "pages/show/detail/v2/index",
    "token": "MY_S_pquvI7M3IOlE2z9i-ShV4a65kAAAAwS3SxpiR5qvJsaT4kwhLVdB5ZcQF9i58s7hEXXnS10oIxyGmQv_nOwm768-_zAWGKAAAAwAAAAAEB",
    "x-wxa-query": "%7B%22id%22%3A%22438528%22%2C%22modelStyle%22%3A%220%22%2C%22isNewPage%22%3A%22true%22%2C%22isHotProject%22%3A%220%22%7D",
    "version": "wallet-v6.11.13",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://servicewechat.com/wxdbb4c5f1b8ee7da1/1711/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
url = "https://wx.maoyan.com/my/odea/show/tickets"
params = {
    "token": "MY_S_pquvI7M3IOlE2z9i-ShV4a65kAAAAwS3SxpiR5qvJsaT4kwhLVdB5ZcQF9i58s7hEXXnS10oIxyGmQv_nOwm768-_zAWGKAAAAwAAAAAEB",
    "sellChannel": "7",
    "showId": "3058717",
    "projectId": "438528",
    "clientPlatform": "1",
    "cityId": "59",
    "yodaReady": "wx",
    "csecappid": "wxdbb4c5f1b8ee7da1",
    "csecplatform": "3",
    "csecversionname": "wallet-v6.11.13",
    "csecversion": "1.4.0"
}
response = requests.get(url, headers=headers, params=params)

print(response.text)
print(response)