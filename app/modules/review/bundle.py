import json
from app.modules.runs.service import get
from .decisions import timeline


def bundle(run_id):
    history = timeline(run_id)
    run = get(run_id)
    # 导出保留触发日、上年基准、本批依据、连续区间与迟到数据留痕，供值班干预与审计。
    return json.dumps({'manifest': run['manifest'], 'counts': run['counts'],
                       'days': run['days'], 'intervals': run['intervals'],
                       'alerts': run['alerts'], 'corrections': run['corrections'],
                       'quarantine': run['quarantine'], 'suppressed': run['suppressed'],
                       'master': run['master'], 'review': history},
                      ensure_ascii=False, indent=2)
