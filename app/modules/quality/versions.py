from collections import defaultdict
from app.evidence import finding


def _day_key(record):
    """版本归并的业务键 = 门店 + 营业日期（一个门店一天只采信一条最新版本）。"""
    return record['key'], record['fields']['营业日期']


def split_versions(records, unverified):
    groups = defaultdict(list)
    for record in records:
        groups[_day_key(record)].append(record)
    ready, duplicates, conflicts = [], [], []
    for (key, day), group in sorted(groups.items()):
        latest = max(row['revision'] for row in group)
        pending = unverified.get(key, 0)
        if pending >= latest:
            conflicts.extend(finding(row, 'REV_BLOCKED', f'修订 {pending} 仍有来源未采信') for row in group)
            continue
        candidates = sorted((row for row in group if row['revision'] == latest), key=lambda row: row['line'])
        older = [row for row in group if row['revision'] != latest]
        duplicates.extend(finding(row, 'SUPERSEDED', f'{day} 修订 {latest} 取代旧版本') for row in older)
        signatures = {(row['status'], tuple(row['fields'].items())) for row in candidates}
        if len(signatures) > 1:
            conflicts.extend(finding(row, 'REV_CONFLICT', f'{day} 最高修订 {latest} 的来源互相冲突') for row in candidates)
        else:
            chosen = candidates[0]
            chosen['day'] = day
            ready.append(chosen)
            duplicates.extend(finding(row, 'EXACT_DUP', f'{day} 同为修订 {latest}，保留第 {chosen["line"]} 行')
                              for row in candidates[1:])
    return ready, duplicates, conflicts
