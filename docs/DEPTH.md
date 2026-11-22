# 门店低销预警台业务与测试登记

- 规模：中型
- 使用者：区域值班经理
- 核心规则：上年同财周同星期营业日对照；2 个走弱营业日触发；单日停业/缺报不断区间；跨财周不拆段；确认后不可倒退、不可新增。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 日销送报 | 检查编码、列宽、来源行 | `POST /api/intake` | `app/modules/intake/{reader,service}.py` | `tests/test_intake.py` |
| M2 字段归一 | 归一修订、状态、业务键与偏移时间 | `POST /api/contract` | `app/modules/contract/{schema,service}.py` | `tests/test_contract.py` |
| M3 版本冲突 | 按门店+营业日归并版本，定位冲突与替代 | `POST /api/quality` | `app/modules/quality/{versions,service}.py` | `tests/test_quality.py`、`test_revision_failover.py` |
| M4 走弱检测 | 单日对照、阈值判定与连续区间扫描 | `POST /api/domain` | `app/modules/domain/{calendar,rule,streak,service}.py` | `tests/test_calendar.py`、`test_domain.py`、`test_streak.py` |
| M5 低销预警 | 区间、触发日、依据与门店主数据 | `GET /api/signals`、`POST /api/reconcile` | `app/modules/signals/ledger.py`、`app/modules/reconcile/*` | `tests/test_reconcile.py`、`test_immutability.py` |
| M6 预警批次 | 内容寻址批次、复算、确认锁定 | `POST /api/runs`、`/confirm`、`/replay` | `app/modules/runs/*` | `tests/test_runs.py` |
| M7 值班确认 | 乐观锁意见登记与证据导出 | `POST /api/review/{run_id}`、`/api/export` | `app/modules/review/*` | `tests/test_review.py` |

## 陷阱登记

| TRAP | 现象 | 样例 | 处理位置 | 测试 |
|---|---|---|---|---|
| TRAP-01 | GB18030 来源文件 | legacy.csv | `intake/reader.py` | `test_intake.py::test_gb18030` |
| TRAP-02 | BOM 前缀 | shift.csv | `intake/reader.py` | `test_intake.py::test_bom` |
| TRAP-03 | 备注引号内换行 | shift.csv | `intake/service.py` | `test_intake.py::test_multiline` |
| TRAP-04 | 分段重复表头 | shift.csv | `intake/service.py` | `test_intake.py::test_repeated_header` |
| TRAP-05 | 列数不足 | shift.csv | `intake/service.py` | `test_quality.py::test_reason_counts` |
| TRAP-07 | 缺测哨兵 | shift.csv | `contract/schema.py` | `test_contract.py::test_missing_required` |
| TRAP-08 | 前导零门店号 | shift.csv | `contract/service.py` | `test_contract.py::test_leading_zero_preserved` |
| TRAP-11 | 偏移时刻 UTC 归一 | shift.csv | `domain/values.py` | `test_contract.py::test_offsets_normalized_to_utc` |
| TRAP-14 | 同版业务字段冲突 | shift.csv | `quality/versions.py` | `test_quality.py::test_conflicting_latest_revision_quarantined` |
| TRAP-16 | 末行引号截断 | truncated.csv | `intake/reader.py` | `test_intake.py::test_truncated_rejected` |
| TRAP-17 | 旧版列名映射 | legacy.csv | `contract/schema.py` | `test_contract.py::test_legacy_aliased` |
| TRAP-18 | 空/空白/仅表头 | 测试构造 | `intake/service.py` | `test_intake.py::test_empty_states` |
| TRAP-23 | 营业日越出财年 | 测试构造 | `domain/calendar.py` | `test_calendar.py::test_outside_current_year_rejected` |
| TRAP-26 | 陈旧确认版本拒绝 | 测试构造 | `review/decisions.py` | `test_review.py::test_stale_version_rejected` |
| TRAP-107 | 上年第 53 闰周无配对 | 日历常量 | `domain/calendar.py` | `test_calendar.py::test_leap_week_has_no_current_counterpart` |

## 低销专项不变量（test_immutability.py）

1. 批次确认后重跑，预警全部保持 `confirmed`，字段不回退。
2. 确认幂等：重复确认只产生一条确认水位。
3. 已确认门店出现新起始日区间 → 拒收并记 `BLOCKED_LOCKED_STORE`。
4. 迟到补报使未确认区间缩短 → 保留原 `end_day`，追加 `LATE_DATA`。
5. 新走弱日延伸区间 → 只更新 `end_day`，`start_day`/`trigger_day` 固定。
6. 预警依据可查触发日、基准日、走弱日、缺口日与财周。

## 对账

输入 = 计入对照营业日 + 隔离坏行 + 版本替换（suppressed）+ 空白行 + 重复表头。`pipeline.execute` 断言该闭合恒等式，坏行全部带原因留痕、不丢失。数值以 `Decimal` 定点计算，对外按字符串传输。
