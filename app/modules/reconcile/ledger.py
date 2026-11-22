from app.errors import DataError
from app.settings import KEY
from app.modules.intake.reader import decode, records

REQUIRED_HEADER = [KEY, '门店名称', '区域']


def stores(payload):
    """门店主数据：门店编号 -> (名称, 区域, 来源行)。重复编号整单拒绝。"""
    text, _ = decode(payload)
    rows = iter(records(text))
    _, header = next(rows, (0, []))
    if header != REQUIRED_HEADER:
        raise DataError('HEADER', f'门店清单表头须为 {",".join(REQUIRED_HEADER)}')
    by_key = {}
    for line, row in rows:
        if not row or not any(value.strip() for value in row):
            continue
        if len(row) != 3 or not row[0].strip():
            raise DataError('WIDTH', f'门店清单第 {line} 行字段不完整')
        key = row[0].strip()
        if key in by_key:
            raise DataError('BOOK_CONFLICT', f'门店清单第 {line} 行重复门店 {key}')
        by_key[key] = (row[1].strip() or key, row[2].strip() or '未分区', line)
    return by_key
