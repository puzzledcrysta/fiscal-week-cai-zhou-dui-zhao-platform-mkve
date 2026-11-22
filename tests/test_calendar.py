import pytest
from app.errors import DataError
from app.modules.domain.calendar import (
    FiscalCalendar, CURRENT, PRIOR, pair_baseline, continuity_ok, WEEKDAYS,
)


def test_fiscal_anchors_are_mondays_and_contiguous():
    assert CURRENT.anchor.weekday() == 0 and PRIOR.anchor.weekday() == 0
    assert continuity_ok() is True


def test_same_weekday_baseline_maps_to_prior_fiscal_week():
    # 本财年 W01 周一对照上年 W01 周一；W02 周三对照上年 W02 周三。
    base, week, weekday, label = pair_baseline(CURRENT.day_at(1, 0))
    assert base == PRIOR.day_at(1, 0) and (week, weekday) == (1, 0)
    base2, week2, weekday2, label2 = pair_baseline(CURRENT.day_at(2, 2))
    assert base2 == PRIOR.day_at(2, 2) and (week2, weekday2) == (2, 2)
    assert 'W02' in label2 and WEEKDAYS[2] in label2


def test_leap_week_has_no_current_counterpart():
    # 上年 53 周；本年只有 52 周，不存在第 53 周配对。
    assert PRIOR.weeks == 53 and CURRENT.weeks == 52
    last_current = CURRENT.day_at(52, 6)
    base, week, _, _ = pair_baseline(last_current)
    assert week == 52 and base == PRIOR.day_at(52, 6)


def test_outside_current_year_rejected():
    with pytest.raises(DataError) as error:
        pair_baseline(CURRENT.anchor.replace(year=CURRENT.anchor.year - 1))
    assert error.value.code == 'FISCAL_SPAN'


def test_period_label_uses_445():
    cal = FiscalCalendar(CURRENT.anchor, 52)
    # 每季 13 周：第 1-4 周属期 1，5-8 属期 2，9-13 属期 3。
    assert [cal.period_of(w) for w in (1, 4, 5, 8, 9, 13)] == [1, 1, 2, 2, 3, 3]
