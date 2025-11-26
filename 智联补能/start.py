from apscheduler.schedulers.blocking import BlockingScheduler
from loguru import logger
import pytz

from stationFreeNumAndRate import run_rate
from getGunListByStationCodeV2 import run_gun


def run():
    logger.info("开始执行采集任务...")
    run_gun()
    run_rate()
    logger.info("采集任务完成")


if __name__ == '__main__':
    # 使用 pytz（APScheduler 必须用 pytz 时区）
    scheduler = BlockingScheduler(timezone=pytz.timezone("Asia/Shanghai"))

    # 定时任务：每半小时执行一次
    scheduler.add_job(run, "interval", minutes=30, id="job_all")

    # 启动时先执行一次
    run()

    logger.info("定时任务已启动：每 30 分钟运行一次")

    scheduler.start()
