import requests


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Google Chrome\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
}
cookies = {
    "yyb_muid": "0FBD6ACC2E3A647C1F887CCC2F3B65D4",
    "eas_sid": "r1h7m5r1c2Y5G0o3V0N4f2u4B7",
    "pgv_pvid": "683453400",
    "fqm_pvqid": "957df8d8-4627-47c6-b523-c4de910acc29",
    "_qimei_uuid42": "1980f0921381001beb3338d74dc521df70c159573c",
    "_qimei_fingerprint": "0a49b192fa6a9395fd6434d3aab053ca",
    "_qimei_q36": "",
    "_qimei_h38": "a4fafff2eb3338d74dc521df0200000691980f",
    "RK": "im/Y6DkaGd",
    "ptcz": "72e55d752b7c25101426cae205b0aa9c2c7e5315f319099bf759d4ae454fe1ff",
    "rewardsn": "",
    "wxtokenkey": "777"
}
url = "https://mp.weixin.qq.com/s/kVQqjuuZ5SM6xFfbe0CBDw"
response = requests.get(url, headers=headers, cookies=cookies)

print(response.text)
print(response)