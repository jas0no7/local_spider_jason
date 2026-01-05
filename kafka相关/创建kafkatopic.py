def create_kafkatopic(new_topic_name):
    from kafka import KafkaProducer
    from elasticsearch import Elasticsearch
    import json
    from kafka.admin import KafkaAdminClient, NewTopic
    # 0. 创建主题（用KafkaAdminClient）
    topic_name = new_topic_name
    admin_client = KafkaAdminClient(
        bootstrap_servers=['192.168.0.220:9092', '192.168.0.221:9092', '192.168.0.222:9092', '192.168.0.223:9092'],
    )

    # 定义主题配置（32个分区，副本因子根据你的broker数量调整）
    topic = NewTopic(
        name=topic_name,
        num_partitions=32,  # 32个分区
        replication_factor=3,  # 副本数，通常为2或3    1
        topic_configs={
            'retention.ms': str(90 * 24 * 60 * 60 * 1000),  # 保留90天
            'retention.bytes': '-1',  # 无大小限制
            'cleanup.policy': 'delete'
        }
    )

    # 创建主题
    admin_client.create_topics([topic])



create_kafkatopic("spider-policy-wx-test")