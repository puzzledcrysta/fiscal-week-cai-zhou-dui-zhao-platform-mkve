from fastapi import APIRouter
from app.inputs import Source
from app.pipeline import stages

router = APIRouter()


@router.post('/api/domain')
def recalculate(source: Source):
    result = stages(source.raw())
    return {'days': result['days'], 'intervals': result['intervals'],
            'rejected': result['rejected'], 'domain_bad': result['domain_bad']}
