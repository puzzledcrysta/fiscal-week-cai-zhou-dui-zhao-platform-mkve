"""迟到数据、批次确认与不可倒退规则（本需求的核心验收）。"""
import csv
from io import StringIO
from tests.conftest import day_row
from app.modules.domain.calendar import CURRENT


def _rid(client):
    return client.post('/api/runs', json={}).json()['manifest']['run_id']


def modify_source(source, changes):
    rows = list(csv.reader(StringIO(source.decode('utf-8-sig'))))
    header, data = rows[0], rows[1:]
    for row in data:
        for key, day, value in changes:
            if row and row[0] == key and row[3] == day:
                row[5] = value
    out = StringIO(newline='')
    csv.writer(out).writerows([header, *data])
    return out.getvalue().encode()


def sample_bytes():
    from pathlib import Path
    return (Path(__file__).resolve().parents[1] / 'sample_data' / 'shift.csv').read_bytes()


def append_rows(source_bytes, extra):
    text = source_bytes.decode('utf-8-sig').rstrip('\n')
    lines = '\n'.join(','.join(str(cell) for cell in row) for row in extra)
    return (text + '\n' + lines + '\n').encode()


def test_confirmed_alerts_lock_across_rerun(client):
    rid = _rid(client)
    assert client.post(f'/api/runs/{rid}/confirm').json()['count'] >= 1
    rerun = client.post('/api/runs', json={}).json()
    assert rerun['confirmed_run'] is True
    assert all(a['status'] == 'confirmed' and a['confirmed_run'] == rid for a in rerun['alerts'])


def test_confirmation_is_idempotent(client):
    rid = _rid(client)
    first = client.post(f'/api/runs/{rid}/confirm').json()
    second = client.post(f'/api/runs/{rid}/confirm').json()
    assert first['count'] == second['count']
    assert len(client.get('/api/signals').json()['confirmations']) == 1


def test_confirmed_store_rejects_new_interval(client):
    rid = _rid(client)
    client.post(f'/api/runs/{rid}/confirm')
    # 已确认门店 00103：达标断开后再出现两个走弱日，构成新起始日区间，必须拒收。
    extra = [
        day_row('00103', CURRENT.day_at(3, 0).isoformat(), amount='950'),
        day_row('00103', CURRENT.day_at(3, 1).isoformat(), amount='100', rev=3),
        day_row('00103', CURRENT.day_at(3, 2).isoformat(), amount='100', rev=3),
    ]
    # 直接构造追加字节，避免与既有营业日冲突。
    import base64
    raw = base64.b64decode(client.get(f'/api/runs/{rid}/source').json()['data_base64'])
    payload = append_rows(raw, extra)
    report = client.post('/api/runs', json={'data': payload.decode()}).json()
    starts = [a['start_day'] for a in report['alerts'] if a['key'] == '00103']
    assert starts == ['2025-01-06']  # 只有原确认区间
    assert any(c['kind'] == 'BLOCKED_LOCKED_STORE' for c in report['corrections'])


def test_late_data_shortening_unconfirmed_alert_does_not_regress(client):
    first = client.post('/api/runs', json={}).json()
    alert = next(a for a in first['alerts'] if a['key'] == '00101')
    original_end = alert['end_day']
    # 迟到补报把最后一个走弱日改成达标，纯计算区间会缩短。
    late = modify_source(sample_bytes(), [('00101', '2025-01-09', '950')])
    report = client.post('/api/runs', json={'data': late.decode()}).json()
    kept = next(a for a in report['alerts'] if a['key'] == '00101')
    assert kept['end_day'] == original_end  # 结论不倒退
    assert any(c['kind'] == 'LATE_DATA' for c in kept['corrections'])


def test_late_data_extending_alert_updates_end_only(client):
    first = client.post('/api/runs', json={}).json()
    before = next(a for a in first['alerts'] if a['key'] == '00101')
    # 追加一个新的走弱营业日，区间应向后延伸而非新增区间。
    extra = day_row('00101', CURRENT.day_at(1, 4).isoformat(), amount='100')
    text = append_rows(sample_bytes(), [extra]).decode()
    report = client.post('/api/runs', json={'data': text}).json()
    after = next(a for a in report['alerts'] if a['key'] == '00101')
    assert after['start_day'] == before['start_day']
    assert after['end_day'] == CURRENT.day_at(1, 4).isoformat()
    assert after['trigger_day'] == before['trigger_day']  # 触发日固定不变


def test_alert_evidence_is_queryable(client):
    report = client.post('/api/runs', json={}).json()
    alert = next(a for a in report['alerts'] if a['key'] == '00101')
    ev = alert['evidence']
    assert ev['trigger_day'] and ev['baseline_day']
    assert ev['weak_days'] and ev['gap_days'] and ev['fiscal_weeks']


def test_signals_endpoint_lists_open_and_confirmed(client):
    rid = _rid(client)
    signals = client.get('/api/signals').json()
    assert signals['total'] == signals['open_count'] and signals['open_count'] >= 1
    client.post(f'/api/runs/{rid}/confirm')
    after = client.get('/api/signals').json()
    assert after['open_count'] == 0 and after['total'] >= 1
