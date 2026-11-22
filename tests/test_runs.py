from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from app.modules.runs.service import run


def test_idempotent_same_bytes_one_run(client):
    first = client.post('/api/runs', json={}).json()
    second = client.post('/api/runs', json={}).json()
    assert first['manifest']['run_id'] == second['manifest']['run_id']
    assert len(client.get('/api/runs').json()) == 1


def test_different_book_new_run(client, book):
    first = client.post('/api/runs', json={}).json()['manifest']
    second = client.post('/api/runs', json={'book': book.decode() + '\n'}).json()['manifest']
    assert first['source_sha256'] == second['source_sha256']
    assert first['run_id'] != second['run_id']


def test_replay_same_result(client):
    result = client.post('/api/runs', json={}).json()
    rid = result['manifest']['run_id']
    assert client.post(f'/api/runs/{rid}/replay').json()['manifest']['run_id'] == rid


def test_manifest_fingerprint_and_params(client, source, book):
    proof = client.post('/api/runs', json={}).json()['manifest']
    assert proof['source_sha256'] == sha256(source).hexdigest()
    assert proof['book_sha256'] == sha256(book).hexdigest()
    assert proof['parameters']['weak_ratio'] == '0.80'
    assert proof['parameters']['trigger_days'] == 2


def test_failed_run_not_written(client):
    assert client.post('/api/runs', json={'data': 'bad\na'}).status_code == 422
    assert client.get('/api/runs').json() == []


def test_concurrent_runs_one_record(client, source, book):
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: run(source, book), range(4)))
    assert all(item['manifest']['run_id'] == results[0]['manifest']['run_id'] for item in results)
    assert len(client.get('/api/runs').json()) == 1


def test_missing_id(client):
    response = client.get('/api/runs/not-found')
    assert (response.status_code, response.json()['code']) == (404, 'RUN_UNKNOWN')


def test_encoded_source_same_fingerprint(client, source):
    from base64 import b64encode
    expected = client.post('/api/runs', json={}).json()
    uploaded = client.post('/api/runs', json={'data_base64': b64encode(source).decode()})
    assert uploaded.status_code == 200
    assert uploaded.json()['manifest']['run_id'] == expected['manifest']['run_id']


def test_invalid_encoding_explicit(client):
    problem = client.post('/api/runs', json={'data_base64': 'bad!'})
    assert (problem.status_code, problem.json()['code']) == (422, 'ENCODING')


def test_history_reopens_inputs(client, source, book):
    from base64 import b64decode
    rid = client.post('/api/runs', json={}).json()['manifest']['run_id']
    restored = client.get(f'/api/runs/{rid}/source').json()
    assert b64decode(restored['data_base64']) == source
    assert b64decode(restored['book_base64']) == book
