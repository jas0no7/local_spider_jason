from kafka import KafkaConsumer
import json

TOPIC = "article_ocr_task"
OUTPUT_FILE = f"{TOPIC}.jsonl"   # 一行一个 JSON，更标准

def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=[
            '192.168.0.220:9092',
            '192.168.0.221:9092',
            '192.168.0.222:9092',
            '192.168.0.223:9092'
        ],
        api_version=(2, 7),
        client_id="spider_json_consumer",
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda v: v.decode('utf-8')
    )

    print(f"Saving messages to {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for msg in consumer:
            raw = msg.value

            try:
                # 反序列化 JSON 字符串
                data = json.loads(raw)

                # 格式化输出（中文正常）
                pretty = json.dumps(data, ensure_ascii=False, indent=4)

                print(pretty)  # 控制台中文也正常显示

                # 保存格式化 JSON
                f.write(pretty + "\n\n")

            except Exception as e:
                print("JSON 解析失败，原始数据：", raw)
                f.write(raw + "\n")


if __name__ == "__main__":
    main()
