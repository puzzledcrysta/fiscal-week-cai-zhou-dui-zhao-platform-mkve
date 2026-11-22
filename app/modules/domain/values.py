from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from unicodedata import normalize
from app.errors import DataError


def number(raw, minimum=None, maximum=None):
    value = normalize('NFKC', str(raw)).strip()
    if not re.fullmatch(r'[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?', value) or len(value) > 28:
        raise DataError('NUMBER', f'数字格式无效 {raw[:80]}')
    try:
        parsed = Decimal(value.replace(',', ''))
    except InvalidOperation as error:
        raise DataError('NUMBER', f'数字格式无效 {raw[:80]}') from error
    if (minimum is not None and parsed < minimum) or (maximum is not None and parsed > maximum):
        raise DataError('RANGE', f'数字越界 {raw[:80]}')
    return parsed


def whole(raw, minimum=None, maximum=None):
    parsed = number(raw, minimum, maximum)
    if parsed != parsed.to_integral_value():
        raise DataError('NUMBER', f'需要整数 {raw[:80]}')
    return int(parsed)


def instant(value):
    try:
        if 'T' not in value:
            raise ValueError('无时间')
        stamp = datetime.fromisoformat(value)
        if stamp.utcoffset() is None:
            raise ValueError('无偏移')
        return stamp.astimezone(timezone.utc)
    except (ValueError, OverflowError) as error:
        raise DataError('TIMESTAMP', f'需要带偏移的时间 {value[:80]}') from error


def calendar(raw):
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', str(raw).strip()):
        raise DataError('DATE', f'日期须使用 YYYY-MM-DD {str(raw)[:80]}')
    try:
        return date.fromisoformat(raw.strip())
    except ValueError as error:
        raise DataError('DATE', f'日历日期无效 {str(raw)[:80]}') from error
