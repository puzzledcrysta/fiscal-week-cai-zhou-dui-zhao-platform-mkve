from collections import defaultdict
from app.errors import DataError
from app.evidence import finding
from .rule import classify_day
from .streak import detect


def calculate(records):
    """对已采信的门店-日记录做单日对照与走弱区间检测。

    返回 (days, intervals, domain_bad)：
    - days：每个门店按日升序的全部对照结论（含不可比日，坏行不丢记录）；
    - intervals：本批数据算出的触发区间（纯计算结果，尚未与持久化预警合并）；
    - domain_bad：财年越界、数值等业务坏行，逐条隔离并说明原因。
    """
    days, domain_bad = [], []
    by_store = defaultdict(list)
    for record in records:
        try:
            conclusion = classify_day(record)
        except DataError as error:
            domain_bad.append(finding(record, error.code, str(error)))
            continue
        by_store[record['key']].append(conclusion)
    intervals = []
    for store in sorted(by_store):
        ordered = sorted(by_store[store], key=lambda item: item['day'])
        days.extend(ordered)
        for interval in detect(store, ordered):
            interval['weak_count'] = len(interval['weak_days'])
            interval['gap_count'] = len(interval['gap_days'])
            interval['cross_week'] = len(interval['fiscal_weeks']) > 1
            intervals.append(interval)
    return days, intervals, domain_bad
