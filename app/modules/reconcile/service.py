from .ledger import stores


def enrich(days, intervals, payload):
    """把门店主数据（名称、区域）补到对照结论与预警区间上；清单外门店保留编号、标注未登记。"""
    master = stores(payload)
    for day in days:
        name, region, line = master.get(day['key'], (day['key'], '未登记门店', None))
        day['store_name'] = name
        day['region'] = region
        day['master_line'] = line
    for interval in intervals:
        name, region, line = master.get(interval['key'], (interval['key'], '未登记门店', None))
        interval['store_name'] = name
        interval['region'] = region
    return {'stores': len(master), 'unregistered': sorted({d['key'] for d in days if d['master_line'] is None})}
