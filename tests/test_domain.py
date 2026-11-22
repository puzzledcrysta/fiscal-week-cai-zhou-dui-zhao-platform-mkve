from decimal import Decimal
import pytest
from app.errors import DataError
from app.modules.domain.rule import evaluate


def test_leap_week(cases):
    # TRAP-107
    actual, proof = evaluate(cases['leap_week'])
    assert actual == Decimal('20')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['上年闰周'])) == Decimal('1100')


def test_closed_excluded(cases):
    actual, proof = evaluate(cases['closed_excluded'])
    assert actual == Decimal('20')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['未配对'])) == Decimal('1')


def test_negative_delta(cases):
    actual, proof = evaluate(cases['negative_delta'])
    assert actual == Decimal('-30.75')
    assert proof


def test_zero_counts(cases):
    actual, proof = evaluate(cases['zero_counts'])
    assert actual == Decimal('45')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['双方营业'])) == Decimal('1')


def test_no_double_count(cases):
    actual, proof = evaluate(cases['no_double_count'])
    assert actual == Decimal('10')
    assert proof


def test_period_transition(cases):
    actual, proof = evaluate(cases['period_transition'])
    assert actual == Decimal('20')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['第02期 W05'])) == Decimal('15')


def test_calendar_boundary(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['calendar_boundary'])
    assert error.value.code == 'FISCAL_BOUNDARY'


def test_conflicting_day(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['conflicting_day'])
    assert error.value.code == 'FISCAL_CONFLICT'


def test_outside_year(cases):
    # TRAP-23
    with pytest.raises(DataError) as error:
        evaluate(cases['outside_year'])
    assert error.value.code == 'FISCAL_SPAN'
