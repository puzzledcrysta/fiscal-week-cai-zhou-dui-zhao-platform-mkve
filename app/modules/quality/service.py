from app.evidence import distribution
from .versions import split_versions


def inspect(records, rejected):
    # 未采信的高修订按门店登记（同一门店任一天的坏高版本都会阻塞该门店旧版本接替）。
    unverified = {}
    for row in rejected:
        if 'revision' in row:
            unverified[row['key']] = max(row['revision'], unverified.get(row['key'], 0))
    ready, duplicates, conflicts = split_versions(records, unverified)
    quarantine = sorted([*rejected, *conflicts], key=lambda row: row['line'])
    return {'ready': ready, 'suppressed': sorted(duplicates, key=lambda row: row['line']),
            'rejected': quarantine, 'reasons': distribution(quarantine)}
