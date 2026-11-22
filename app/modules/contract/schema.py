from app.settings import KEY, FIELDS
from app.errors import DataError

REQUIRED = (KEY, '修订号', '提交时间', *FIELDS, '营业状态')
ALIASES = {'门店编码': KEY, '门店号': KEY, '版本': '修订号', '更新时刻': '提交时间',
           '当日销售额': '本年日销售', '基准销售额': '上年同星期日销售', '备注': '原始备注'}
MISSING = {'', '-', 'n/a', 'null', '未知'}
# 营业状态：营业 / 停业（计划停业，明确不营业）/ 缺报（应报未报）。
STATUS = ('营业', '停业', '缺报')


def mapping(header):
    names = [ALIASES.get(name, name) for name in header]
    if len(set(names)) != len(names) or set(REQUIRED) - set(names):
        raise DataError('CONTRACT', '必需字段缺失或新旧字段重复')
    return names
