REASONS = {
    'EMPTY': '文件无内容', 'BLANK_FILE': '文件只有空白', 'HEADER_ONLY': '文件只有表头',
    'ENCODING': '无法识别编码', 'CSV': '表格语法错误', 'HEADER': '表头无效',
    'WIDTH': '列数与表头不一致', 'CONTRACT': '列契约无法应用', 'REQUIRED': '主键或业务字段缺失',
    'TIMESTAMP': '时间需包含偏移量', 'NUMBER': '数字无法归一', 'RANGE': '数字越界',
    'EXACT_DUP': '同版本重复传输', 'SUPERSEDED': '已被更新版本代替',
    'REV_CONFLICT': '最高版本证据有冲突', 'BUSINESS': '业务规则无法判定',
    'RUN_UNKNOWN': '没有此批次', 'DEMO_UNKNOWN': '没有此样例', 'STALE': '确认版本已过期',
    'REVIEW_NOTE': '退回或有未确认预警时须填写处理意见', 'REVIEW_DECISION': '确认结论无效',
    'DATE': '日期格式无效', 'REV_BLOCKED': '较新来源尚未采信',
    # 低销域
    'FISCAL_SPAN': '营业日超出财年范围', 'FISCAL_LEAP': '上年闰周无同星期基准',
    'DAY_CONFLICT': '同日营业记录互相冲突', 'STATUS_INVALID': '营业状态取值无效',
    'BASE_MISSING': '上年同星期基准缺失', 'NOT_OPEN': '当日门店未营业，不参与对照',
    'NO_BASELINE': '缺少同星期营业基准', 'SIGNAL_UNKNOWN': '没有此预警区间',
    'ALERT_LOCKED': '已确认预警不可变更', 'ALERT_REGRESSED': '新版本不得倒退既有预警',
    'BOOK_CONFLICT': '门店清单含重复门店', 'BOOK_KEY': '门店清单缺少门店编号',
}
