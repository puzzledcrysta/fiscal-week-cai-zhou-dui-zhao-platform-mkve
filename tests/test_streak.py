from app.modules.domain.streak import detect
from app.modules.domain.calendar import CURRENT


def w(day, weak=True, store='S1'):
    d = CURRENT.day_at(*day)
    return {'key': store, 'day': d.isoformat(), 'baseline_day': d.isoformat(),
            'fiscal_week': day[0], 'weekday': day[1], 'comparable': True, 'weak': weak,
            'status': '营业', 'code': 'WEAK' if weak else 'OK'}


def gap(day, store='S1', status='停业'):
    d = CURRENT.day_at(*day)
    return {'key': store, 'day': d.isoformat(), 'baseline_day': d.isoformat(),
            'fiscal_week': day[0], 'weekday': day[1], 'comparable': False, 'weak': False,
            'status': status, 'code': 'NOT_OPEN'}


def test_trigger_on_second_weak_day():
    # 第一天就能在第 2 个走弱日收到信号；触发日 = 第二个走弱日。
    intervals = detect('S1', [w((1, 0)), w((1, 1))])
    assert len(intervals) == 1
    iv = intervals[0]
    assert iv['trigger_day'] == CURRENT.day_at(1, 1).isoformat()
    assert iv['start_day'] == CURRENT.day_at(1, 0).isoformat()


def test_single_weak_day_does_not_trigger():
    assert detect('S1', [w((1, 0)), w((1, 1), weak=False)]) == []


def test_single_gap_does_not_break_interval():
    # 走弱-停业-走弱：单日停业不切断，区间连续且在第 2 个走弱日触发。
    intervals = detect('S1', [w((1, 0)), gap((1, 1)), w((1, 2))])
    assert len(intervals) == 1
    iv = intervals[0]
    assert iv['gap_days'] == [CURRENT.day_at(1, 1).isoformat()]
    assert iv['weak_days'] == [CURRENT.day_at(1, 0).isoformat(), CURRENT.day_at(1, 2).isoformat()]


def test_missing_report_behaves_like_gap():
    intervals = detect('S1', [w((1, 0)), gap((1, 1), status='缺报'), w((1, 2))])
    assert len(intervals) == 1 and intervals[0]['gap_days']


def test_two_consecutive_gaps_break_interval():
    intervals = detect('S1', [w((1, 0)), w((1, 1)), gap((1, 2)), gap((1, 3)), w((1, 4))])
    # 前两个走弱日已触发成一个区间；连续两个不可比日断开，第 5 日只有 1 个走弱日不触发。
    assert len(intervals) == 1
    iv = intervals[0]
    assert iv['end_day'] == CURRENT.day_at(1, 1).isoformat()  # 止于最后走弱日，不含致断缺口
    assert iv['gap_days'] == [CURRENT.day_at(1, 2).isoformat(), CURRENT.day_at(1, 3).isoformat()]


def test_strong_day_breaks_interval():
    intervals = detect('S1', [w((1, 0)), w((1, 1), weak=False), w((1, 2))])
    assert intervals == []


def test_cross_week_interval_is_not_split():
    # W01 周日走弱、W02 周一走弱：跨财周仍是同一连续区间，不拆成两段报警。
    intervals = detect('S1', [w((1, 6)), w((2, 0))])
    assert len(intervals) == 1
    iv = intervals[0]
    assert iv['fiscal_weeks'] == [1, 2]
    assert iv['start_day'] == CURRENT.day_at(1, 6).isoformat()
    assert iv['end_day'] == CURRENT.day_at(2, 0).isoformat()
