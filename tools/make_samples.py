"""生成低销预警样例 CSV（工具脚本，不是运行时依赖）。

对照规则：本年营业日 d 的基准 = 上年同财周同星期营业日的销售额；
本年值 < 基准 * 0.80 记为走弱；2 个走弱营业日触发，中间允许 1 个不可比日。
运行：python3 tools/make_samples.py
"""
import csv
from datetime import date, timedelta
from pathlib import Path

CURRENT_ANCHOR = date(2025, 1, 6)     # 本财年期首（周一）
PRIOR_ANCHOR = date(2024, 1, 1)       # 上年财年期首（周一，53 周）
OUT = Path(__file__).resolve().parents[1] / 'sample_data'

HEADER = ['门店编号', '修订号', '提交时间', '营业日期', '营业状态',
          '本年日销售', '上年同星期日销售', '原始备注']


def current_day(week, weekday):  # week 从 1 开始，weekday 0=周一
    return CURRENT_ANCHOR + timedelta(days=(week - 1) * 7 + weekday)


def prior_day(week, weekday):
    return PRIOR_ANCHOR + timedelta(days=(week - 1) * 7 + weekday)


def iso(d):
    return d.isoformat()


def row(store, rev, stamp, day, status, amount, base, note=''):
    return [store, rev, stamp, iso(day), status,
            '' if amount is None else amount, '' if base is None else base, note]


def weak(day, base=1000):      # 低于八成：1000 -> 700
    return row(day[0], 1, '2026-11-18T09:30:00+08:00', day[1], '营业', 700, base, day[2])


def ok(day, base=1000):        # 达标：900 >= 800
    return row(day[0], 1, '2026-11-18T09:30:00+08:00', day[1], '营业', 900, base, day[2])


def d(store, week, weekday, note):
    return store, current_day(week, weekday), note


