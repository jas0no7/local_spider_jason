# --coding:utf-8--
import sys
import os
from scrapy.http import Request
'''
    用去删除掉Redis的重复指纹
    
'''
# 将项目根目录添加到 Python 路径，以确保能够找到所有模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 假设 mydefine.py 和 myredis.py 都在 province_policy_news 目录下
# 调整导入路径以匹配你的项目结构
from mydefine import _dupefilter_key, request_seen_del

# 模拟一个请求对象，用于生成指纹
request = Request(
    url="http://www.zggzzk.com/zhikudongtai/shownews.php?id=1576",
    method='GET'
)

# 从你的爬虫类中获取 dupefilter_field
dupefilter_field = {"batch": "20231227"}

# 调用删除去重函数
print("正在删除去重指纹...")
try:
    request_seen_del(request, **dupefilter_field)
    print("去重指纹删除完成。")
except Exception as e:
    print(f"删除失败：{e}")