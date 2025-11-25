# !/usr/bin/env python
# _*_ coding: utf-8 _*_

import os
from argparse import ArgumentParser
from copy import deepcopy
from datetime import timedelta, datetime
from pathlib import Path
from random import randint
from subprocess import Popen
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BlockingScheduler
from loguru import logger

from tfpolicy.settings import cron as tf_cron

obj_path = 'tfpolicy/spiders'
spider_names = [path[:-3] for path in os.listdir(obj_path) if not path.startswith('__')]


def get_now_date():
    """
    获取当前时区时间
    :return:
    """
    return datetime.now(tz=ZoneInfo(key='PRC'))


def scheduler(scheduler_info: list, replace_existing: bool = True):
    """
    Apscheduler 定时任务
    :param scheduler_info: 执行的任务信息
    :param replace_existing: 存在任务是否替换 True:替换
    :return:
    """
    blocking_scheduler = BlockingScheduler(timezone='Asia/Shanghai')

    # 记录任务是否已经过期
    run_list = []
    for info in scheduler_info:
        cron = info.get('cron')
        if 'trigger' not in cron:
            cron.update({
                "trigger": "cron"
            })

        trigger = cron.get('trigger')
        if info.get('is_now', False) and trigger in ["cron"]:
            cron.update({
                'next_run_time': get_now_date() + timedelta(seconds=5)
            })

        job_id = info.get('job_id')
        if not job_id:
            path = Path(info.get('file_path', '未知/未知'))
            job_id = f'spider_{path.parent.stem}_{path.stem}'

        _message = info.get('message')
        run_date = f'{cron.get("hour", "*")}:{cron.get("minute", "*")}:{cron.get("second", "*")}'
        end_date = cron.get('end_date')
        if end_date:
            _end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S") if isinstance(end_date, str) else end_date
            if _end_date < get_now_date():
                logger.info(f'定时任务 {job_id} 结束时间为 {_end_date.strftime("%Y-%m-%d %H:%M:%S")}, 不满足条件！')
                run_list.append(False)
                continue

        logger.info(f'等待定时任务中, {job_id} {_message} 运行时间为: {run_date}, 结束时间: {end_date}')
        run_list.append(True)
        blocking_scheduler.add_job(info.get('func'), id=job_id, args=info.get('args'), kwargs=info.get('kwargs'), replace_existing=replace_existing, **cron)

    # 如果全部过期就不用启用定时任务
    if any(run_list):
        blocking_scheduler.start()


def crawl_spider(current_name):
    """
    运行
    # :param message:
    :param current_name: 名称
    :return:
    """
    p = Popen(f'scrapy crawl {current_name}', shell=True)
    p.wait()


def run(current_name):
    if not current_name or current_name not in spider_names:
        raise Exception(f'输入的名称{current_name}不存在, 请检查名称是否正确!')

    my_cron = {
        **tf_cron,
        "hour": f"{randint(9, 18)}",
        "minute": f"{randint(0, 59)}",
        "second": f"{randint(0, 59)}",
    }

    scheduler([
        {
            'func': crawl_spider,
            'cron': my_cron,
            'job_id': f"spider_{current_name}",
            'file_path': __file__,
            'args': deepcopy([current_name]),
            'message': f'天府五库{current_name}'
        }
    ])


if __name__ == '__main__':
    parser = ArgumentParser(description='命令行参数示例')
    parser.add_argument('-n', '--name', type=str, default='policy_cdsrmzf')
    args = parser.parse_args()
    # run(args.name)
    crawl_spider("policy_scsfzggw")