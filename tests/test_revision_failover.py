import csv
from io import StringIO
from app.pipeline import stages


def test_known_invalid_latest_revision_blocks_valid_old_row(source):
    reader = csv.reader(StringIO(source.decode('utf-8-sig')))
    header = next(reader)
    rows = list(reader)
    old = next(r for r in rows if r and r[0] == '00106')
    new = old.copy()
    new[1] = '3'
    new[5] = ''  # 最高修订缺本年销售额 -> 必填坏行
    stream = StringIO(newline='')
    csv.writer(stream).writerows([header, new, old])
    report = stages(stream.getvalue().encode())
    keys = {row['key'] for row in report['days']}
    assert '00106' not in keys
    codes = [item['code'] for item in report['rejected'] if item['key'] == '00106']
    assert 'REV_BLOCKED' in codes
