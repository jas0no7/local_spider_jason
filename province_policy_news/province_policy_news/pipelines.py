# !/usr/bin/env python
# _*_ coding: utf-8 _*_

import sys
from copy import deepcopy
import hashlib
from loguru import logger
from lxml.html import clean
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings
from scrapy.exceptions import DropItem

sys.path.append('..')
sys.path.append('../..')

from .mydefine import MyRedis, MyKafkaProducer, get_content_fingerprint

settings = get_project_settings()

# 新的 topic 映射字典（来自 settings）
KAFKA_TOPIC_MAP = settings.get("KAFKA_TOPIC", {})

# 去重 key
dupefilter_key = settings.get('SCHEDULER_DUPEFILTER_KEY')

cleaner = clean.Cleaner()
cleaner.style = True
cleaner.scripts = True


class EducationPipeline:
    def __init__(self):
        self.myredis = MyRedis()
        self.kafka = MyKafkaProducer()
        self.topics = self.kafka.topics_list()

    def open_spider(self, spider):
        """
        检查是否存在对应 topic，不存在则创建
        """
        spider_topic = KAFKA_TOPIC_MAP.get(spider.name)
        if spider_topic:
            if spider_topic not in self.topics:
                self.kafka.create_topics(topic_names=[spider_topic])
        else:
            logger.warning(f"未找到 spider.name={spider.name} 对应的 Kafka topic")

    def process_item(self, item, spider):
        logger.info(f"[pipeline-debug] item.title = {item.get('title')}")

        item = dict(item)

        _id = item.get('_id')
        body_html = item.get('body_html', '')
        attachment = item.get("attachment", [])
        title = item.get('title')
        url = item.get('url')
        publish_time = item.get('publish_time')
        content = item.get('content', '')
        images = item.get('images', [])

        # 必要字段校验
        if not title or not url or not _id or not body_html or not publish_time or \
                (not content and not images and not attachment and spider.name in ['edu_policy_hebeijyt']):
            logger.debug(f'缺少必要信息, 不保存数据：{item}')
            return

        spider_key = spider.name

        # 根据 spider.name 获取 topic
        kafka_topic = KAFKA_TOPIC_MAP.get(spider_key)
        if not kafka_topic:
            logger.warning(f"找不到与 spider.name={spider_key} 对应的 topic，跳过 Kafka 推送")
            kafka_topic = None

        ## 全局去重
        if self.myredis.exists(key=dupefilter_key, value=_id):
            logger.info(f'{spider_key} 已存在 {_id} 跳过')
            return item
        self.myredis.add(key=dupefilter_key, value=_id)

        # 内容指纹去重
        fp_key = f"{spider_key}:content_fingerprint"
        fingerprint = get_content_fingerprint(title, content)
        if self.myredis.exists(key=fp_key, value=fingerprint):
            logger.info(f'[内容去重] {spider_key} 内容指纹重复，跳过: {title}')
            raise DropItem('内容重复')
        self.myredis.add(key=fp_key, value=fingerprint)

        # 清理 HTML
        try:
            body_html = cleaner.clean_html(body_html)
        except Exception as e:
            logger.info(f'{spider_key} 的 body_html 清理失败: {e}')
        else:
            item.update({
                "body_html": body_html,
                "content": ' '.join(Selector(text=body_html).xpath('//text()').extract()),
            })

        item.update({
            "spider_topic": kafka_topic,
            "title": ' '.join(Selector(text=title).xpath('//text()').extract()),
            "images": list(set(item.get('images', []))),
        })

        # 删除关键词过滤逻辑（已按你要求移除）

        # 去除字符串首尾空格
        for key, value in item.items():
            if isinstance(value, str):
                item[key] = value.strip()

        # 推送 Kafka
        if kafka_topic:
            try:
                self.kafka.send(topic=kafka_topic, value=deepcopy(item))
                logger.info(f"[Kafka OK] 已发送到 {kafka_topic} -> {_id}")
            except Exception as e:
                logger.error(f"[Kafka ERROR] 发送失败 {kafka_topic} -> {_id}, 原因: {e}")

        return item

    def close_spider(self, spider):
        self.kafka.close()
