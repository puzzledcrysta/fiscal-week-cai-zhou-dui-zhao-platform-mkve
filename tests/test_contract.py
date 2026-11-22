import pytest
from app.errors import DataError
from app.modules.contract.service import normalize
from app.modules.intake.service import intake


def converted(source):
    return normalize(intake(source))


def test_missing_required(source):
    bad = [item for item in converted(source)[1] if item['code'] == 'REQUIRED']
    assert {item['key'] for item in bad} == {'00109'}


def test_leading_zero_preserved(source):
    assert converted(source)[0][0]['key'] == '00101'


def test_offsets_normalized_to_utc(source):
    rows, _ = converted(source)
    assert rows[0]['time'].endswith('+00:00')


def test_legacy_aliased():
    from pathlib import Path
    payload = (Path(__file__).resolve().parents[1] / 'sample_data' / 'legacy.csv').read_bytes()
    row, = converted(payload)[0]
    assert row['key'] == '00013' and row['revision'] == 1
    assert row['fields']['本年日销售'] == '700'


def test_fullwidth_revision(builder):
    csv_bytes = builder([['00201', '２', '2026-11-18T10:00:00+08:00', '2025-01-06',
                          '营业', '700', '1000', '']])
    row, = converted(csv_bytes)[0]
    assert row['revision'] == 2


def test_no_naive_clock(builder):
    csv_bytes = builder([['00202', '1', '2026-11-18T10:00:00', '2025-01-06',
                          '营业', '700', '1000', '']])
    assert [row['code'] for row in converted(csv_bytes)[1]] == ['TIMESTAMP']


def test_invalid_status_rejected(builder):
    csv_bytes = builder([['00203', '1', '2026-11-18T10:00:00+08:00', '2025-01-06',
                          '装修', '700', '1000', '']])
    assert [row['code'] for row in converted(csv_bytes)[1]] == ['STATUS_INVALID']


def test_unknown_columns_not_accepted():
    with pytest.raises(DataError) as error:
        normalize(intake(b'foo,bar\n1,2'))
    assert error.value.code == 'CONTRACT'
