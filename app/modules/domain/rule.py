from datetime import timedelta
from decimal import Decimal as D
from app.errors import DataError
from .values import calendar, number, whole, parts


def index(text, start, weeks):
    result = {}
    for item in parts(text):
        raw_day, sep, raw_amount = item.partition(':')
        if not sep:
            raise DataError('FISCAL_FORMAT', '日销售须包含日期和销售额')
        day = calendar(raw_day)
        offset = (day-start).days
        if not 0 <= offset < weeks*7:
            raise DataError('FISCAL_SPAN', f'{day} 超出本财年')
        amount = None if raw_amount == '停业' else number(raw_amount, -10**8, 10**8)
        if offset in result and result[offset] != amount:
            raise DataError('FISCAL_CONFLICT', f'{day} 有互相矛盾的营业记录')
        result[offset] = amount
    return result


def evaluate(row):
    previous, current = calendar(row['上年期首']), calendar(row['本年期首'])
    prev_count, cur_count = whole(row['上年周数'], 52, 53), whole(row['本年周数'], 52, 53)
    if previous.weekday() or current-previous != timedelta(weeks=prev_count):
        raise DataError('FISCAL_BOUNDARY', '期首须为周一，且两期连续')
    before = index(row['上年日销售'], previous, prev_count)
    after = index(row['本年日销售'], current, cur_count)
    delta, used, skipped = D(0), 0, 0
    weeks = {}
    for offset in sorted(before.keys() | after.keys()):
        a,b = before.get(offset), after.get(offset)
        if offset >= 364 or a is None or b is None:
            skipped += 1
            continue
        value = b-a
        week = offset//7+1
        weeks[week] = weeks.get(week, D(0))+value
        delta += value
        used += 1
    if not used:
        raise DataError('FISCAL_NO_PAIR', '共有财周内没有双方营业日')
    proof = []
    for week, value in weeks.items():
        period = ((week-1)//13)*3 + (1 if (week-1)%13<4 else 2 if (week-1)%13<8 else 3)
        proof.append((f'第{period:02}期 W{week:02}', value, '元'))
    extra = sum((amount for offset, amount in after.items() if offset >= 364 and amount is not None), D(0))
    previous_extra = sum((amount for offset, amount in before.items() if offset >= 364 and amount is not None), D(0))
    proof += [('双方营业',used,'日'),('未配对',skipped,'日'),('本年闰周',extra,'元'),('上年闰周',previous_extra,'元')]
    return delta, proof
