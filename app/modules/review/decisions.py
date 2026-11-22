from app.errors import DataError
from app.store import connection
from app.modules.runs.repository import lookup
from .decisions_ledger import decide as persist_decision, timeline as load_timeline


def timeline(run_id):
    with connection() as db:
        lookup(db, run_id)
    return load_timeline(run_id)


def decide(run_id, version, decision, note):
    note = note.strip()
    with connection() as db:
        lookup(db, run_id)
        current = db.execute('SELECT COALESCE(MAX(version),0) FROM reviews WHERE run_id=?', (run_id,)).fetchone()[0]
        if current != version:
            raise DataError('STALE', '确认版本已过期，请刷新', 409)
        # 以实时预警台账判断是否还有未确认项（批次确认后 run 缓存可能滞后）。
        open_alerts = db.execute(
            'SELECT 1 FROM alerts WHERE confirmed_run IS NULL LIMIT 1').fetchone()
        if (decision == '退回' or open_alerts) and not note:
            raise DataError('REVIEW_NOTE', '退回或有未确认预警时须填写处理意见')
    return persist_decision(run_id, decision, note)
