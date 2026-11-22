import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / 'sample_data'
DB = Path(os.getenv('WORKBENCH_DB', str(ROOT/'state/ledger.sqlite3')))
TITLE = '财周对照台'
SLUG = 'fiscal-week'
KEY = '门店财周单'
FIELDS = ('上年期首', '上年周数', '本年期首', '本年周数', '上年日销售', '本年日销售')
ROLE = '连锁零售经营分析员'
UNIT = '元'
RULE_VERSION = 'fiscal-week-1.0'
SIGNATURE = '配对周差额'
TABS = {'intake': '日销送报', 'contract': '财年字段', 'quality': '日历冲突', 'domain': '可比财周', 'reconcile': '经营清单', 'runs': '财周批次', 'review': '月结复核'}