def main():
    rows = []
    # 门店 00101：W01 周一走弱、周二停业（单日不可比不断区间）、周三再走弱 -> 周三触发，区间不断。
    s = '00101'
    rows += [
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 0), '营业', 700, 1000, '周一走弱'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 1), '停业', None, 1000, '盘点停业一天'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 2), '营业', 720, 1000, '周三仍走弱，触发'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 3), '营业', 710, 1000, '持续走弱'),
    ]
    # 门店 00102：仅周一走弱，周二达标 -> 只有 1 个走弱日，不触发。
    s = '00102'
    rows += [
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 0), '营业', 600, 1000, '单日波动'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 1), '营业', 950, 1000, '次日恢复'),
    ]
    # 门店 00103：周一走弱、周二缺报（应报未报，不断区间但留痕）、周三走弱 -> 触发。
    s = '00103'
    rows += [
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 0), '营业', 650, 1000, '周一走弱'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 1), '缺报', None, 1000, '系统未上报'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 2), '营业', 640, 1000, '周三走弱，触发'),
    ]
    # 门店 00104：连续两个不可比日断开；前两个走弱日已触发，断后新走弱需重新累计。
    s = '00104'
    rows += [
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 0), '营业', 700, 1000, '走弱1'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 1), '营业', 700, 1000, '走弱2，触发'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 2), '停业', None, 1000, '停业'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 3), '缺报', None, 1000, '连续第二日不可比，断开'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 4), '营业', 700, 1000, '新区间第1个走弱，不触发'),
    ]
    # 门店 00105：跨财周不拆段——W01 周日走弱、W02 周一走弱，同一连续区间，标记 cross_week。
    s = '00105'
    rows += [
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 6), '营业', 700, 1000, '本周日走弱'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(2, 0), '营业', 690, 1000, '次周一走弱，触发且跨周'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(2, 1), '营业', 705, 1000, '继续走弱'),
    ]
    # 门店 00106：版本归并——旧版走弱被修订 2 的达标值替代，不触发。
    s = '00106'
    rows += [
        row(s, 1, '2026-11-18T08:00:00+08:00', current_day(1, 0), '营业', 500, 1000, '旧版误报'),
        row(s, 2, '2026-11-18T10:00:00+08:00', current_day(1, 0), '营业', 900, 1000, '修订后达标'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 1), '营业', 920, 1000, '达标'),
    ]
    # 门店 00107：同版字段冲突（修订 2 两条不一致）-> 隔离 REV_CONFLICT，旧版不得接替。
    s = '00107'
    rows += [
        row(s, 1, '2026-11-18T08:00:00+08:00', current_day(1, 0), '营业', 700, 1000, '旧版'),
        row(s, 2, '2026-11-18T10:00:00+08:00', current_day(1, 0), '营业', 700, 1000, '新版A'),
        row(s, 2, '2026-11-18T10:05:00+08:00', current_day(1, 0), '营业', 900, 1000, '新版B冲突'),
    ]
    # 门店 00108：缺基准（上年同星期为空）-> 不可比 NO_BASELINE，不算走弱。
    s = '00108'
    rows += [
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 0), '营业', 100, None, '新店无上年基准'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 1), '营业', 700, 1000, '次日走弱'),
        row(s, 1, '2026-11-18T09:30:00+08:00', current_day(1, 2), '营业', 700, 1000, '再次走弱，触发'),
    ]
    # 坏行与闭合用例：必填缺失、状态非法、列数不足、空白行与重复表头。
    rows += [
        ['00109', '1', '2026-11-18T09:30:00+08:00', iso(current_day(1, 0)), '营业', '', '1000', '缺本年销售额'],
        ['00110', '1', '2026-11-18T09:30:00+08:00', iso(current_day(1, 0)), '装修', '700', '1000', '非法状态'],
        ['残行', '2'],
        [],
        HEADER,
    ]
    with (OUT / 'shift.csv').open('w', encoding='utf-8-sig', newline='') as fp:
        writer = csv.writer(fp)
        writer.writerow(HEADER)
        writer.writerows(rows)
        # 引号内换行备注（TRAP-03 回归）
        fp.write('00111,1,2026-11-18T09:30:00+08:00,' + iso(current_day(1, 0)) +
                 ',营业,900,1000,"排班补登\n区域备注"\n')

    master = [
        ['门店编号', '门店名称', '区域'],
        ['00101', '中山广场店', '华东一区'],
        ['00102', '滨江路店', '华东一区'],
        ['00103', '城西银泰店', '华东二区'],
        ['00104', '大学城店', '华东二区'],
        ['00105', '火车站店', '华北一区'],
        ['00106', '老街口店', '华北一区'],
        ['00107', '会展中心店', '华北二区'],
        ['00108', '新区旗舰店', '华北二区'],
    ]
    with (OUT / 'external.csv').open('w', encoding='utf-8', newline='') as fp:
        csv.writer(fp).writerows(master)

    # 历史格式：GB18030 + 旧版表头别名。
    legacy_header = ['门店编码', '版本', '更新时刻', '营业日期', '营业状态', '当日销售额', '基准销售额', '备注']
    legacy = [legacy_header,
              ['00013', '1', '2026-11-18T09:30:00+08:00', iso(current_day(1, 0)), '营业', '700', '1000', '历史系统导出']]
    with (OUT / 'legacy.csv').open('w', encoding='gb18030', newline='') as fp:
        csv.writer(fp).writerows(legacy)

    # 末行引号截断（TRAP-16 回归）。
    with (OUT / 'truncated.csv').open('w', encoding='utf-8', newline='') as fp:
        fp.write('门店编号,备注\n00001,"未写完的引号')

    # 固定算例（cases.csv）供领域单测逐例断言。
    with (OUT / 'cases.csv').open('w', encoding='utf-8', newline='') as fp:
        writer = csv.writer(fp)
        writer.writerow(['case', 'expected', 'evidence', '营业日期', '营业状态', '本年日销售', '上年同星期日销售'])
        writer.writerow(['weak_day', 'WEAK', 'threshold=800.00', iso(current_day(1, 0)), '营业', '700', '1000'])
        writer.writerow(['ok_day', 'OK', 'threshold=800.00', iso(current_day(1, 0)), '营业', '800', '1000'])
        writer.writerow(['closed_day', 'NOT_OPEN', '计划停业', iso(current_day(1, 1)), '停业', '', '1000'])
        writer.writerow(['missing_day', 'BASE_MISSING', '当日缺报', iso(current_day(1, 1)), '缺报', '', '1000'])
        writer.writerow(['no_baseline', 'NO_BASELINE', '缺少基准', iso(current_day(1, 0)), '营业', '100', ''])
    print('samples written to', OUT)


if __name__ == '__main__':
    main()
