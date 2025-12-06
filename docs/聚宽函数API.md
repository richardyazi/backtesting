# get_price 函数文档

## 功能描述
`get_price` 用于获取历史数据，支持查询多个标的的多个数据字段，返回数据格式为 `DataFrame`。

## 函数签名
```python
get_price(
    security,
    start_date=None,
    end_date=None,
    frequency='daily',
    fields=None,
    skip_paused=False,
    fq='pre',
    count=None,
    panel=True,
    fill_paused=True
)
```

## 参数说明

### `security`
- **类型**: 一支股票代码或一个股票代码的列表。
- **描述**: 指定需要查询的股票代码或股票代码列表。

### `start_date` 与 `count`
- **二选一**: 不可同时使用。
- **`count`**: 返回的结果集的行数，表示获取 `end_date` 之前几个 `frequency` 的数据。
- **`start_date`**: 字符串或 `datetime.datetime`/`datetime.date` 对象，表示开始时间。
  - 如果 `count` 和 `start_date` 均未提供，则 `start_date` 默认为 `'2015-01-01'`。
  - **分钟数据**: 时间可精确到分钟，例如 `datetime.datetime(2015, 1, 1, 10, 0, 0)` 或 `'2015-01-01 10:00:00'`。
  - **天数据**: 传入的日内时间会被忽略。

### `end_date`
- **类型**: 同 `start_date`。
- **描述**: 结束时间，默认为 `'2015-12-31'`，包含此日期。
  - **分钟数据**: 如果 `end_date` 只有日期，则日内时间默认为 `00:00:00`，返回的数据不包括 `end_date` 这一天。

### `frequency`
- **类型**: 字符串。
- **描述**: 单位时间长度，支持 `'Xd'`、`'Xm'`、`'daily'`（等同于 `'1d'`）、`'minute'`（等同于 `'1m'`），其中 `X` 为正整数。
  - 当 `X > 1` 时，`fields` 仅支持 `['open', 'close', 'high', 'low', 'volume', 'money']`。
  - 默认值为 `'daily'`。

### `fields`
- **类型**: 字符串列表。
- **描述**: 选择要获取的行情数据字段。默认为 `None`（表示获取标准字段 `['open', 'close', 'high', 'low', 'volume', 'money']`）。
  - 支持 `SecurityUnitData` 的所有基本属性，包括 `['open', 'close', 'low', 'high', 'volume', 'money', 'factor', 'high_limit', 'low_limit', 'avg', 'pre_close', 'paused', 'open_interest']`。
  - `paused` 为 `1` 表示停牌。

### `skip_paused`
- **类型**: 布尔值。
- **描述**: 是否跳过不交易日期（包括停牌、未上市或退市后的日期）。
  - 默认为 `False`。
  - 当 `skip_paused=True` 时，获取多个标的时需设置 `panel=False`。

### `fq`
- **类型**: 字符串。
- **描述**: 复权选项（对股票/基金的价格字段、成交量字段及 `factor` 字段生效）。
  - `'pre'`: 前复权（默认）。
  - `None`: 不复权，返回实际价格。
  - `'post'`: 后复权。

### `panel`
- **类型**: 布尔值。
- **描述**: 在 `pandas 0.25` 版后，`Panel` 被移除。建议获取多标的数据时设置 `panel=False`，返回等效的 `DataFrame`。

### `fill_paused`
- **类型**: 布尔值。
- **描述**: 对于停牌股票的价格处理。
  - `True`: 使用 `pre_close` 价格填充（默认）。
  - `False`: 使用 `NAN` 填充停牌数据。

## 合成数据的逻辑
当 `frequency` 为 `X` 天或 `X` 分钟时，表示使用以 `X` 为长度的滑动窗口合并数据。

### 示例
- **9:33:00** 调用 `get_price`，`frequency='5min'`，表示使用上一交易日 `14:58`、`14:59`、`15:00` 及本交易日 `9:31`、`9:32` 这 5 根 1 分钟 K 线合成数据。
- **9:37:00** 调用 `get_price`，`frequency='5min'`，表示使用本交易日 `9:32`、`9:33`、`9:34`、`9:35`、`9:36` 这 5 根 1 分钟 K 线合成数据。

## 返回结果
根据 `security` 参数的不同，返回的数据结构也不同（默认 `panel=False`）。

### 单支股票
返回 `pandas.DataFrame` 对象：
- **行索引**: `datetime.datetime` 对象。
- **列索引**: 行情字段名称（如 `'open'`、`'close'`）。

