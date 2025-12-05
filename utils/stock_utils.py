"""
股票工具函数模块
包含股票代码转换、格式验证等功能
"""

import re
from typing import List, Dict, Set


def convert_to_jq_code(stock_code: str) -> str:
    """
    将普通股票代码转换为聚宽可用的格式
    
    Args:
        stock_code: 原始股票代码，如'601888', '002594'
        
    Returns:
        str: 聚宽格式的股票代码，如'601888.XSHG', '002594.XSHE'
    """
    if not isinstance(stock_code, str):
        raise ValueError(f"股票代码必须是字符串类型: {stock_code}")
    
    # 去除空格和特殊字符
    code = stock_code.strip()
    
    # 如果已经是聚宽格式，直接返回
    if '.' in code:
        return code
    
    # 根据代码前缀判断交易所
    if code.startswith(('60', '900')):
        # 沪市股票
        return f"{code}.XSHG"
    elif code.startswith(('00', '30', '200')):
        # 深市股票
        return f"{code}.XSHE"
    elif code.startswith('688'):
        # 科创板
        return f"{code}.XSHG"
    elif code.startswith('8'):
        # 北交所
        return f"{code}.BJ"
    else:
        raise ValueError(f"无法识别的股票代码格式: {code}")


def convert_stock_pool(pool_stocks: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    转换整个股票代码池
    
    Args:
        pool_stocks: 原始股票代码池字典
        
    Returns:
        Dict[str, List[str]]: 转换后的股票代码池
    """
    converted_pool = {}
    
    for category, stock_list in pool_stocks.items():
        converted_stocks = []
        for stock_code in stock_list:
            try:
                jq_code = convert_to_jq_code(stock_code)
                converted_stocks.append(jq_code)
            except ValueError as e:
                print(f"警告: 跳过无效股票代码 {stock_code}: {e}")
                continue
        
        converted_pool[category] = converted_stocks
    
    return converted_pool


def get_all_stocks_from_pool(pool_stocks: Dict[str, List[str]]) -> Set[str]:
    """
    从股票池中获取所有股票代码（去重）
    
    Args:
        pool_stocks: 股票代码池字典
        
    Returns:
        Set[str]: 所有股票代码的集合
    """
    all_stocks = set()
    
    for stock_list in pool_stocks.values():
        for stock_code in stock_list:
            try:
                jq_code = convert_to_jq_code(stock_code)
                all_stocks.add(jq_code)
            except ValueError as e:
                print(f"警告: 跳过无效股票代码 {stock_code}: {e}")
                continue
    
    return all_stocks


def validate_stock_code(stock_code: str) -> bool:
    """
    验证股票代码格式是否正确
    
    Args:
        stock_code: 股票代码
        
    Returns:
        bool: 是否有效
    """
    try:
        convert_to_jq_code(stock_code)
        return True
    except ValueError:
        return False


def get_listing_year(stock_code: str) -> int:
    """
    获取股票上市年份（需要调用聚宽API）
    
    Args:
        stock_code: 聚宽格式的股票代码
        
    Returns:
        int: 上市年份
    """
    try:
        # 导入聚宽函数
        from jqdata import get_security_info
        
        info = get_security_info(stock_code)
        if info and info.start_date:
            return info.start_date.year
        else:
            # 如果无法获取上市年份，返回默认年份
            return 2000
    except Exception as e:
        print(f"无法获取股票 {stock_code} 的上市年份: {e}")
        return 2000


if __name__ == "__main__":
    # 测试代码
    test_codes = ['601888', '002594', '000001', '600000', '300831']
    
    for code in test_codes:
        jq_code = convert_to_jq_code(code)
        print(f"{code} -> {jq_code}")
    
    # 测试股票池转换
    test_pool = {
        '测试板块': ['601888', '002594', '000001']
    }
    
    converted = convert_stock_pool(test_pool)
    print(f"转换后的股票池: {converted}")