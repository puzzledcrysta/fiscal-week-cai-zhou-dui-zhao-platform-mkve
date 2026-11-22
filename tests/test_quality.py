from app.modules.contract.service import normalize
from app.modules.intake.service import intake
from app.modules.quality.service import inspect
from tests.conftest import make_csv, day_row
from app.modules.domain.calendar import CURRENT


def report(source):
    return inspect(*normalize(intake(source)))


def test_conflicting_latest_revision_quarantined(source):
    result = report(source)
    keys = {row['key'] for row in result['ready']}
    assert '00107' not in keys
    assert [row['code'] for row in result['rejected'] if row['key'] == '00107'] == ['REV_CONFLICT', 'REV_CONFLICT']


def test_exact_duplicate_suppressed(source):
    taken = report(source)['suppressed']
    # 00111 只有一条；00106 的同键同日由版本归并处理，重复传输记入 suppressed。
    assert any(row['code'] == 'SUPERSEDED' and row['key'] == '00106' for row in taken)


def test_prefers_high_revision(source):
    rows = [r for r in report(source)['ready'] if r['key'] == '00106' and r['day'] == '2025-01-06']
    row, = rows
    assert row['revision'] == 2 and row['fields']['本年日销售'] == '900'


def test_older_revision_explained(source):
    suppressed = report(source)['suppressed']
    assert any(row['key'] == '00106' and row['code'] == 'SUPERSEDED' for row in suppressed)


def test_reason_counts(source):
    codes = report(source)['reasons']
    assert codes == {'REQUIRED': 1, 'REV_CONFLICT': 2, 'STATUS_INVALID': 1, 'WIDTH': 1}


def test_version_key_is_store_and_day(builder):
    # 同一门店两个不同营业日各自独立归并，互不覆盖。
    d1, d2 = CURRENT.day_at(1, 0).isoformat(), CURRENT.day_at(1, 1).isoformat()
    payload = make_csv([day_row('00301', d1, amount='700'), day_row('00301', d2, amount='700')])
    ready = report(payload)['ready']
    assert {row['day'] for row in ready} == {d1, d2}