**示例**:
```python
get_price('000300.XSHG')[:2]
```
**输出**:
```
            open    close     high      low       volume          money
2015-01-05  3566.09  3641.54  3669.04  3551.51  451198098.0  519849817448.0
2015-01-06  3608.43  3641.06  3683.23  3587.23  420962185.0  498529588258.0
```

### 多支股票
返回 `pandas.Panel` 对象（已废弃，建议使用 `panel=False`）：
- **索引**: 行情字段（`open`、`close` 等）。
- **每个 `DataFrame`**: 行索引为 `datetime.datetime` 对象，列索引为股票代码。

**示例**:
```python
get_price(['000300.XSHG', '000001.XSHE'])['open'][:2]
```
**输出**:
```
            000300.XSHG  000001.XSHE
2015-01-05      3566.09        13.21
2015-01-06      3608.43        13.09
```

## 使用示例

### 获取单支股票数据
```python
# 获取 000001.XSHE 的 2015 年按天数据
df = get_price('000001.XSHE')

# 获取 000001.XSHG 的 2015 年 01 月分钟数据，仅获取 open 和 close 字段
df = get_price('000001.XSHE', start_date='2015-01-01', end_date='2015-01-31 23:00:00', frequency='1m', fields=['open', 'close'])

# 获取 000001.XSHG 在 2015-01-31 前 2 个交易日的数据
df = get_price('000001.XSHE', count=2, end_date='2015-01-31', frequency='daily', fields=['open', 'close'])

# 获取 000001.XSHG 的 2015-12-01 14:00 至 2015-12-02 12:00 的分钟数据
df = get_price('000001.XSHE', start_date='2015-12-01 14:00:00', end_date='2015-12-02 12:00:00', frequency='1m')
```

### 获取多支股票数据
```python
# 获取中证 100 所有成分股的 2015 年天数据
panel = get_price(get_index_stocks('000903.XSHG'))

# 获取开盘价数据
df_open = panel['open']

# 获取交易量数据
df_volume = panel['volume']

# 获取平安银行的开盘价数据
df_open['000001.XSHE']
```


# get_security_info

## 功能描述
获取股票、基金、指数或期货的详细信息。

## 函数签名
```python
get_security_info(code, date=None)
```

## 参数说明

### `code` (str)
证券代码。

### `date` (datetime.date, 可选)
查询日期，默认为 `None`，仅支持股票。

## 返回值
返回一个对象，包含以下属性：

| 属性名 | 类型 | 描述 |
|--------|------|------|
| `display_name` | str | 中文名称 |
| `name` | str | 缩写简称 |
| `start_date` | datetime.date | 上市日期 |
| `end_date` | datetime.date | 退市日期（股票是最后一个交易日，不同于摘牌日期），如果没有退市则为 `2200-01-01` |
| `type` | str | 证券类型 |
| `parent` | str | 分级基金的母基金代码 |

### 证券类型 (`type`)
支持的类型包括：
- `stock`: 股票
- `fund`: 基金
- `index_futures`: 金融期货
- `futures`: 期货
- `etf`: ETF
- `bond_fund`: 债券基金
- `stock_fund`: 股票基金
- `QDII_fund`: QDII 基金
- `money_market_fund`: 货币基金
- `mixture_fund`: 混合基金
- `open_fund`: 场外基金

## 使用示例

```python
# 获取000001.XSHE的上市时间
start_date = get_security_info('000001.XSHE').start_date
print(start_date)
```


# normalize_code

## 功能描述
将其他形式的股票代码转换为聚宽可用的股票代码形式。

## 函数签名
```python
normalize_code(codes)
```

## 参数说明

### `codes`
- **类型**: 字符串、整数、列表或元组
- **描述**: 需要转换的股票代码，支持多种输入格式
  - 支持字符串格式：如 `'000001'`、`'SZ000001'`、`'000001SZ'`、`'000001.sz'`
  - 支持整数格式：如 `1`
  - 支持列表或元组：批量转换多个代码

## 适用范围
- A股市场股票代码
- 期货代码
- 场内基金代码

## 转换规则
- 将各种格式的股票代码统一转换为聚宽标准格式
- 对于A股股票，转换为 `XXXXXX.XSHE`（深交所）或 `XXXXXX.XSHG`（上交所）格式

## 返回值
- **单个代码**: 返回转换后的标准代码字符串
- **多个代码**: 返回包含所有转换后代码的列表

## 使用示例

