import json
from kafka import KafkaProducer
from loguru import logger

'''
把消息 发送到kafka-topic
'''

# ==============================
# Kafka 配置（你给的集群配置）
# ==============================
KAFKA = {
    "bootstrap_servers": [
        '192.168.0.220:9092',
        '192.168.0.221:9092',
        '192.168.0.222:9092',
        '192.168.0.223:9092'
    ],
    "api_version": (2, 7),
    "client_id": "spider_json_producer"
}


# ==============================
# 创建 Kafka Producer
# ==============================
def get_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA["bootstrap_servers"],
        api_version=KAFKA["api_version"],
        client_id=KAFKA["client_id"],
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        retries=3
    )


# ==============================
# JSON 数组 → 逐条写入 Kafka
# ==============================
def send_json_array_to_kafka(json_path: str, topic: str):
    if not topic:
        logger.error("topic 为空！请先设置 topic 名称。")
        return

    producer = get_producer()
    logger.info(f"读取 JSON 文件: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data_list = json.load(f)
    except Exception as e:
        logger.error(f"JSON 解析失败: {e}")
        return

    if not isinstance(data_list, list):
        logger.error("JSON 顶层不是数组格式，无法处理")
        return

    logger.info(f"检测到 {len(data_list)} 条记录，开始写入 Kafka 集群 ...")

    for idx, item in enumerate(data_list):
        try:
            producer.send(topic, item)
            producer.flush()
            logger.info(f"[OK] 第 {idx + 1} 条写入成功 (_id={item.get('_id')})")
        except Exception as e:
            logger.error(f"[ERR] 第 {idx + 1} 条发送失败: {e}")
            continue

    logger.info("全部写入完成！")


if __name__ == "__main__":
    json_path = "national_data.json"
    topic = "spider_national_data"

    send_json_array_to_kafka(json_path, topic)

