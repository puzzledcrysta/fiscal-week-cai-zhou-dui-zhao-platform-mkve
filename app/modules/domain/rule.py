"""单日对照与走弱判定（纯函数，便于逐算例测试）。"""
from decimal import Decimal
from app.errors import DataError
from app.settings import WEAK_RATIO
from .values import calendar, number
from .calendar import pair_baseline

RATIO = Decimal(WEAK_RATIO)
OPEN = '营业'
CLOSED = '停业'
MISSING = '缺报'
# 不可比原因：停业（计划内，不算持续下滑）与缺报（应报未报，同样不断区间但需说明）。
NON_COMPARABLE = {CLOSED: 'NOT_OPEN', MISSING: 'BASE_MISSING'}


def _amount(raw, allow_blank):
    text = (raw or '').strip()
    if not text:
        if allow_blank:
            return None
        raise DataError('REQUIRED', '营业日须填写本年销售额')
    return number(text, -10 ** 8, 10 ** 8)


def classify_day(record):
    """把一条已采信的门店-日记录归一成对照结论。

    返回 dict：day/status/可比与否/基准、本年值、阈值、降幅、财周标签、原因码。
    无法判定时抛 DataError，由上层作为坏行隔离（记录不丢失）。
    """
    day = calendar(record['fields']['营业日期'])
    baseline_date, week, weekday, label = pair_baseline(day)
    status = record['status']
    base = {
        'key': record['key'], 'line': record['line'], 'revision': record['revision'],
        'day': day.isoformat(), 'baseline_day': baseline_date.isoformat(),
        'fiscal_week': week, 'weekday': weekday, 'calendar': label, 'status': status,
    }
    if status in NON_COMPARABLE:
        base.update(comparable=False, code=NON_COMPARABLE[status],
                    detail='计划停业' if status == CLOSED else '当日缺报，待补',
                    amount=None, baseline=None, threshold=None, decline=None)
        return base
    amount = _amount(record['fields']['本年日销售'], allow_blank=False)
    baseline = _amount(record['fields']['上年同星期日销售'], allow_blank=True)
    if baseline is None:
        base.update(comparable=False, code='NO_BASELINE', detail='缺少上年同星期营业基准',
                    amount=str(amount), baseline=None, threshold=None, decline=None)
        return base
    threshold = (baseline * RATIO).quantize(Decimal('0.01'))
    weak = amount < threshold
    decline = amount - baseline
    base.update(comparable=True, weak=weak, code='WEAK' if weak else 'OK',
                detail='低于同星期基准八成' if weak else '达到同星期基准八成',
                amount=str(amount), baseline=str(baseline), threshold=str(threshold),
                decline=str(decline))
    return base
