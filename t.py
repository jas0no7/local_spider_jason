# -*- coding: utf-8 -*-
# 自动根据 spider_name_from_map 生成 docker-compose 服务片段
# 输出全部包含中文注释 + 统一 volumes 的 YAML

spider_name_from_map = {

    # ======================
    # 新闻类（更新完整）
    # ======================
    'news_fgw_fujian': '新闻-发展和改革委员会-福建',
    'news_fgw_gansu': '新闻-发展和改革委员会-甘肃',
    'news_fgw_henan': '新闻-发展和改革委员会-河南',
    'news_fgw_jiangsu': '新闻-发展和改革委员会-江苏',
    'news_fgw_zhejiang': '新闻-发展和改革委员会-浙江',

    'news_gsbnea': '新闻-国家能源局-甘肃',
    'news_gxt_jiangxi': '新闻-工业和信息化厅-江西',

    'news_nea_fujian': '新闻-国家能源局-福建',
    'news_nea_jiangsu': '新闻-国家能源局-江苏',

    'news_scbnea': '新闻-国家能源局-四川',

    'news_sthjt_fujian': '新闻-生态环境厅-福建',
    'news_sthjt_shaanxi': '新闻-生态环境厅-陕西',
    'news_sthjt_sichuan': '新闻-生态环境厅-四川',

    'new_fgw_sichuan': '新闻-发展和改革委员会-四川',

    # ======================
    # 政策类（发展改革委 fgw）
    # ======================
    'policy_fgw_chongqing': '政策-发展和改革委员会-重庆',
    'policy_fgw_henan': '政策-发展和改革委员会-河南',
    'policy_fgw_jiangsu': '政策-发展和改革委员会-江苏',
    'policy_fgw_shaanxi': '政策-发展和改革委员会-陕西',
    'policy_fgw_zhejiang': '政策-发展和改革委员会-浙江',
    'policy_fgw_hunan': '政策-发展和改革委员会-湖南',
    'policy_fgw_sichuan': '政策-发展和改革委员会-四川',

    # ======================
    # 政策类（gxt 工业和信息化厅）
    # ======================
    'policy_gsbnea': '政策-国家能源局-甘肃',
    'policy_gxt_fujian': '政策-工业和信息化厅-福建',
    'policy_gxt_hunan': '政策-工业和信息化厅-湖南',
    'policy_gxt_henan': '政策-工业和信息化厅-河南',
    'policy_gxt_jiangsu': '政策-工业和信息化厅-江苏',
    'policy_gxt_jiangxi': '政策-工业和信息化厅-江西',
    'policy_gxt_shaanxi': '政策-工业和信息化厅-陕西',

    # ======================
    # 政策类（能源局）
    # ======================
    'policy_hnnyfz': '政策-能源发展厅-河南',
    'policy_hunb_nea': '政策-国家能源局-湖北',

    'policy_nea_fujian': '政策-国家能源局-福建',
    'policy_nea_shaanxi': '政策-国家能源局-陕西',
    'policy_nea_jiangsu': '政策-国家能源局-江苏',
    'policy_nea_zhejiang': '政策-国家能源局-浙江',

    'policy_scbnea': '政策-国家能源局-四川',

    # ======================
    # 政策类（其他厅局）
    # ======================
    'policy_jjxxw_chongqing': '政策-经济和信息化委员会-重庆',

    'policy_jxt_sichuan': '政策-交通运输厅-四川',

    'policy_sndrc_shaanxi': '政策-发展和改革委员会-陕西（能源处）',

    # ======================
    # 生态环境厅 sthjt
    # ======================
    'policy_sthjt_chongqing': '政策-生态环境厅-重庆',
    'policy_sthjt_fujian': '政策-生态环境厅-福建',
    'policy_sthjt_hunan': '政策-生态环境厅-湖南',
    'policy_sthjt_shaanxi': '政策-生态环境厅-陕西',
    'policy_sthjt_sichuan': '政策-生态环境厅-四川',

}


def generate_compose(map_dict):
    template = """
  # 各省份新闻政策 {cn_name}
  spider_province_policy_news_{spider}:
    <<: *common_spider_config
    container_name: spider_province_policy_news_{spider}
    volumes:
      - ./province_policy_news:/app
    command: python start.py -n {spider}
"""
    result = ""
    for spider, cn_name in map_dict.items():
        block = template.format(spider=spider, cn_name=cn_name)
        result += block

    return result


if __name__ == "__main__":
    out = generate_compose(spider_name_from_map)
    print("=== 以下是自动生成的 docker-compose 片段 ===\n")
    print(out)
    # 如果你想存文件，也可以打开下面这行
    open("compose_generated.yml", "w", encoding="utf-8").write(out)
