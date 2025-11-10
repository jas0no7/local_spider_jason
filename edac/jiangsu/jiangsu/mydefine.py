from datetime import datetime

from zoneinfo import ZoneInfo


def get_now_date() -> str:
    """
    获取当前时间
    :return:
    """
    return datetime.now(tz=ZoneInfo(key='PRC')).strftime('%Y-%m-%d %H:%M:%S')
