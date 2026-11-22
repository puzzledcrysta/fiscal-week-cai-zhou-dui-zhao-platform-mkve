from app.errors import DataError
from app.evidence import finding
from app.settings import KEY, FIELDS
from app.modules.domain.values import instant, whole
from .schema import mapping, MISSING, STATUS


def normalize(source):
    names = mapping(source['header'])
    passed, rejected = [], list(source['rejected'])
    for record in source['rows']:
        values = dict(zip(names, record['values']))
        key = values[KEY]
        revision = None
        try:
            if not any(values[k].casefold() in MISSING for k in (KEY, '修订号')):
                revision = whole(values['修订号'], 1, 10 ** 9)
            if any(values[k].casefold() in MISSING for k in (KEY, '修订号', '提交时间', '营业日期', '营业状态')):
                raise DataError('REQUIRED', '主键、修订号、时间、营业日期和状态均须填写')
            changed = instant(values['提交时间']).isoformat()
            status = values['营业状态']
            if status not in STATUS:
                raise DataError('STATUS_INVALID', f'营业状态须为 {"/".join(STATUS)}')
            # 营业日必须有本年销售额；停业/缺报本就无金额。基准允许留空（无基准归为不可比，不作坏行）。
            if status == '营业' and values['本年日销售'].casefold() in MISSING:
                raise DataError('REQUIRED', '营业状态须填写本年日销售')
        except DataError as error:
            issue = finding(dict(record, key=key), error.code, str(error))
            if revision is not None:
                issue['revision'] = revision
            rejected.append(issue)
            continue
        passed.append({'key': key, 'revision': revision, 'time': changed, 'line': record['line'],
                       'raw': record['raw'], 'status': status,
                       'fields': {field: values[field] for field in FIELDS},
                       'note': values.get('原始备注', '')})
    return passed, rejected
