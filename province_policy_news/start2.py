# -*- coding: utf-8 -*-
"""
start2.py
作用：自动加载 spiders/ 目录下的所有爬虫，依次运行，并记录报错日志。
"""

import os
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.utils.spider import iter_spider_classes

# ==========================================================
# 初始化 Scrapy 进程
# ==========================================================
settings = get_project_settings()
process = CrawlerProcess(settings)

# ==========================================================
# 日志配置：将错误写入 error.log
# ==========================================================
logging.basicConfig(
    filename='error.log',
    filemode='a',
    level=logging.ERROR,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

console = logging.getLogger('console')
console.setLevel(logging.INFO)

# ==========================================================
# 动态加载 spiders/ 下所有 Spider 类
# ==========================================================

def load_all_spiders():
    """自动读取项目 spiders 文件夹下所有爬虫类"""
    spider_list = []
    spiders_path = os.path.join(os.getcwd(), settings.get('SPIDER_MODULES')[0].replace('.', '/'))

    for file in os.listdir(spiders_path):
        if file.endswith('.py') and not file.startswith('_'):
            module_name = file.replace('.py', '')
            full_module = settings.get('SPIDER_MODULES')[0] + '.' + module_name

            try:
                module = __import__(full_module, fromlist=[''])
                for spider_cls in iter_spider_classes(module):
                    spider_list.append(spider_cls)
            except Exception as e:
                logging.error(f'无法加载模块 {full_module}: {e}')

    return spider_list


# ==========================================================
# 主执行逻辑
# ==========================================================

def run_all_spiders():
    spiders = load_all_spiders()
    console.info(f"共加载到 {len(spiders)} 个爬虫")

    for spider in spiders:
        spider_name = spider.name
        console.info(f"开始运行爬虫：{spider_name}")

        try:
            process.crawl(spider)
        except Exception as e:
            logging.error(f"爬虫 {spider_name} 运行失败: {e}")
            console.error(f"爬虫 {spider_name} 运行失败，请检查 error.log")
            continue

    process.start()  # 阻塞直到全部结束
    console.info("全部爬虫执行完毕")


# ==========================================================
# 入口
# ==========================================================
if __name__ == '__main__':
    run_all_spiders()
