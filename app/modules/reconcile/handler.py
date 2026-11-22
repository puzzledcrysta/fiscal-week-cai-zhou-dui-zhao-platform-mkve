from fastapi import APIRouter
from app.inputs import Paired
from app.pipeline import execute

router = APIRouter()


@router.post('/api/reconcile')
def reconcile(source: Paired):
    report = execute(source.raw(), source.ledger())
    return {'master': report['master'], 'counts': report['counts'], 'balanced': report['balanced']}
