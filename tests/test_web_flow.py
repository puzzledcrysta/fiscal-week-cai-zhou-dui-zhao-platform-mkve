from app.settings import TITLE


def test_page_and_stages(client):
    page = client.get('/')
    assert page.status_code == 200 and TITLE in page.text
    for route, field in [('intake', 'encoding'), ('contract', 'accepted'), ('quality', 'ready'),
                         ('domain', 'days'), ('reconcile', 'balanced')]:
        response = client.post(f'/api/{route}', json={})
        assert response.status_code == 200 and field in response.json()


def test_malformed_sample_can_retry(client):
    invalid = client.post('/api/runs', json={'data': '"ab'})
    assert invalid.json()['code'] == 'CSV'
    assert client.post('/api/runs', json={}).json()['counts']['days'] >= 1


def test_full_warning_flow(client):
    report = client.post('/api/runs', json={}).json()
    assert report['balanced'] and report['intervals']
    rid = report['manifest']['run_id']
    signals = client.get('/api/signals').json()
    assert signals['open_count'] == len(report['intervals'])
    confirmed = client.post(f'/api/runs/{rid}/confirm').json()
    assert confirmed['count'] == signals['open_count']
    assert client.get('/api/signals').json()['open_count'] == 0


def test_health(client):
    assert client.get('/health').json() == {'status': 'ok'}
