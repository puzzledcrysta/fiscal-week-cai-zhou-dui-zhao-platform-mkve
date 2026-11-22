import json
from datetime import datetime, timezone
from time import perf_counter
from app.manifest import manifest
from app.pipeline import execute
from app.modules.signals.ledger import load_state, merge, confirm_batch
from .repository import fetch, persist


def run(source, book):
    proof = manifest(source, book)
    run_id = proof['run_id']
    prior_alerts, confirmed_runs, _ = load_state()
    started = perf_counter()
    result = execute(source, book)
    created = datetime.now(timezone.utc).isoformat()
    proof.update(elapsed_ms=round((perf_counter() - started) * 1000, 2), created=created)

    alerts, corrections = merge(run_id, result['intervals'], prior_alerts, confirmed_runs)
    _, confirmed_after, _ = load_state()
    result['manifest'] = proof
    result['alerts'] = alerts
    result['corrections'] = corrections
    result['confirmed_run'] = run_id in confirmed_after
    stored = persist(run_id, source, book, result, created)
    return json.loads(stored['result'])


def replay(run_id):
    old = fetch(run_id)
    return run(old['source'], old['book'])


def get(run_id):
    return json.loads(fetch(run_id)['result'])


def confirm(run_id):
    old = fetch(run_id)
    created = json.loads(old['result'])['manifest']['created']
    alerts = confirm_batch(run_id, created)
    return confirmations_view(alerts)


def confirmations_view(alerts):
    locked = [a for a in alerts if a['confirmed_run'] is not None]
    return {'confirmed_runs': sorted({a['confirmed_run'] for a in locked}),
            'locked_alerts': locked, 'count': len(locked)}
