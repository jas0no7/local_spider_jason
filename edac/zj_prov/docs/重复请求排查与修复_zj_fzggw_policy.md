**背景**
- 项目为 Scrapy 爬虫，启用自定义调度与去重（Redis Cuckoo Filter）。
- 运行 `zj_fzggw_policy` 时，出现同一详情页短时间内被重复抓取并产出两次 Item 的现象。

**现象**
- 日志出现同一 URL 的重复抓取，如：`https://fzggw.zj.gov.cn/art/2025/9/28/art_1229123489_5650096.html`。
- Pipeline 日志显示“已存在 … 跳过”，同时 Scrapy 仍打印 “Scraped from <200 …>”。这表明同一详情页请求在同一轮次中被并发处理了至少两次。

**定位过程**
- 关键文件：
  - `zj_prov/mydefine.py` 自定义去重与调度（`RFPDupeFilter`, `Scheduler`）。
  - `zj_prov/pipelines.py` Item 级去重与发送。
  - `zj_prov/spiders/zj_fzggw_policy.py` 详情请求生成逻辑。
- 代码点：
  - 请求级去重使用 RedisBloom Cuckoo Filter，但实现为 `exists()` + `add()` 两步检查；
  - Item 级去重与请求级去重共用同一个 Redis Key：`duplicate:zj_prov`；
  - 详情请求在 `zj_fzggw_policy` 中未显式设置 `dont_filter=False`（虽默认为 False，但与其它 Spider 不一致）。

**根因分析**
- 根因 1：请求级去重存在竞态
  - 原实现：`exists(key, fp)` 为 False 时再 `add(key, fp)` 写入；
  - 在并发环境（或多进程/多爬虫共享同一 Key）下，两次相同请求可能都在 `add` 之前看到 `exists=False`，从而都入队，造成同一详情页被重复请求。

- 根因 2：请求与 Item 共用同一个 Cuckoo Filter Key
  - 二者的 fingerprint 值不同，但共用 Key 会相互污染，显著提升误判率（CF 的假阳性概率随填充升高）。
  - 结果表现为：调度层面可能放过重复请求；Pipeline 又在 Item 层面判定“已存在”。

**修复方案**
- 修复 1：请求级去重改为原子判重（仅用 CF.ADDNX）
  - 修改 `zj_prov/mydefine.py:RFPDupeFilter.request_seen`：使用 `addnx` 直接判断并写入，避免 `exists + add` 的时间窗口竞态；
  - 保持指纹计算逻辑不变（method + canonical_url + body + 批次标记）。

- 修复 2：拆分请求与 Item 的 Redis Key
  - `settings.py`
    - `SCHEDULER_DUPEFILTER_KEY = "duplicate:req:zj_prov"`
    - 新增 `ITEM_DUPEFILTER_KEY = "duplicate:item:zj_prov"`
  - `pipelines.py`
    - 读取 `ITEM_DUPEFILTER_KEY` 做 Item 级去重；
    - 在 `__init__` 中确保创建对应的 Cuckoo Filter。

- 修复 3：与其它 Spider 保持一致
  - `zj_fzggw_policy.py` 的详情请求显式加上 `dont_filter=False`，避免差异行为。

**涉及改动**
- 文件与片段：
  - `zj_prov/mydefine.py`
    - 原 `request_seen`（exists + add）→ 原子 `addnx` 判断；
  - `zj_prov/settings.py`
    - 拆分 `SCHEDULER_DUPEFILTER_KEY` 与新增 `ITEM_DUPEFILTER_KEY`；
  - `zj_prov/pipelines.py`
    - 使用 `ITEM_DUPEFILTER_KEY`，并创建对应 CF；
  - `zj_prov/spiders/zj_fzggw_policy.py`
    - 详情请求补充 `dont_filter=False`。

**验证建议**
- 单独运行 `zj_fzggw_policy` 某一个栏目，观察：
  - 同一详情 URL 不应在同一次运行中重复出现两条 `Scraped from <200 …>`；
  - Pipeline 仅在真正重复运行（或手动再次触发）时打印“已存在 … 跳过”。
- 如需彻底复位，可手动清理旧 Key（注意影响范围）：
  - 请求：`duplicate:req:zj_prov`
  - Item：`duplicate:item:zj_prov`

**注意事项**
- 目前 `_id` 仍按 `md5(method + url + body)` 生成（与请求指纹不同）。这不会影响正确性，且保持了历史兼容。
- 若同时运行多爬虫共享 CF，建议按项目或站点拆分 Key，控制填充和误判率。

**结论**
- 重复请求的主因是“非原子判重 + 共用 Key”。本次修改通过原子去重与 Key 拆分，从根因上消除重复调度与互相污染的问题。

