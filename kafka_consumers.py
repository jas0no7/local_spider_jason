'''
kafka消费者，把消息消费到本地
'''
from kafka import KafkaConsumer
import json
import time

# =======================
# Kafka 配置
# =======================
KAFKA = {
    "bootstrap_servers": [
        '192.168.0.220:9092',
        '192.168.0.221:9092',
        '192.168.0.222:9092',
        '192.168.0.223:9092'
    ],
    "api_version": (2, 7),
    "client_id": "spider_json_consumer"
}
TOPIC = "spider-policy-nea-v2-v2"  # TODO：改成你的 topic

# 输出文件 = topic.jsonl
OUTPUT_FILE = f"{TOPIC}.json"


def main():
    print(f"正在连接 Kafka 集群：{KAFKA['bootstrap_servers']}")
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA["bootstrap_servers"],
        api_version=KAFKA["api_version"],
        client_id=KAFKA["client_id"],
        auto_offset_reset='earliest',  # 从头消费
        enable_auto_commit=True,       # 自动提交 offset
        value_deserializer=lambda v: v.decode('utf-8', errors='ignore')
    )

    print(f"成功订阅 topic：{TOPIC}")
    print(f"消息将保存到：{OUTPUT_FILE}")
    print("开始消费，按 Ctrl + C 停止...\n")

    try:
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            for message in consumer:
                raw_msg = message.value.strip()

                # 打印到控制台
                print(raw_msg)

                # 写入本地文件（保持原始结构）
                f.write(raw_msg + "\n")

    except KeyboardInterrupt:
        print("\n手动退出消费...")

    finally:
        consumer.close()
        print("Kafka consumer 已关闭")


if __name__ == "__main__":
    main()
