from datetime import datetime, timezone
from app.errors import DataError
from app.store import connection


def created_stamp():
    return datetime.now(timezone.utc).isoformat()


def decide(run_id, decision, note):
    if decision not in {'确认', '退回'}:
        raise DataError('REVIEW_DECISION', '确认结论无效')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        current = db.execute('SELECT COALESCE(MAX(version),0) FROM reviews WHERE run_id=?', (run_id,)).fetchone()[0]
        record = {'version': current + 1, 'decision': decision, 'note': note,
                  'changed': created_stamp()}
        db.execute('INSERT INTO reviews(run_id,version,decision,note,changed) VALUES (?,?,?,?,?)',
                   (run_id, *record.values()))
        return record


def timeline(run_id):
    with connection() as db:
        return list(map(dict, db.execute(
            'SELECT version,decision,note,changed FROM reviews WHERE run_id=? ORDER BY version DESC', (run_id,))))
