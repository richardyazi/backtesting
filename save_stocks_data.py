import re,os
import pandas as pd
import traceback
from pathlib import Path
from jqdata import *
import datetime
# 股票信息
stocks_zone = {
    '核心股': ['601888','002594'],
    '特高压':[
        '601179','600406','600312','300831','002028','000400'
    ],
    '灶基熔盐反应堆':[
        '601985','601727','600875','600170','600010','300402','002255','000932'
    ],
    '虚拟电厂':[
        '688717', '603421', '600406', '301162', '300882', '300880', '300682', '300286', '300068', 
        '300001', '002929', '000682'],
    '存储':[
        "688627","688525","688449","688072","688008","603986","600667","600584","301308","301099",
        "300672","300475","002409","002371","001309","000021"],
    '新疆振兴':[
        '601121', '600888', '600425', '600256', '600089', '300603', '002941', '002532', '002457', '002307', 
        '002202', '000933'],
    '可控核聚变':[
        '688776', '688122', '605123', '603308', '603015', '601985', '601727', '601611', '601609', '601212', 
        '601011', '600973', '600875', '600869', '600501', '600468', '600363', '600105', '300963','003816', 
        '002735', '002639', '002611', '002438', '002366', '002318', '002130', '000969', '000881', '000777', 
        '000543'],
    '电力':  [
        '688717', '688599', '688516', '688349', '688223', '603806', '603556', '601985', '601877', '601615', 
        '601012', '600905', '600900', '600795', '600509', '600438', '600406', '600312', '600089', '600011', 
        '301162', '300682', '300274', '002531', '002487', '002459', '002202', '002028', '001289', '001269', 
        '000400'],
    '源网荷储': ['601012', '600023', '300490', '300471', '300118', '002531', '002145', '002060'],
    '储能': [
        '688676', '688663', '688567', '688411', '688390', '688348', '688248', '688063', '688032', '605117',
        '603105', '603063', '603050', '601877', '601868', '601798', '601766', '601727', '601669', '601369', 
        '600995', '600875', '600522', '600517', '600348', '600312', '600173', '600157', '600152', '600089', 
        '301327', '301282', '300982', '300890', '300827', '300763', '300750', '300745', '300735', '300693', 
        '300530', '300438', '300274', '300124', '300118', '300091', '300068', '300066', '300014', '002866', 
        '002608', '002600', '002580', '002534', '002518', '002469', '002430', '002407'],
    '电力出海':  [
        '688676', '603556', '601868', '601669', '601567', '600406', '600089', '300274', '002922',
        '002270', '002028'],
    '断电器':['601877', '601567', '601179', '600885', '600312', '300001', '000400'],
    '游戏': ['603444', '300459', '300002', '002624', '002602', '002558', '002555'],
    '军工': [
        '600893', '600760', '000768', '600038', '600316',  # 航空装备
        '002025', '300395', '600118', '002414',           # 导弹与航天
        '002179', '002049', '600562', '600990',           # 信息化与电子装备
        '601989', '600150',                               # 船舶与海洋工程
        '300699', '688122', '600456', '600862', '000733', '603267', '688385', # 材料与元器件
        '688568', '300581', '688297', '601606', '600879', '600764', '600685', # 其他细分领域
        '302132', '001270', '601698', '688552', '000519', '600435', '002389', # 航天、无人机、兵器等
        '002625', '000738', '002465', '600967'            # 核心系统及其他
    ]
}
pool_stocks = []
for k,v in stocks_zone.items():
    for code in v:
        pool_stocks.append(code)

# 股票代码转换成聚宽股票代码
pool_stocks = list(set(pool_stocks))
pool_stocks = [normalize_code(i)  for i in pool_stocks]

# 获取所有股票基本信息
all_securities = get_all_securities(['stock'])


# 循环遍历所有股票，
# 首先检查本地是否存在对应缓存文件。
#   若不存在缓存，则从股票上市日期到最新交易日全量下载该股票数据；
#   若存在缓存，则比较本地文件最后一行日期与最新交易日，仅下载增量数据。
# 下载完成后，将新旧数据合并、去重并按日期排序，最后更新本地缓存文件。
# 所有下载数据需按股票上市年份分类存储在不同目录中。具体API调用方法请参考@聚宽函数API.md文档。


def calc_stock_data_path(stock_code, stock_info, root_dir='./data/stocks'):
    """根据股票上市年份计算存储路径"""
    year = stock_info['start_date'].year
    file_path = Path(root_dir) / str(year) / f"{stock_code}.csv"
    return file_path

