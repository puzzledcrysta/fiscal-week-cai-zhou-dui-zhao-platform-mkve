"""四四五财周日历与同星期对照。

自然日期映射到 (财年, 财周, 星期)。上年与本年按「同财周序号 + 同星期」配对，
这正是「上年同星期营业日」。上年第 53 闰周在本年没有对应财周，单独标记、不参与对照。
"""
from datetime import date, timedelta
from app.errors import DataError
from app.settings import FISCAL
from .values import calendar

WEEKDAYS = ('周一', '周二', '周三', '周四', '周五', '周六', '周日')
# 每季 13 周：4+4+5。返回 1..4 的期序号。
PERIODS = (4, 4, 5)


class FiscalCalendar:
    def __init__(self, anchor, weeks):
        self.anchor = anchor if isinstance(anchor, date) else calendar(anchor)
        if self.anchor.weekday() != 0:
            raise DataError('FISCAL_BOUNDARY', '财年期首须为周一')
        self.weeks = weeks
        self.days = weeks * 7

    def locate(self, day):
        """返回 (财周序号 1..weeks, 星期 0..6, 距期首天数)；越界返回 None。"""
        offset = (day - self.anchor).days
        if offset < 0 or offset >= self.days:
            return None
        return offset // 7 + 1, offset % 7, offset

    def day_at(self, week, weekday):
        return self.anchor + timedelta(days=(week - 1) * 7 + weekday)

    def period_of(self, week):
        within = (week - 1) % 13
        boundary = 0
        for period, span in enumerate(PERIODS, start=1):
            boundary += span
            if within < boundary:
                return period
        return 3

    def label(self, week, weekday):
        quarter = (week - 1) // 13 + 1
        return f'Q{quarter} 第{self.period_of(week)}期 W{week:02d} {WEEKDAYS[weekday]}'


PRIOR = FiscalCalendar(FISCAL['prior']['anchor'], FISCAL['prior']['weeks'])
CURRENT = FiscalCalendar(FISCAL['current']['anchor'], FISCAL['current']['weeks'])


def continuity_ok():
    """两个财年须首尾相接：本年期首 = 上年期首 + 上年周数*7。"""
    return CURRENT.anchor == PRIOR.anchor + timedelta(weeks=PRIOR.weeks)


def pair_baseline(day):
    """本年营业日 -> 上年同星期营业日。

    返回 (baseline_date, fiscal_week, weekday, label)。
    落在上年第 53 闰周（本年无同序号财周）时抛 FISCAL_LEAP。
    """
    located = CURRENT.locate(day)
    if located is None:
        raise DataError('FISCAL_SPAN', f'{day} 超出本财年范围')
    week, weekday, _ = located
    if week > PRIOR.weeks:
        raise DataError('FISCAL_LEAP', f'{day} 对应上年闰周，无同星期基准')
    baseline = PRIOR.day_at(week, weekday)
    return baseline, week, weekday, CURRENT.label(week, weekday)
