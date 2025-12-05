"""
股票数据缓存主程序
集成所有模块，提供统一的数据缓存接口
"""

import os
import pandas as pd
from typing import Dict, List, Set, Optional
from datetime import datetime

from config import pool_stocks, jq_params, cache_config, storage_config
from utils.stock_utils import convert_stock_pool, get_all_stocks_from_pool, get_listing_year
from utils.logger import get_logger, info, warning, error, exception
from utils.data_validator import DataValidator
from cache.cache_manager import CacheManager
from data_fetcher.jq_fetcher import JQFetcher
from storage.storage_manager import StorageManager


class StockCache:
    """股票数据缓存主类"""
    
    def __init__(self, custom_config: Optional[Dict] = None):
        """
        初始化股票数据缓存器
        
        Args:
            custom_config: 自定义配置（可选）
        """
        # 合并配置
        self.config = self._merge_configs(custom_config)
        
        # 初始化日志
        self.logger = get_logger(
            log_dir="./logs",
            log_level=self.config.get('log', {}).get('level', 'INFO')
        )
        
        # 初始化数据验证器
        self.validator = DataValidator(
            min_data_points=self.config.get('validation', {}).get('min_data_points', 10),
            max_null_ratio=self.config.get('validation', {}).get('max_null_ratio', 0.1)
        )
        
        # 初始化各模块
        self.cache_mgr = CacheManager(
            base_path=self.config['storage']['base_path'],
            cache_meta_file="cache_meta.json"
        )
        
        self.fetcher = JQFetcher(
            max_retry=self.config['cache']['max_retry'],
            retry_delay=self.config['cache']['retry_delay']
        )
        
        self.storage_mgr = StorageManager(
            base_path=self.config['storage']['base_path'],
            format=self.config['storage']['format'],
            compression=self.config['storage']['compression']
        )
        
        # 转换股票代码池
        self.pool_stocks = convert_stock_pool(self.config['pool_stocks'])
        self.all_stocks = get_all_stocks_from_pool(self.pool_stocks)
        
        info(f"股票缓存器初始化完成，共 {len(self.all_stocks)} 只股票")
    
    def _merge_configs(self, custom_config: Optional[Dict]) -> Dict:
        """合并默认配置和自定义配置"""
        # 默认配置
        default_config = {
            'pool_stocks': pool_stocks,
            'jq_params': jq_params,
            'cache': cache_config,
            'storage': storage_config
        }
        
        if custom_config is None:
            return default_config
        
        # 深度合并配置
        merged_config = default_config.copy()
        
        for key, value in custom_config.items():
            if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
                merged_config[key].update(value)
            else:
                merged_config[key] = value
        
        return merged_config
    
    def download_all_stocks(self, force_full: bool = False) -> Dict[str, bool]:
        """
        下载所有股票数据
        
        Args:
            force_full: 是否强制全量下载
            
        Returns:
            Dict[str, bool]: 每只股票的下载结果
        """
        results = {}
        
        print(f"开始下载 {len(self.all_stocks)} 只股票数据...")
        
        for i, stock_code in enumerate(self.all_stocks, 1):
            print(f"\n[{i}/{len(self.all_stocks)}] 处理股票: {stock_code}")
            
            try:
                success = self.download_single_stock(stock_code, force_full)
                results[stock_code] = success
                
                if success:
                    print(f"✓ {stock_code} 下载成功")
                else:
                    print(f"✗ {stock_code} 下载失败")
                
            except Exception as e:
                print(f"✗ {stock_code} 处理异常: {e}")
                results[stock_code] = False
        
        # 统计结果
        success_count = sum(results.values())
        print(f"\n下载完成: {success_count}/{len(self.all_stocks)} 成功")
        
        return results
    
    def download_single_stock(self, stock_code: str, force_full: bool = False) -> bool:
        """
        下载单只股票数据
        
        Args:
            stock_code: 股票代码
            force_full: 是否强制全量下载
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取配置参数
            start_date = self.config['jq_params']['start_date']
            end_date = self.config['jq_params']['end_date']
            
            # 判断下载模式
            if force_full:
                download_mode = 'full'
            else:
                download_mode = self.cache_mgr.determine_download_mode(
                    stock_code, start_date, end_date
                )
            
            if download_mode == 'none':
                print(f"股票 {stock_code} 数据已最新，无需下载")
                return True
            
            # 获取数据
            if download_mode == 'full':
                # 全量下载
                print(f"全量下载 {stock_code} 数据")
                data = self._fetch_stock_data(stock_code, start_date, end_date)
                
            elif download_mode == 'incremental':
                # 增量下载
                inc_start, inc_end = self.cache_mgr.get_incremental_dates(
                    stock_code, start_date, end_date
                )
                print(f"增量下载 {stock_code} 数据 ({inc_start} 到 {inc_end})")
                
                # 获取增量数据
                new_data = self._fetch_stock_data(stock_code, inc_start, inc_end)
                
                # 加载旧数据并合并
                old_data = self._load_cached_data(stock_code)
                data = self.cache_mgr.merge_data(old_data, new_data)
                
                # 更新日期范围为完整范围
                start_date = min(start_date, self.cache_mgr.get_cache_data_range(stock_code)[0])
                end_date = max(end_date, self.cache_mgr.get_cache_data_range(stock_code)[1])
            
            else:
                raise ValueError(f"未知的下载模式: {download_mode}")
            
            if data is None or data.empty:
                print(f"股票 {stock_code} 无有效数据")
                return False
            
            # 保存数据
            year_dir = str(get_listing_year(stock_code)) if self.config['storage']['by_listing_year'] else None
            file_path = self.storage_mgr.save_data(data, stock_code, year_dir)
            
            # 更新缓存元数据
            self.cache_mgr.update_cache_meta(
                stock_code, file_path, start_date, end_date, len(data)
            )
            
            return True
            
        except Exception as e:
            print(f"下载股票 {stock_code} 失败: {e}")
            return False
    
    def _fetch_stock_data(self, stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取股票数据"""
        try:
            # 验证日期范围
            if not self.fetcher.validate_date_range(start_date, end_date):
                return None
            
            # 获取数据
            data = self.fetcher.get_single_stock_data(
                stock_code, start_date, end_date, **self.config['jq_params']
            )
            
            if data is not None and not data.empty:
                print(f"获取到 {len(data)} 条数据")
            else:
                print("获取到空数据")
            
            return data
            
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None
    
    def _load_cached_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """加载缓存数据"""
        cache_info = self.cache_mgr.get_stock_cache_info(stock_code)
        
        if cache_info and 'file_path' in cache_info:
            file_path = cache_info['file_path']
            if os.path.exists(file_path):
                return self.storage_mgr.load_data(stock_code)
        
        return None
    
    def get_stock_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取股票数据（优先从缓存加载）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Optional[pd.DataFrame]: 股票数据
        """
        # 检查缓存
        if self.cache_mgr.check_cache_exists(stock_code):
            print(f"从缓存加载 {stock_code} 数据")
            return self._load_cached_data(stock_code)
        
        # 缓存不存在，重新下载
        print(f"缓存不存在，下载 {stock_code} 数据")
        success = self.download_single_stock(stock_code)
        
        if success:
            return self._load_cached_data(stock_code)
        else:
            return None
    
    def get_stocks_by_category(self, category: str) -> List[str]:
        """
        获取指定分类的股票列表
        
        Args:
            category: 分类名称
            
        Returns:
            List[str]: 股票代码列表
        """
        return self.pool_stocks.get(category, [])
    
    def list_categories(self) -> List[str]:
        """
        获取所有分类
        
        Returns:
            List[str]: 分类名称列表
        """
        return list(self.pool_stocks.keys())
    
    def update_cache(self, categories: Optional[List[str]] = None) -> Dict[str, bool]:
        """
        更新指定分类的缓存
        
        Args:
            categories: 分类列表，为None时更新所有分类
            
        Returns:
            Dict[str, bool]: 每只股票的更新结果
        """
        if categories is None:
            # 更新所有股票
            return self.download_all_stocks()
        
        # 更新指定分类的股票
        target_stocks = set()
        for category in categories:
            if category in self.pool_stocks:
                target_stocks.update(self.pool_stocks[category])
        
        results = {}
        for stock_code in target_stocks:
            results[stock_code] = self.download_single_stock(stock_code)
        
        return results


def main():
    """主函数"""
    # 创建缓存器
    cache = StockCache()
    
    # 显示可用分类
    categories = cache.list_categories()
    print(f"可用分类: {categories}")
    
    # 下载所有股票数据
    print("\n开始下载股票数据...")
    results = cache.download_all_stocks()
    
    # 测试获取单只股票数据
    test_stock = '601888.XSHG'
    print(f"\n测试获取股票数据: {test_stock}")
    data = cache.get_stock_data(test_stock)
    
    if data is not None:
        print(f"数据形状: {data.shape}")
        print(f"数据样例:\n{data.head()}")
    else:
        print("获取数据失败")


if __name__ == "__main__":
    main()