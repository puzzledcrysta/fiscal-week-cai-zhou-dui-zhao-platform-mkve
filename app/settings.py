import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / 'sample_data'
DB = Path(os.getenv('WORKBENCH_DB', str(ROOT/'state/ledger.sqlite3')))

TITLE = '门店低销预警台'
SLUG = 'low-sales'
KEY = '门店编号'
ROLE = '区域值班经理'
UNIT = '元'
RULE_VERSION = 'low-sales-1.0'
SIGNATURE = '低销预警'

# 四四五财年：期首为周一，季度前两期各四周、第三期五周（4+4+5=13 周/季）。
# 两个连续财年的期首；上年财年可能含第 53 闰周，闰周不参与同星期对照。
FISCAL = {
    'prior': {'anchor': '2024-01-01', 'weeks': 53},
    'current': {'anchor': '2025-01-06', 'weeks': 52},
}

# 触发规则参数（计入规则版本指纹，调整即产生新版本批次）。
WEAK_RATIO = '0.80'          # 本年同星期营业日 < 基准 * 0.80 记为走弱
TRIGGER_DAYS = 2             # 累计 2 个走弱营业日即首次触发（第一天收到信号）
GAP_TOLERANCE = 1            # 连续 1 个不可比日（停业/缺报）不断区间，第 2 个连续不可比日断开
MAX_REVISION = 10 ** 9

FIELDS = ('营业日期', '本年日销售', '上年同星期日销售')
TABS = {
    'intake': '日销送报',
    'contract': '字段归一',
    'quality': '版本冲突',
    'domain': '走弱检测',
    'signals': '低销预警',
    'runs': '预警批次',
    'review': '值班确认',
}
