# nonce / X-Ca-Signature 生成逻辑（来自小程序源码逆向）

本文档基于本目录内小程序打包后的 `appservice.app.js` 代码还原出接口请求中 `nonce` 参数与 `X-Ca-Signature` 请求头的生成方式，便于你在本地复现同样的签名值做联调/排查。

## 1. 代码位置

- 发起请求时组装 `timestamp`、`nonce`、`X-Ca-Signature`：`appservice.app.js:1429`
- `getSignature` 的实现：`appservice.app.js:1423`（webpack module id `57`）

## 2. nonce 的生成逻辑

在统一请求封装里，每次请求会生成一个 `nonce`，并作为请求体参数发送。

- `nonce = uuid.v4()`（UUID v4，带连字符，例如：`4ab9365d-02b4-4a8f-a7c8-a581c8ebefea`）

## 3. timestamp 的生成与使用

请求时生成毫秒级时间戳：

- `timestamp = (new Date).getTime()`（13 位毫秒时间戳）

该值会同时出现在：

- 请求体参数 `timestamp`
- 请求头 `X-Ca-Timestamp`

并且参与 `X-Ca-Signature` 的计算（见下文）。

## 4. 请求参数的“规范化”（canonicalization）

签名计算前，请求体参数会按以下步骤处理：

1. **补齐签名相关字段**
   - 在原始 `data` 基础上追加 `timestamp` 与 `nonce`。
2. **按 key 排序**
   - 使用 `Object.keys(obj).sort()` 对 key 做字典序排序，并按排序后的 key 重新构造对象（保证后续遍历顺序稳定）。
3. **删除空值字段**
   - 对每个字段：若值为 `null` 或 `undefined`，则 `delete` 该字段。
4. **拼接成参数串**
   - 按对象遍历顺序拼成：`k1=v1&k2=v2&...`
   - 注意：这里**不做 URL 编码**，值直接用 JS 的字符串化结果（数字用 `toString()`，字符串原样拼接）。

在源码里，这段拼接逻辑等价于：

```js
var u = function (e) {
  var t = "";
  for (var n in e) t += "".concat(n, "=").concat(e[n], "&");
  return t.slice(0, -1);
};
```

## 5. X-Ca-Signature 的生成算法

源码中的核心实现（webpack module `57`）：

```js
t.getSignature = function (e) {
  var t = md5(u(e));
  return (t = md5("".concat(t).concat(e.timestamp))).toUpperCase();
};
```

因此最终算法为：

1. `canonical = "k1=v1&k2=v2&...&kn=vn"`（已排序、已删空、包含 `timestamp` 与 `nonce`）
2. `md5_1 = MD5(canonical)`（得到 32 位 hex，小写）
3. `md5_2 = MD5(md5_1 + str(timestamp))`（再做一次 MD5）
4. `X-Ca-Signature = md5_2.upper()`（32 位 hex，大写）

用公式表示：

```
X-Ca-Signature = UPPER( MD5( MD5(canonical_query_string) + timestamp ) )
```

## 6. Python 复现

脚本见：`gen_ca_signature.py`

它做了与小程序一致的：

- 生成 UUIDv4 `nonce`
- 生成毫秒 `timestamp`
- 对参数按 key 排序并拼接 `k=v&...`
- 计算 `X-Ca-Signature = MD5(MD5(canonical) + timestamp).upper()`

示例（用你提供的参数校验；Windows PowerShell 下推荐用 `--data key=value` 方式避免 JSON 引号在传参时丢失）：

```bash
python gen_ca_signature.py ^
  --timestamp 1766042398608 ^
  --nonce 4ab9365d-02b4-4a8f-a7c8-a581c8ebefea ^
  --data allStation=1 ^
  --data equipmentType=0 ^
  --data lat=30.570199966430664 ^
  --data lng=104.06475830078125 ^
  --data orderType=1 ^
  --data page=2 ^
  --data pagecount=10 ^
  --data radius=10000 ^
  --data stubGroupTypes=0,1
```

输出中的 `x_ca_signature` 应与抓包里的 `X-Ca-Signature` 一致。