def get_latest_trading_date():
    """获取最新交易日
    
    基于聚宽API的get_trade_days函数实现，准确获取最新交易日数据
    """
    # 使用get_trade_days获取最近2个交易日，返回最近的一个
    trade_days = get_trade_days(count=2)
    if len(trade_days):
        return trade_days[-1].strftime('%Y-%m-%d')
    else:
        # 如果没有交易日数据，返回昨天作为备用
        today = datetime.datetime.now()
        latest_date = today - datetime.timedelta(days=1)
        return latest_date.strftime('%Y-%m-%d')

def download_stock_data_with_cache(stock_code, stock_info, root_dir='./data/stocks'):
    """带缓存的股票数据下载"""
    
    # 计算存储路径
    save_path = calc_stock_data_path(stock_code, stock_info, root_dir)
    
    # 确保目录存在
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 获取最新交易日
    latest_date = get_latest_trading_date()
    
    # 检查缓存文件是否存在
    if save_path.exists():
        print(f"检测到缓存文件: {save_path}")
        
            # 读取现有缓存数据
            try:
                cached_df = pd.read_csv(save_path,index_col=0,parse_dates=True)
                # 确保日期列是datetime类型并设置为索引
                if cached_df.index.name != 'date':
                    cached_df = cached_df.reset_index()
                    if 'date' in cached_df.columns:
                        cached_df['date'] = pd.to_datetime(cached_df['date'])
                        cached_df.set_index('date', inplace=True)
                    else:
                        # 如果第一列是日期，使用第一列
                        date_col = cached_df.columns[0]
                        cached_df[date_col] = pd.to_datetime(cached_df[date_col])
                        cached_df.set_index(date_col, inplace=True)
                cached_df.index.name = None
            
            # 获取缓存数据的最新日期
            if not cached_df.empty:
                last_cached_date = cached_df.index[-1].strftime('%Y-%m-%d')
                
                # 如果缓存数据已是最新，则跳过下载
                if last_cached_date >= latest_date:
                    print(f"{stock_code} 数据已是最新，跳过下载")
                    return cached_df
                
                # 增量下载：从缓存最后日期到最新交易日
                print(f"增量下载 {stock_code}: {last_cached_date} ~ {latest_date}")
                new_data = get_price(
                    stock_code,
                    start_date=last_cached_date,
                    end_date=latest_date,
                    fields=['open', 'close', 'high', 'low', 'volume'],
                    skip_paused=True
                )
                
                # 合并数据（去重并排序）
                combined_df = pd.concat([cached_df, new_data])
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                combined_df = combined_df.sort_index()
                
                # 保存更新后的数据
                combined_df.to_csv(save_path)
                print(f"{stock_code} 数据更新完成，共 {len(combined_df)} 行")
                return combined_df
                
        except Exception as e:
            print(f"读取缓存文件失败: {e}，重新全量下载")
    
    # 全量下载：从上市日期到最新交易日
    print(f"全量下载 {stock_code}: {stock_info['start_date']} ~ {latest_date}")
    
    df = get_price(
        stock_code,
        start_date=stock_info['start_date'],
        end_date=latest_date,
        fields=['open', 'close', 'high', 'low', 'volume'],
        skip_paused=True
    )
    
    # 保存数据
    if not df.empty:
        df.to_parquet(save_path)
        print(f"{stock_code} 全量下载完成，共 {len(df)} 行")
    else:
        print(f"警告: {stock_code} 没有获取到数据")
    
    return df

# 主循环：遍历所有股票并下载数据
print("开始股票数据下载任务...")
print(f"总共需要处理的股票数量: {len(pool_stocks)}")

for i, stock_code in enumerate(pool_stocks, 1):
    print(f"\n[{i}/{len(pool_stocks)}] 处理股票: {stock_code}")
    
    # 检查股票是否在all_securities中
    if stock_code not in all_securities.index:
        print(f"跳过 {stock_code}: 不在股票列表中")
        continue
    
    # 获取股票信息
    stock_info = all_securities.loc[stock_code]
    
    # 检查股票是否已退市
    if stock_info['end_date'] < datetime.datetime.now().date():
        print(f"跳过 {stock_code}: 已退市")
        continue
    
    try:
        # 下载数据（带缓存机制）
        df = download_stock_data_with_cache(stock_code, stock_info)
        
        # 添加一些统计信息
        if not df.empty:
            latest_date = df.index[-1].strftime('%Y-%m-%d')
            print(f"{stock_code} 数据范围: {df.index[0].strftime('%Y-%m-%d')} ~ {latest_date}")
        
    except Exception as e:
        print(f"处理 {stock_code} 时出错: {e}")
        print("堆栈信息:")
        traceback.print_exc()
        continue

print("\n股票数据下载任务完成！")