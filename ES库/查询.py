# -*- coding: utf-8 -*-
from elasticsearch import Elasticsearch

# 配置
ES_HOSTS = ["http://192.168.0.220:9200", "http://192.168.0.221:9200", "http://192.168.0.222:9200", "http://192.168.0.223:9200"]
ES_AUTH = ("elastic", "edac200700")
INDEX_NAME = "news_v2"

es = Elasticsearch(ES_HOSTS, http_auth=ES_AUTH, timeout=30)

# ==========================================
# 这里直接使用您提供的查询逻辑
# ==========================================
dsl = {
    "query": {
        "match": {
            "spider_from": "中国日报网"
        }
    },
    "size": 10,
    "from": 0,
    # 建议加上排序，不然结果顺序是随机的（按相关性）
    "sort": [{"publish_time": "desc"}]
}

# 执行
try:
    res = es.search(index=INDEX_NAME, body=dsl)
    hits = res["hits"]["hits"]

    print(f"查询到 {res['hits']['total']['value']} 条结果：\n")

    for hit in hits:
        src = hit["_source"]
        print(f"来源: {src.get('spider_from')}")
        print(f"标题: {src.get('title')}")
        print("-" * 50)

except Exception as e:
    print("查询失败:", e)