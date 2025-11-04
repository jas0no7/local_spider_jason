# !/usr/bin/env python
# _*_ coding: utf-8 _*_

import sys
from copy import deepcopy

from loguru import logger
from lxml.html import clean
from scrapy.selector import Selector
from scrapy.utils.project import get_project_settings

sys.path.append('..')
sys.path.append('../..')

from .mydefine import MyRedis, MyKafkaProducer

settings = get_project_settings()

policy_kafka_topic = settings.get('POLICY_KAFKA_TOPIC')
news_kafka_topic = settings.get('NEWS_KAFKA_TOPIC')

# 独立的 Item 去重 Key，避免与请求级去重互相干扰
item_dupefilter_key = settings.get('ITEM_DUPEFILTER_KEY', 'duplicate:item:zj_prov')

cleaner = clean.Cleaner()
cleaner.style = True
cleaner.scripts = True


class Pipeline:
    def __init__(self):
        self.myredis = MyRedis()
        self.kafka = MyKafkaProducer()
        self.topics = self.kafka.topics_list()
        # 确保用于 Item 去重的 Cuckoo Filter 存在
        try:
            self.myredis.create(key=item_dupefilter_key, capacity=10000000)
        except Exception:
            pass

    def open_spider(self, spider):
        """
        在启动时 判断是否有对应的kafka topic 没有则新建
        :param spider:
        :return:
        """
        if policy_kafka_topic not in self.topics:
            self.kafka.create_topics(topic_names=[policy_kafka_topic])

        topic = 'spider-temp-scrapy-news-cpc-v1' if spider.name == 'news_cpc' else news_kafka_topic.format(spider.name).replace('_', '-')
        if spider.name.startswith('news') and topic not in self.topics and 'news-zdl' not in topic:
            self.kafka.create_topics(topic_names=[topic])

    def process_item(self, item, spider):
        item = dict(item)

        _id = item.get('_id')
        body_html = item.get('body_html', '')
        attachment = item.get("attachment", [])
        title = item.get('title')
        url = item.get('url')
        publish_time = item.get('publish_time')
        content = item.get('content', '')
        images = item.get('images', [])

        # 去除没有title url id 或者 没有html源码、附件和图片(因为有些网站列表页直接就是附件,没有源码)的数据
        if not title or not url or not _id or not body_html or not publish_time or \
                (not content and not images and not attachment):
            logger.debug(f'缺少必要信息, 不保存数据：{item}')
            return

        current_key = spider.name
        kafka_topic = 'spider-temp-scrapy-news-cpc-v1' if spider.name == 'news_cpc' else \
            item.get('spider_topic') or news_kafka_topic.format(current_key).replace('_', '-')

        # 整个页面去重
        if self.myredis.exists(key=item_dupefilter_key, value=_id):
            logger.info(f'{kafka_topic} 的 {current_key} 已存在 {_id} 跳过')
            return item
        self.myredis.add(key=item_dupefilter_key, value=_id)

        try:
            # 主要是删除html中的style和script标签
            body_html = cleaner.clean_html(body_html)
        except Exception as e:
            logger.info(f'{current_key} 主题文章 {_id} 的body_html为空: {e}')
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

        # 去除字符串开始结尾的空格
        for key, value in item.items():
            if not isinstance(value, str):
                continue

            item[key] = value.strip()

        # 发送到kafka
        if current_key.startswith('policy'):
            key = f'tf_{current_key}'
        else:
            key = None

        try:
            self.kafka.send(topic=kafka_topic, value=deepcopy(item), key=key)
        except Exception as e:
            logger.debug(f'发送失败: {e}')

        return item

    def close_spider(self, spider):
        self.kafka.close()
