"""
聚宽数据获取模块
封装聚宽API调用，实现数据获取功能
"""

import time
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class JQFetcher:
    """聚宽数据获取器"""
    
    def __init__(self, max_retry: int = 3, retry_delay: int = 5):
        """
        初始化数据获取器
        
        Args:
            max_retry: 最大重试次数
            retry_delay: 重试延迟秒数
        """
        self.max_retry = max_retry
        self.retry_delay = retry_delay
    
    def get_stock_data(self, stock_codes: List[str], start_date: str, end_date: str,
                      frequency: str = 'daily', fields: List[str] = None,
                      fq: str = 'pre', skip_paused: bool = False,
                      fill_paused: bool = True, panel: bool = False) -> pd.DataFrame:
        """
        获取股票历史数据
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            fields: 数据字段
            fq: 复权方式
            skip_paused: 是否跳过停牌
            fill_paused: 是否填充停牌数据
            panel: 是否返回Panel格式
            
        Returns:
            pd.DataFrame: 股票数据
        """
        for attempt in range(self.max_retry):
            try:
                # 导入聚宽API
                from jqdata import get_price
                
                # 设置默认字段
                if fields is None:
                    fields = ['open', 'high', 'low', 'close', 'volume']
                
                # 调用聚宽API
                data = get_price(
                    security=stock_codes,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    fields=fields,
                    skip_paused=skip_paused,
                    fq=fq,
                    fill_paused=fill_paused,
                    panel=panel
                )
                
                return data
                
            except Exception as e:
                print(f"第 {attempt + 1} 次获取数据失败: {e}")
                
                if attempt < self.max_retry - 1:
                    print(f"等待 {self.retry_delay} 秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print("达到最大重试次数，放弃获取数据")
                    raise
    
    def get_single_stock_data(self, stock_code: str, start_date: str, end_date: str,
                             **kwargs) -> pd.DataFrame:
        """
        获取单只股票数据
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
            
        Returns:
            pd.DataFrame: 股票数据
        """
        return self.get_stock_data([stock_code], start_date, end_date, **kwargs)
    
    def get_batch_data(self, stock_codes: List[str], start_date: str, end_date: str,
                      batch_size: int = 50, **kwargs) -> Dict[str, pd.DataFrame]:
        """
        批量获取股票数据（分批处理，避免内存溢出）
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            batch_size: 批次大小
            **kwargs: 其他参数
            
        Returns:
            Dict[str, pd.DataFrame]: 股票数据字典
        """
        results = {}
        
        for i in range(0, len(stock_codes), batch_size):
            batch_codes = stock_codes[i:i + batch_size]
            print(f"正在获取第 {i//batch_size + 1} 批数据，共 {len(batch_codes)} 只股票...")
            
            try:
                batch_data = self.get_stock_data(batch_codes, start_date, end_date, **kwargs)
                
                # 处理返回的数据格式
                if len(batch_codes) == 1:
                    # 单只股票返回DataFrame
                    results[batch_codes[0]] = batch_data
                else:
                    # 多只股票返回的格式处理
                    if isinstance(batch_data, dict):
                        # Panel格式（已废弃）
                        for field, df in batch_data.items():
                            for stock_code in batch_codes:
                                if stock_code in df.columns:
                                    if stock_code not in results:
                                        results[stock_code] = pd.DataFrame()
                                    results[stock_code][field] = df[stock_code]
                    else:
                        # DataFrame格式，需要处理多索引
                        if isinstance(batch_data.index, pd.MultiIndex):
                            # 多索引格式，按股票代码分组
                            for stock_code in batch_codes:
                                stock_data = batch_data.xs(stock_code, level=1)
                                results[stock_code] = stock_data
                        else:
                            # 单只股票的情况
                            if len(batch_codes) == 1:
                                results[batch_codes[0]] = batch_data
                            else:
                                print("警告: 无法解析多只股票的数据格式")
                
                # 批次间延迟，避免API限制
                time.sleep(1)
                
            except Exception as e:
                print(f"获取批次数据失败: {e}")
                # 记录失败但继续处理其他批次
                continue
        
        return results
    
    def get_stock_info(self, stock_code: str) -> Optional[object]:
        """
        获取股票基本信息
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Optional[object]: 股票信息对象
        """
        try:
            from jqdata import get_security_info
            return get_security_info(stock_code)
        except Exception as e:
            print(f"获取股票信息失败 {stock_code}: {e}")
            return None
    
    def validate_date_range(self, start_date: str, end_date: str) -> bool:
        """
        验证日期范围是否有效
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            bool: 是否有效
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_dt > end_dt:
                print("错误: 开始日期不能晚于结束日期")
                return False
            
            # 检查日期是否在合理范围内
            min_date = datetime(1990, 1, 1)
            max_date = datetime.now() + timedelta(days=365)
            
            if start_dt < min_date or end_dt > max_date:
                print("警告: 日期范围可能超出数据可用范围")
            
            return True
            
        except ValueError:
            print("错误: 日期格式不正确，请使用 YYYY-MM-DD 格式")
            return False


def main():
    """测试数据获取器"""
    fetcher = JQFetcher()
    
    # 测试日期验证
    valid = fetcher.validate_date_range('2024-01-01', '2024-12-31')
    print(f"日期验证结果: {valid}")
    
    # 测试单只股票数据获取（在聚宽环境中运行）
    try:
        data = fetcher.get_single_stock_data('601888.XSHG', '2024-01-01', '2024-01-10')
        print(f"数据形状: {data.shape}")
        if not data.empty:
            print(f"数据样例:\n{data.head()}")
    except Exception as e:
        print(f"数据获取测试失败: {e}")


if __name__ == "__main__":
    main()