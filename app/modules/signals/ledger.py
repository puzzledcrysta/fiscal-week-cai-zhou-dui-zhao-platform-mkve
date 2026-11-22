import json
from app.store import connection


def load_state():
    """读取既有预警与批次确认水位。已确认区间为受保护事实，任何重跑不得改写。"""
    with connection() as db:
        alerts = [dict(row) for row in db.execute('SELECT * FROM alerts ORDER BY key, start_day')]
        for alert in alerts:
            alert['evidence'] = json.loads(alert['evidence'])
            alert['corrections'] = json.loads(alert['corrections'])
        marks = [dict(row) for row in db.execute('SELECT run_id, created FROM confirmations ORDER BY created')]
    return alerts, {row['run_id'] for row in marks}, marks


def _upsert_alert(db, alert):
    payload = (alert['key'], alert['start_day'], alert['trigger_day'], alert['end_day'],
               alert['status'], alert['first_run'], alert['last_run'],
               json.dumps(alert['evidence'], ensure_ascii=False),
               json.dumps(alert.get('corrections', []), ensure_ascii=False),
               alert.get('confirmed_run'), alert.get('confirmed_at'),
               alert.get('decision_note'))
    # 冲突时只回写未确认区间的延伸字段；status/confirmed_* 受确认水位保护，永不被重算覆盖。
    db.execute('''INSERT INTO alerts(key,start_day,trigger_day,end_day,status,first_run,last_run,
                 evidence,corrections,confirmed_run,confirmed_at,decision_note)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                 ON CONFLICT(key,start_day) DO UPDATE SET
                   end_day=CASE WHEN alerts.confirmed_run IS NULL THEN excluded.end_day ELSE alerts.end_day END,
                   last_run=excluded.last_run,
                   evidence=CASE WHEN alerts.confirmed_run IS NULL THEN excluded.evidence ELSE alerts.evidence END,
                   corrections=excluded.corrections''', payload)


def merge(run_id, computed, prior_alerts=None, confirmed_runs=None):
    """把本批纯计算结果并入不可变预警台账，返回写入后的权威状态与本批留痕。

    单调性约束（业务硬规则）：
    - 始终以数据库为权威状态；已确认预警完全锁定，重跑不改字段。
    - 「已确认门店与区间不能新增」：只要门店已有确认区间，该门店的新区间一律拒收并留痕。
    - 未确认区间只允许 end_day 向后延伸；迟到数据使区间缩短/消失时不回退，追加 corrections。
    """
    prior, confirmed, _ = load_state()
    indexed = {(a['key'], a['start_day']): a for a in prior}
    locked_stores = {a['key'] for a in prior if a['confirmed_run'] in confirmed}
    computed_index = {(c['key'], c['start_day']): c for c in computed}
    corrections, blocked = [], []

    for interval in computed:
        identity = (interval['key'], interval['start_day'])
        existing = indexed.get(identity)
        if existing is None:
            if interval['key'] in locked_stores:
                note = {'run_id': run_id, 'kind': 'BLOCKED_LOCKED_STORE',
                        'detail': f"门店 {interval['key']} 已有确认区间，新区间 {identity[1]} 不予新增"}
                blocked.append(note)
                continue
            prior.append({
                'key': interval['key'], 'start_day': interval['start_day'],
                'trigger_day': interval['trigger_day'], 'end_day': interval['end_day'],
                'status': 'open', 'first_run': run_id, 'last_run': run_id,
                'evidence': _evidence(interval), 'corrections': [],
                'confirmed_run': None, 'confirmed_at': None, 'decision_note': None,
            })
            continue
        if existing['confirmed_run'] in confirmed:
            continue
        if interval['end_day'] < existing['end_day']:
            note = {'run_id': run_id, 'kind': 'LATE_DATA',
                    'detail': f"迟到数据算出的区间止于 {interval['end_day']}，早于已登记 {existing['end_day']}，保留原结论",
                    'computed_end': interval['end_day'], 'kept_end': existing['end_day']}
            existing['corrections'].append(note)
            corrections.append(note)
        else:
            existing['end_day'] = interval['end_day']
            existing['evidence'] = _evidence(interval, existing['evidence'])
        existing['last_run'] = run_id

    for identity, existing in indexed.items():
        if identity in computed_index or existing['confirmed_run'] in confirmed:
            continue
        note = {'run_id': run_id, 'kind': 'NOT_REPRODUCED',
                'detail': f"本批未复现自 {existing['start_day']} 的区间，保留登记并标记待人工复核"}
        existing.setdefault('corrections', []).append(note)
        corrections.append(note)
        existing['last_run'] = run_id

    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        for alert in prior:
            _upsert_alert(db, alert)

    final_alerts, _, _ = load_state()
    return final_alerts, corrections + blocked


def _evidence(interval, previous=None):
    base = previous or {'trigger_day': interval['trigger_day'], 'baseline_day': interval['baseline_day'],
                        'weak_days': [], 'gap_days': [], 'fiscal_weeks': []}
    base.update({'trigger_day': interval['trigger_day'], 'baseline_day': interval['baseline_day'],
                 'weak_days': interval['weak_days'], 'gap_days': interval['gap_days'],
                 'fiscal_weeks': interval['fiscal_weeks']})
    return base


def confirm_batch(run_id, created):
    """登记批次确认水位。同一批次重跑确认幂等；确认后该批次门店与区间不再新增。

    确认范围是「本批次首次产生的区间」（first_run = run_id）中的未确认项。
    """
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT OR IGNORE INTO confirmations(run_id, created) VALUES (?,?)', (run_id, created))
        db.execute('UPDATE alerts SET status=?, confirmed_run=?, confirmed_at=? '
                   'WHERE first_run=? AND confirmed_run IS NULL',
                   ('confirmed', run_id, created, run_id))
        rows = [dict(row) for row in db.execute('SELECT * FROM alerts ORDER BY key, start_day')]
    for row in rows:
        row['evidence'] = json.loads(row['evidence'])
        row['corrections'] = json.loads(row['corrections'])
    return rows


def timeline(run_id):
    with connection() as db:
        return list(map(dict, db.execute(
            'SELECT version,decision,note,changed FROM reviews WHERE run_id=? ORDER BY version DESC', (run_id,))))
