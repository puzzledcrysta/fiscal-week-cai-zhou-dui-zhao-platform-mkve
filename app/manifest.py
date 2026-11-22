from hashlib import sha256
from app.settings import RULE_VERSION, WEAK_RATIO, TRIGGER_DAYS, GAP_TOLERANCE, FISCAL


def manifest(raw, book):
    source_hash, book_hash = sha256(raw).hexdigest(), sha256(book).hexdigest()
    # 规则参数进入指纹：同一字节在不同阈值下是不同批次，避免结论串号。
    parameters = {'weak_ratio': WEAK_RATIO, 'trigger_days': TRIGGER_DAYS,
                  'gap_tolerance': GAP_TOLERANCE, 'fiscal': FISCAL}
    fingerprint = f'{RULE_VERSION}:{source_hash}:{book_hash}:{WEAK_RATIO}:{TRIGGER_DAYS}:{GAP_TOLERANCE}'
    run_id = sha256(fingerprint.encode()).hexdigest()
    return {'run_id': run_id, 'source_sha256': source_hash, 'book_sha256': book_hash,
            'version': RULE_VERSION, 'parameters': parameters}
