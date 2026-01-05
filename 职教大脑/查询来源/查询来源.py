def es_search_result_processing2(es_result: list, intercept=True):
    result = []
    for item in es_result:
        tags = {}

        policy_directory_category = item['_source'].get('policy_directory_category', [])

        es_index = config.ES_CONF.get("ve_index")
        influence = item['_source'].get('area_of_influence', [])
        if influence:
            temp_list = app_config.PROVINCE_LIST + app_config.CITY_LIST
            influence = sorted(influence, key=temp_list.index)
            tags['influence'] = influence

        policy_type = item['_source'].get('policy_type', [])
        if policy_type:
            tags['policy'] = policy_type

        keywords = item['_source'].get('keywords', [])
        if keywords:
            tags['keywords'] = keywords

        title = item.get('highlight', {}).get('title', [])
        if title:
            title = title[0]
        else:
            title = item['_source']['title']

        content = item.get('highlight', {}).get('content', [])
        if content:
            content = content[0]
        else:
            content = item['_source']['content']

        if intercept:
            for _ in content.split('。'):
                if "<font style='color:red'>" in _:
                    content = f"{_}。"
                    break

        result.append(
            {
                "index": es_index,
                "es_id": item['_id'],
                "title": title,
                "publish_time": item['_source']['publish_time'].split(' ')[0],
                "spider_from": item['_source']['spider_from'],
                "url": item['_source']['url'],
                "content": content,
                "tags": tags,
                "ai_summary": item['_source']['ai_summary'],
                "policy_issuer": item['_source'].get('policy_issuer', []),
                "relevant_policy": item['_source'].get('relevant_policy', [])
            }
        )

    return result
