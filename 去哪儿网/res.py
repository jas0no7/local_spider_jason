import requests


headers = {
    "accept": "text/javascript, text/html, application/xml, text/xml, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded",
    "csht;": "",
    "f1ff6e": "561568cc16f69a6fa887c6dc60b05a51ac6fd690",
    "origin": "https://flight.qunar.com",
    "pragma": "no-cache",
    "pre": "dbe1bc99-1d9548-94489c82-50be8671-13b27bf28bb5",
    "priority": "u=1, i",
    "referer": "https://flight.qunar.com/site/oneway_list.htm?searchDepartureAirport=%E6%88%90%E9%83%BD&searchArrivalAirport=%E4%B8%8A%E6%B5%B7&searchDepartureTime=2025-11-01&searchArrivalTime=2025-11-04&nextNDays=0&startSearch=true&fromCode=CTU&toCode=SHA&from=flight_dom_search&lowestPrice=null",
    "sec-ch-ua": "\"Google Chrome\";v=\"141\", \"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"141\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "w": "2",
    "x-requested-with": "XMLHttpRequest"
}
cookies = {
    "QN1": "0000ec80306875cdc018d2e9",
    "QN300": "s%3Dbing",
    "QN99": "848",
    "qunar-assist": "{%22version%22:%2220211215173359.925%22%2C%22show%22:false%2C%22audio%22:false%2C%22speed%22:%22middle%22%2C%22zomm%22:1%2C%22cursor%22:false%2C%22pointer%22:false%2C%22bigtext%22:false%2C%22overead%22:false%2C%22readscreen%22:false%2C%22theme%22:%22default%22}",
    "QN205": "s%3Dbing",
    "QN277": "s%3Dbing",
    "csrfToken": "VmEht5yxBSa9ghI26Z9MeI6n1Ld4jgQ3",
    "_i": "VInJOv90zSwquxnxMfRzBRbh_8xq",
    "_vi": "ICmSTOIAwnCSWaoW-x0BnPKEtkuNDlCK6B08XbqaGct8lLmgw2lKwwFTO7ErnBGPPubn7HHslKRVRDJxP38TYcuqC81kRoHKQjUx0PPq_yZAs9G_A9x_Bi28FjfhcqpenEs1gDiTic6CeKfERvkZdNSyRsmqO4W_AorENfI2wdRt",
    "QN269": "26CDA310B57411F0BA3E829BBD9F81E5",
    "QN601": "58f604e01540cc5aafb4f408b9674ac1",
    "QN48": "00010c802f1075cdc0202e03",
    "quinn": "88f0434199c1bb2027933430b53d191ac4921104d4b06b4f4d71996e8c5d79d372e5affecb833452a6ea5e6f73c414b1",
    "fid": "3cf9a9cb-f2fc-47b5-925e-1aeff7752ecf",
    "RT": "s=1761817099811&r=https%3A%2F%2Fflight.qunar.com%2F",
    "QN621": "fr%3Dflight_dom_search",
    "Alina": "97c4749c-2db660-07442153-46b71c43-21bd6903320d",
    "F235": "1761817101312",
    "ariaDefaultTheme": "undefined",
    "QN271": "cc6b5e1b-e33e-4751-952c-717836f42e6b",
    "QN668": "51%2C57%2C56%2C51%2C58%2C51%2C57%2C51%2C50%2C59%2C56%2C52%2C59",
    "11344": "1722403391463##iK3was3mVuPwawPwast8WRGIXS0ha%3DDnWPasESPOXsWIERPmVR3Na%3DGTXsXmiK3siK3saKgOaKtnWsDnWsgwaUPwaUvt",
    "11536": "1722403391463##iK3wWsj%2BawPwawPwasDNXsEhVPWhaKgAWsXOXPPAEPDOVRP8WDa%3DESvAaS3NiK3siK3saKgOaKtnWsD8aKvNWwPwaUvt",
    "QN267": "0132094091811e96f41",
    "cs_june": "645007511c10e36bd9c20036111481609f63361b85a01173ce5518ee353bf0a5634e260e3ae020a57f77c63f40a0d64f4d84773d943429863a399e90434d1e6eb17c80df7eee7c02a9c1a6a5b97c1179bb9ab32cfa97d5892313433bf40a95ab5a737ae180251ef5be23400b098dd8ca"
}
url = "https://flight.qunar.com/touch/api/domestic/wbdflightlist"
data = {
    "departureCity": "成都",
    "arrivalCity": "上海",
    "departureDate": "2025-11-01",
    "ex_track": "",
    "__m__": "f626d69ad10a4648a246f2dba68133b7",

    "st": "1761817117875",
    "sort": "",
    "Bella": "1722403391463##28549c0c874088e0e7921f637a1ac58d41772c72##iKohiK3wgMkMf-i0gUPwaUPsXuPwaMfLy9opohNno9NHgUNScO=0a2fsy-X0aS30a2a0aSi8y9WScOnxiK3wiKWTiK3wVR2wWhPwawPwas0DVPiTES3OWDWGWDaAaRX0aSa0aSanWsjnVRD+aKD+VKX8iK3wiKiRiK3wgOHQgMn0duPwaUPsXuPwaSj+WK0MaODwfK3OWKESWRWHWRPnWRP=fKjnaSP=fKiSiK3wiKiRiK3woI0=cIP0aS30a=D0aS30EKg0X2X0VKGEo9NHgUNScO=0aS30a2a0aSilf-0+c+i2gwPwaUPsXuPwaUPwXAGAcMGwqMWxcuPwaUPwXwPwaME0gOWwy-T=y9FbiK3wiKWTiK3wiPPAiKHGiPihiPPAiK2siPGTiPPAiKt=iPiIJGGAcMGwqMWxcu20EKX0X2X0VPa0EKX0XSt0X2D0EKP0VRP0XKt0EKg0VKv0VRa0EKj0VPa0VRv0EKP0XKX0XKg0aS30a2a0aSipc+W=iK3wiKWTiK3wfMnQfOH=q5GAcMGwqMWxcuPwaUPwXwPwa5WSgM08oGWwjwPwaUPsXuPAXUPwaMfLy9opoIF8fIG=juNno9m0aS30a2a0aSiScOAecOmbg-kbj-irdUNSiK3wiKkDiKiRiK3wgInHoIfxgM=0aS30a=D0aSi-y9msaUPwaUPwXwPwaMnxjwPwaUPsXuPwaSX0aS30a2a0aSiScIGsg=NHc9PniK3wiKWTiK3wgkFpf9G2f-i/oINHo0Fxc9kbokFeiK3wiKiRiK3woI0ef-W=j9A8iK3wiKWTaKgOaKtnWsDnWs2=ahPwXwPwa5ksf-iTfOkbohPwaUPsXuPwa2AxdM0LcID0a2jAqSv0aSvpkO0bfIF+gwPwaDNPiK38aKvbahPsXUPwaGoQcSj=iKWhiK38dRj=JuPwaDG8gIn0kOkUuO0=iKiIWKa+qSaOiK38JDe3kDAaiKiRiK38cI0lfuPwaDo0jOexJuPwaDWpgMFefuPwESD=aum8qSvbahPwaGWHfMGwyuPwESPsWwmsWUPwaUP+Ehvt##vaAtiRp-Xe73BEseoi5c6##departureCity,arrivalCity,departureDate,ex_track,__m__,st,sort##2oT/oX2lkq7FvEiWuPe1Q4yhGIKnUUq/4PYb710/pEBD6RS4Qm39NMeNLRPl7TEbfJViQuuNP1Z1nBtuBjPhrJkEqEGZGC3nQGRBg71UhOoo5Ymzb/KAOTVUwfqLhcTjfwBQ8G0GUxK5oKuvNmT+kRYyOlAEqlIzzVd3L5MnSy5EAhNdkOv9P/BjaApPtso+2oT/oX2lkqAbmiCYL9gmTACYkqx9/PJlD9kEWsiDKwHiC3YP8KO3EFWPhvw6UNf9WiVj0vVMI7WDMPenBOQinXQtW8FcZX7gTKMl1HQj1LC=",
    "_v": "4"
}
response = requests.post(url, headers=headers, cookies=cookies, data=data)

print(response.text)
print(response)