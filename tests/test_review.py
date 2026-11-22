import pytest


@pytest.fixture
def anchor(client):
    return client.post('/api/runs', json={}).json()['manifest']['run_id']


def review(client, anchor, version=0, decision='确认', note='已安排店长跟进'):
    return client.post(f'/api/review/{anchor}', json={'version': version, 'decision': decision, 'note': note})


def test_stale_version_rejected(client, anchor):
    assert review(client, anchor).json()['version'] == 1
    stale = review(client, anchor)
    assert (stale.status_code, stale.json()['code']) == (409, 'STALE')


def test_note_required_with_open_alerts(client, anchor):
    response = review(client, anchor, note='  ')
    assert (response.status_code, response.json()['code']) == (422, 'REVIEW_NOTE')


def test_versioned_history(client, anchor):
    assert review(client, anchor).status_code == 200
    assert review(client, anchor, 1, '退回', '请补停业旁证').status_code == 200
    assert [item['version'] for item in client.get(f'/api/review/{anchor}').json()] == [2, 1]


def test_export_reproducible(client, anchor):
    first = client.get(f'/api/export/{anchor}')
    second = client.get(f'/api/export/{anchor}')
    assert first.content == second.content and 'attachment' in first.headers['content-disposition']


def test_export_carries_alert_evidence(client, anchor):
    proof = client.get(f'/api/export/{anchor}').json()
    assert proof['alerts'] and proof['intervals']
    alert = proof['alerts'][0]
    assert alert['trigger_day'] and alert['evidence']['weak_days']
    assert proof['quarantine'] and proof['manifest']['parameters']


def test_decision_reaches_export(client, anchor):
    assert review(client, anchor).status_code == 200
    assert client.get(f'/api/export/{anchor}').json()['review'][0]['decision'] == '确认'


def test_confirm_then_review_note_rule_relaxes(client, anchor):
    # 批次确认后没有未确认预警，确认结论可免意见；退回仍须意见。
    client.post(f'/api/runs/{anchor}/confirm')
    ok = client.post(f'/api/review/{anchor}', json={'version': 0, 'decision': '确认', 'note': ''})
    assert ok.status_code == 200
    bad = client.post(f'/api/review/{anchor}', json={'version': 1, 'decision': '退回', 'note': ''})
    assert bad.json()['code'] == 'REVIEW_NOTE'
