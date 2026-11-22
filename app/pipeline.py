from app.evidence import distribution
from app.modules.intake.service import intake
from app.modules.contract.service import normalize
from app.modules.quality.service import inspect
from app.modules.domain.service import calculate
from app.modules.reconcile.service import enrich


def stages(source):
    raw = intake(source)
    contract, rejected = normalize(raw)
    quality = inspect(contract, rejected)
    days, intervals, domain_bad = calculate(quality['ready'])
    bad = sorted([*quality['rejected'], *domain_bad], key=lambda row: row['line'])
    return {'intake': raw, 'contract': contract, 'quality': quality, 'days': days,
            'intervals': intervals, 'domain_bad': domain_bad, 'rejected': bad}


def execute(source, book):
    result = stages(source)
    raw, days, bad = (result[key] for key in ('intake', 'days', 'rejected'))
    suppressed = result['quality']['suppressed']
    counts = {'input': raw['input_count'], 'days': len(days), 'rejected': len(bad),
              'suppressed': len(suppressed), 'blank': len(raw['blank_lines']),
              'repeated_header': len(raw['header_lines'])}
    # 输入 = 计入对照 + 隔离 + 版本替换 + 空白 + 重复表头，逐行闭合，坏行全部留痕不丢失。
    balanced = counts['input'] == counts['days'] + counts['rejected'] + counts['suppressed'] \
        + counts['blank'] + counts['repeated_header']
    master = enrich(days, result['intervals'], book)
    weak = sum(1 for day in days if day.get('weak'))
    non_comparable = sum(1 for day in days if not day['comparable'])
    return {'counts': {**counts, 'weak': weak, 'non_comparable': non_comparable,
                       'intervals': len(result['intervals'])},
            'balanced': balanced, 'days': days, 'intervals': result['intervals'],
            'quarantine': bad, 'suppressed': suppressed, 'reasons': distribution(bad),
            'master': master, 'encoding': raw['encoding']}
