"""走弱区间检测：同星期基准下，容忍单日停业/缺报的连续区间扫描。

规则（对应业务要求）：
- 只按自然日先后扫描同一门店的已采信记录；缺报/停业是「不可比日」。
- 走弱营业日累计到 TRIGGER_DAYS 即触发，第一天满足就出信号（触发日 = 第 2 个走弱日）。
- 连续 GAP_TOLERANCE 个不可比日不断开区间（单日停业/缺报不算持续下滑、也不机械切断）；
  连续第 2 个不可比日断开；任何一个「达标营业日」立即断开。
- 区间不按财周切断：跨财周下滑保持一个可干预连续区间，月结归因时再标注财周。
- end_day 始终是最后一个走弱营业日；致断的不可比日只在 gap_days 留痕，不延长区间。
"""
from app.settings import TRIGGER_DAYS, GAP_TOLERANCE


def _new_interval(store, first_weak):
    return {
        'key': store, 'start_day': first_weak['day'], 'trigger_day': None,
        'end_day': first_weak['day'], 'weak_days': [], 'gap_days': [],
        'baseline_day': first_weak['baseline_day'], 'fiscal_weeks': [],
    }


def detect(store, days):
    """days: 同一门店、按自然日升序的 classify_day 结论列表。返回触发的区间列表。"""
    intervals, current, gap_run = [], None, 0
    for day in days:
        if day['comparable']:
            if day['weak']:
                if current is None:
                    current = _new_interval(store, day)
                current['weak_days'].append(day['day'])
                current['end_day'] = day['day']
                if current['trigger_day'] is None and len(current['weak_days']) >= TRIGGER_DAYS:
                    current['trigger_day'] = day['day']
                if day['fiscal_week'] not in current['fiscal_weeks']:
                    current['fiscal_weeks'].append(day['fiscal_week'])
                gap_run = 0
            else:
                if current is not None:
                    intervals.append(current)
                    current = None
                gap_run = 0
        else:
            if current is None:
                continue
            gap_run += 1
            current['gap_days'].append(day['day'])
            if gap_run > GAP_TOLERANCE:
                intervals.append(current)
                current, gap_run = None, 0
    if current is not None:
        intervals.append(current)
    return [item for item in intervals if item['trigger_day'] is not None]
