# -*- coding: utf-8 -*-
import base64
import hashlib
import time
from typing import Dict, List, Optional

# -------------------------------
# Utils mirroring the bundle
# -------------------------------

def dencrypt_code(arr: List[int]) -> str:
    # 每个数字减2，再转回字符
    return ''.join(chr(x - 2) for x in arr)


def get_qt_time_from_cookie(raw_cookie_val: Optional[str]) -> int:
    """
    修正版：
    - 如果值是纯数字字符串，直接返回 int。
    - 如果是逗号分隔（例如 '56,57,58'），则执行减2解码。
    - 否则返回时间戳形式（取前13位数字部分）。
    """
    if not raw_cookie_val:
        return int(time.time() * 1000)

    if raw_cookie_val.isdigit():
        return int(raw_cookie_val)

    if ',' in raw_cookie_val:
        try:
            s = ''.join(chr(int(x) - 2) for x in raw_cookie_val.split(','))
            return int(s)
        except Exception:
            pass

    # 提取字符串中出现的数字段（防止非纯数字cookie）
    import re
    nums = re.findall(r'\d{10,13}', raw_cookie_val)
    if nums:
        return int(nums[0])

    # 默认返回当前时间戳
    return int(time.time() * 1000)


def token_encrypt_function(qt_time: int, token_str: str) -> str:
    """
    对应 encryptFunction()[qt_time % 2]：
      分支0：Base64(plain) -> SHA1 -> hex
      分支1：SHA1(plain) -> Base64 -> string
    这里与前端一致：plain = tokenStr + qtTime(十进制)
    """
    plain = f"{token_str}{qt_time}"
    if qt_time % 2 == 0:
        b64 = base64.b64encode(plain.encode('utf-8')).decode('ascii')
        sha1_hex = hashlib.sha1(b64.encode('utf-8')).hexdigest()
        return sha1_hex
    else:
        sha1_hex = hashlib.sha1(plain.encode('utf-8')).hexdigest()
        b64 = base64.b64encode(sha1_hex.encode('utf-8')).decode('ascii')
        return b64

def get_random_key_from_qt(qt_time: int) -> str:
    """
    前端的 getRandomKey：
      - 取 qt_time 字符串的后4位之后的部分
      - 对每个字符取 charCode 再拼接成一串数字
      - 做一次 Base64，再取后6位
    """
    tail = str(qt_time)[4:]
    s = ''.join(str(ord(ch)) for ch in tail)
    b64 = base64.b64encode(s.encode('utf-8')).decode('ascii')
    return b64[-6:]

# -------------------------------
# TokenBox re-implementation
# -------------------------------

class TokenBox:
    # 这三个数组来自上传的 bundle（常量，每个元素 -2 还原）
    QT_TIME_ARR = [83, 80, 56, 56, 58]              # -> cookie 键名
    COOKIE_TOKEN_ARR = [83, 80, 54, 58]             # -> 另一个 cookie 键名（兜底）
    TOKEN_STR_ARR = [115,119,112,99,116,97,99,114,107,97,118,113,109,103,112]  # -> DOM id 或 cookie 名

    def __init__(self, cookies: Dict[str, str], dom_hidden_map: Dict[str, str] = None):
        self.cookies = cookies or {}
        self.dom_hidden_map = dom_hidden_map or {}

        self.qt_cookie_key = dencrypt_code(self.QT_TIME_ARR)
        self.cookie_token_key = dencrypt_code(self.COOKIE_TOKEN_ARR)
        self.token_str_key = dencrypt_code(self.TOKEN_STR_ARR)

    def get_cookie(self, name: str) -> Optional[str]:
        return self.cookies.get(name)

    def get_qt_time(self) -> int:
        raw = self.get_cookie(self.qt_cookie_key)
        return get_qt_time_from_cookie(raw)

    def get_token_str(self) -> str:
        # 先从 DOM 隐藏字段拿（如果前端插了一个隐藏节点），没有再从 cookie 取
        if self.token_str_key in self.dom_hidden_map and self.dom_hidden_map[self.token_str_key]:
            return self.dom_hidden_map[self.token_str_key]
        return self.get_cookie(self.cookie_token_key) or ""

    def make_token_pair(self) -> Dict[str, str]:
        """
        返回 { 动态键名: 动态值 }：
           - 键名：getRandomKey(qt_time)
           - 键值：encryptFunction()[qt_time%2]( tokenStr + qt_time )
        """
        qt = self.get_qt_time()
        token_str = self.get_token_str() or ""
        key_name = get_random_key_from_qt(qt)
        key_val = token_encrypt_function(qt, token_str)
        return {key_name: key_val}

# -------------------------------
# __m__ generator
# -------------------------------

def normalize_params(body: Dict[str, str], field_whitelist: List[str]) -> str:
    """
    按白名单字段顺序，拼成 key=value&key2=value2...
    值用 urllib 风格编码（与前端 encodeURIComponent 等价场景）
    """
    from urllib.parse import quote
    parts = []
    for k in field_whitelist:
        v = body.get(k, "")
        parts.append(f"{k}={quote(str(v), safe='')}")
    return '&'.join(parts)

def compute_m(body: Dict[str, str],
              cookies: Dict[str, str],
              whitelist: List[str],
              st: Optional[int] = None,
              enable_aes_layer: bool = False,
              aes_key: bytes = b"",
              aes_iv: bytes = b"") -> str:
    """
    默认实现 Variant A：MD5( normalized_query & st & token_value )
    若你的线上的实现是 Variant B（先 AES 再 MD5），把 enable_aes_layer=True，
    并传入合适的 aes_key / aes_iv（通常由 token/csrf/qt_time 派生）。
    """
    st = "1761817117875"

    # 1) TokenBox 复刻
    tb = TokenBox(cookies=cookies, dom_hidden_map={})
    token_pair = tb.make_token_pair()
    # 动态的 "键名:值"，这里我们只取“值”参与签名
    token_value = list(token_pair.values())[0]

    # 2) 规范化字段串（白名单顺序）
    norm = normalize_params(body, whitelist)

    # 3) 拼接明文
    plain = f"{norm}&st={st}&t={token_value}"

    # 4) 计算 __m__
    if not enable_aes_layer:
        # Variant A：直接 MD5
        return hashlib.md5(plain.encode('utf-8')).hexdigest()
    else:
        # Variant B：AES-CBC-PKCS7(plain) → MD5(ciphertext)
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad

        if not aes_key or not aes_iv:
            raise ValueError("AES key/iv required when enable_aes_layer=True")

        cipher = AES.new(aes_key, AES.MODE_CBC, iv=aes_iv)
        ct = cipher.encrypt(pad(plain.encode('utf-8'), 16))
        return hashlib.md5(ct).hexdigest()

# -------------------------------
# Example
# -------------------------------
if __name__ == "__main__":
    # 你的请求体核心字段（抓包即可得到）
    body = {
        "departureCity": "成都",
        "arrivalCity": "上海",
        "departureDate": "2025-11-01",
        "ex_track": "",
        "sort": ""
    }
    # 白名单顺序（从 Bella / 前端构造里可见）
    whitelist = ["departureCity", "arrivalCity", "departureDate", "ex_track", "sort"]

    # 真实 cookies（从浏览器导出）；至少要包含 qt_time 与 token 对应的两个 cookie

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

    m = compute_m(body, cookies, whitelist)
    print("__m__ =", m)
