"""
股票数据缓存脚本配置文件
适用于聚宽Jupyter Notebook环境
"""

# 股票代码池配置（Python字典变量）
pool_stocks = {
    '核心股': ['601888', '002594'],
    '特高压': [
        '601179', '600406', '600312', '300831', '002028', '000400'
    ],
    # 可以继续添加其他板块
}

# 聚宽API参数配置
jq_params = {
    'start_date': '2010-01-01',
    'end_date': '2025-12-04',
    'frequency': 'daily',  # daily/weekly/monthly/minute
    'fields': ['open', 'high', 'low', 'close', 'volume'],
    'fq': 'pre',  # 复权方式: pre/post/None
    'skip_paused': False,
    'fill_paused': True,
    'panel': False  # 建议设置为False，返回DataFrame格式
}

# 缓存配置
cache_config = {
    'update_strategy': 'incremental',  # incremental/full
    'auto_update': True,
    'check_interval': 'daily',  # daily/weekly/monthly
    'max_retry': 3,
    'retry_delay': 5  # 重试延迟秒数
}

# 存储配置
storage_config = {
    'base_path': './data',
    'format': 'parquet',  # parquet/csv
    'compression': 'snappy',
    'by_listing_year': True  # 按上市年份分目录
}

# 日志配置
log_config = {
    'level': 'INFO',  # DEBUG/INFO/WARNING/ERROR
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': './stock_cache.log'
}