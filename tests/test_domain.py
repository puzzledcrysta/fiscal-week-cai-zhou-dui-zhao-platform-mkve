from decimal import Decimal
import pytest
from app.errors import DataError
from app.modules.domain.rule import classify_day
from app.modules.domain.calendar import CURRENT


def rec(case):
    return {'key': '00101', 'line': 2, 'revision': 1, 'status': case['营业状态'],
            'fields': {'营业日期': case['营业日期'], '本年日销售': case['本年日销售'],
                       '上年同星期日销售': case['上年同星期日销售']}}


def test_weak_day_below_eighty_percent(cases):
    out = classify_day(rec(cases['weak_day']))
    assert out['code'] == 'WEAK' and out['weak'] is True
    assert Decimal(out['threshold']) == Decimal('800.00')
    assert Decimal(out['decline']) == Decimal('-300')


def test_threshold_boundary_is_not_weak(cases):
    out = classify_day(rec(cases['ok_day']))
    # 恰好等于 0.8 倍基准不算走弱（严格小于才触发）。
    assert out['code'] == 'OK' and out['weak'] is False


def test_closed_day_is_non_comparable_with_reason(cases):
    out = classify_day(rec(cases['closed_day']))
    assert out['comparable'] is False and out['code'] == 'NOT_OPEN'
    assert out['amount'] is None and '停业' in out['detail']


def test_missing_report_is_non_comparable_but_kept(cases):
    out = classify_day(rec(cases['missing_day']))
    assert out['comparable'] is False and out['code'] == 'BASE_MISSING'
    assert out['status'] == '缺报'


def test_missing_baseline_does_not_count_as_weak(cases):
    out = classify_day(rec(cases['no_baseline']))
    assert out['comparable'] is False and out['code'] == 'NO_BASELINE'


def test_open_day_requires_amount():
    bad = rec({'营业日期': CURRENT.day_at(1, 0).isoformat(), '营业状态': '营业',
               '本年日销售': '', '上年同星期日销售': '1000'})
    with pytest.raises(DataError) as error:
        classify_day(bad)
    assert error.value.code == 'REQUIRED'
