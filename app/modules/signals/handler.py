from fastapi import APIRouter
from app.modules.signals.ledger import load_state

router = APIRouter()


@router.get('/api/signals')
def signals():
    alerts, confirmed_runs, marks = load_state()
    open_alerts = [a for a in alerts if a['confirmed_run'] is None]
    return {'alerts': alerts, 'open': open_alerts,
            'confirmed_runs': sorted(confirmed_runs), 'confirmations': marks,
            'open_count': len(open_alerts), 'total': len(alerts)}