```python
# 输入
codes = ('000001', 'SZ000001', '000001SZ', '000001.sz', '000001.XSHE')
result = normalize_code(codes)

# 输出
print(result)
# ['000001.XSHE', '000001.XSHE', '000001.XSHE', '000001.XSHE', '000001.XSHE']

# 单个代码转换
single_code = normalize_code('600000')
print(single_code)
# '600000.XSHG'

# 整数代码转换
int_code = normalize_code(1)
print(int_code)
# '000001.XSHE'
```

## 注意事项
- 仅支持A股、期货和场内基金代码的转换
- 对于不支持的代码类型，可能会返回错误或保持原样
- 建议在调用 `get_price` 等函数前使用此函数进行代码标准化


# get_all_securities

## 功能描述
获取平台支持的所有股票、基金、指数、期货、期权信息。

## 函数签名
```python
get_all_securities(types=[], date=None)
```

## 参数说明

### `types` (list)
- **描述**: 用来过滤 securities 的类型
- **可选值**: 
  - `'stock'`: 股票
  - `'fund'`: 基金
  - `'index'`: 指数
  - `'futures'`: 期货
  - `'options'`: 期权
  - `'etf'`: 场内ETF基金
  - `'lof'`: 上市型开放基金
  - `'fja'`: 场内分级A
  - `'fjb'`: 场内分级B
  - `'open_fund'`: 开放式基金
  - `'bond_fund'`: 债券基金
  - `'stock_fund'`: 股票型基金
  - `'QDII_fund'`: QDII基金
  - `'money_market_fund'`: 场外交易的货币基金
  - `'mixture_fund'`: 混合型基金
- **默认值**: 空列表，返回所有股票，不包括基金、指数和期货

### `date`
- **类型**: 字符串或 `datetime.datetime`/`datetime.date` 对象
- **描述**: 用于获取某日期还在上市的股票信息
- **默认值**: `None`，表示获取所有日期的股票信息
- **建议**: 使用时添加上指定日期

## 返回值
- **类型**: `pandas.DataFrame`
- **描述**: 包含所有标的详细信息的数据框

## 返回数据格式

| 字段名 | 类型 | 描述 |
|--------|------|------|
| `display_name` | str | 中文名称，只返回最新的 |
| `name` | str | 缩写简称 |
| `start_date` | datetime.date | 上市日期 |
| `end_date` | datetime.date | 退市日期（股票是最后一个交易日，不同于摘牌日期），如果没有退市则为 `2200-01-01` |
| `type` | str | 标的类型 |

## 使用示例

```python
# 获取所有股票信息
df = get_all_securities()
print(df[:2])
```

**输出示例**:
```
           display_name  name  start_date    end_date  type
000001.XSHE      平安银行  PAYH  1991-04-03  9999-01-01  stock
000002.XSHE       万 科Ａ   WKA  1991-01-29  9999-01-01  stock
```

```python
# 获取指定日期在市的股票
df = get_all_securities(date='2024-01-01')

# 获取股票和指数信息
df = get_all_securities(types=['stock', 'index'])

# 获取所有基金信息
df = get_all_securities(types=['fund', 'etf', 'lof'])
```

## 注意事项
- 判断是否 ST 股请使用 `get_extras` 函数
- 建议使用时指定 `date` 参数，避免获取过多历史数据
- 返回的数据量较大，建议根据实际需求进行过滤


# get_trade_days

## 功能描述
获取指定范围交易日，返回一个包含 `datetime.date` 对象的列表。

## 函数签名
```python
get_trade_days(start_date=None, end_date=None, count=None)
```

## 参数说明

### `start_date` 与 `count`
- **二选一**: 不可同时使用。
- **`start_date`**: 开始日期，字符串或 `datetime.date`/`datetime.datetime` 对象。
- **`count`**: 数量，必须大于 0。表示取 `end_date` 往前的 `count` 个交易日，包含 `end_date` 当天。

### `end_date`
- **类型**: 字符串或 `datetime.date`/`datetime.datetime` 对象
- **描述**: 结束日期，默认为 `datetime.date.today()`

## 返回值
- **类型**: 包含 `datetime.date` 对象的列表
- **描述**: 包含指定 `start_date` 和 `end_date` 的所有交易日，默认返回至 `datetime.date.today()` 的所有交易日

## 注意事项
- 最多只能获取到截至现实时间的当前年份的最后一天的交易日数据
- 需导入 jqdata 模块，即在策略或研究起始位置加入 `import jqdata`