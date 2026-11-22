from app.pipeline import execute


def test_input_rows_conserved(source, book):
    result = execute(source, book)
    assert result['balanced'] is True
    c = result['counts']
    assert c['input'] == c['days'] + c['rejected'] + c['suppressed'] + c['blank'] + c['repeated_header']


def test_quarantine_keeps_every_bad_row_with_reason(source, book):
    result = execute(source, book)
    codes = {row['code'] for row in result['quarantine']}
    # 坏行逐条留痕：必填、状态非法、版本冲突、列宽。
    assert {'REQUIRED', 'STATUS_INVALID', 'REV_CONFLICT', 'WIDTH'} <= codes
    assert all(row['line'] and row['detail'] for row in result['quarantine'])


def test_expected_stores_trigger(source, book):
    result = execute(source, book)
    triggered = {i['key'] for i in result['intervals']}
    # 00101（含停业缺口）、00103（含缺报缺口）、00105（跨周）、00108、00104 触发；
    # 00102 仅单日走弱、00106 修订后达标，不触发。
    assert triggered == {'00101', '00103', '00104', '00105', '00108'}
    assert '00102' not in triggered and '00106' not in triggered


def test_interval_carries_intervention_window_and_basis(source, book):
    result = execute(source, book)
    iv = next(i for i in result['intervals'] if i['key'] == '00101')
    assert iv['start_day'] <= iv['trigger_day'] <= iv['end_day']
    assert iv['gap_days'] == ['2025-01-07']  # 停业单日不断区间
    assert iv['weak_count'] >= 2


def test_cross_week_interval_flagged(source, book):
    result = execute(source, book)
    iv = next(i for i in result['intervals'] if i['key'] == '00105')
    assert iv['cross_week'] is True and iv['fiscal_weeks'] == [1, 2]


def test_master_enrichment_flags_unregistered(source, book):
    result = execute(source, book)
    iv = next(i for i in result['intervals'] if i['key'] == '00101')
    assert iv['store_name'] == '中山广场店' and iv['region'] == '华东一区'
    assert '00111' in result['master']['unregistered']
