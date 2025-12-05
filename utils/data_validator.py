"""
数据质量验证模块
验证获取的股票数据质量
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from utils.logger import info, warning, error


class DataValidator:
    """数据质量验证器"""
    
    def __init__(self, min_data_points: int = 10, max_null_ratio: float = 0.1):
        """
        初始化数据验证器
        
        Args:
            min_data_points: 最小数据点数
            max_null_ratio: 最大空值比例
        """
        self.min_data_points = min_data_points
        self.max_null_ratio = max_null_ratio
    
    def validate_stock_data(self, data: pd.DataFrame, stock_code: str) -> Tuple[bool, Dict]:
        """
        验证股票数据质量
        
        Args:
            data: 股票数据DataFrame
            stock_code: 股票代码
            
        Returns:
            Tuple[bool, Dict]: (是否有效, 验证结果详情)
        """
        if data is None or data.empty:
            return False, {"error": "数据为空"}
        
        validation_results = {
            "stock_code": stock_code,
            "data_points": len(data),
            "date_range": {
                "start": data.index.min().strftime('%Y-%m-%d') if len(data) > 0 else None,
                "end": data.index.max().strftime('%Y-%m-%d') if len(data) > 0 else None
            },
            "checks": {},
            "warnings": [],
            "errors": []
        }
        
        # 检查数据点数
        if len(data) < self.min_data_points:
            validation_results["errors"].append(f"数据点数不足: {len(data)} < {self.min_data_points}")
        else:
            validation_results["checks"]["data_points"] = "PASS"
        
        # 检查空值
        null_ratio = self._check_null_values(data)
        validation_results["null_ratio"] = null_ratio
        
        if null_ratio > self.max_null_ratio:
            validation_results["errors"].append(f"空值比例过高: {null_ratio:.2%} > {self.max_null_ratio:.2%}")
        else:
            validation_results["checks"]["null_values"] = "PASS"
        
        # 检查数据完整性
        completeness = self._check_data_completeness(data)
        validation_results["data_completeness"] = completeness
        
        if completeness < 0.8:  # 80%完整性阈值
            validation_results["warnings"].append(f"数据完整性较低: {completeness:.2%}")
        else:
            validation_results["checks"]["completeness"] = "PASS"
        
        # 检查价格合理性
        price_issues = self._check_price_validity(data)
        if price_issues:
            validation_results["warnings"].extend(price_issues)
        else:
            validation_results["checks"]["price_validity"] = "PASS"
        
        # 检查日期连续性
        date_gaps = self._check_date_continuity(data)
        if date_gaps:
            validation_results["warnings"].extend(date_gaps)
        else:
            validation_results["checks"]["date_continuity"] = "PASS"
        
        # 总体验证结果
        is_valid = len(validation_results["errors"]) == 0
        validation_results["is_valid"] = is_valid
        
        # 记录验证结果
        if is_valid:
            info(f"股票 {stock_code} 数据验证通过: {len(data)} 条数据")
        else:
            error(f"股票 {stock_code} 数据验证失败: {validation_results['errors']}")
        
        return is_valid, validation_results
    
    def _check_null_values(self, data: pd.DataFrame) -> float:
        """检查空值比例"""
        if data.empty:
            return 1.0
        
        null_count = data.isnull().sum().sum()
        total_cells = data.shape[0] * data.shape[1]
        
        return null_count / total_cells if total_cells > 0 else 0
    
    def _check_data_completeness(self, data: pd.DataFrame) -> float:
        """检查数据完整性"""
        if data.empty:
            return 0.0
        
        # 检查关键字段的完整性
        key_fields = ['open', 'high', 'low', 'close', 'volume']
        available_fields = [field for field in key_fields if field in data.columns]
        
        if not available_fields:
            return 0.0
        
        # 计算每个字段的完整性
        completeness_scores = []
        for field in available_fields:
            field_completeness = 1 - data[field].isnull().sum() / len(data)
            completeness_scores.append(field_completeness)
        
        return sum(completeness_scores) / len(completeness_scores)
    
    def _check_price_validity(self, data: pd.DataFrame) -> List[str]:
        """检查价格合理性"""
        issues = []
        
        if 'open' in data.columns and 'close' in data.columns:
            # 检查价格是否为负
            negative_prices = data[(data['open'] <= 0) | (data['close'] <= 0)]
            if not negative_prices.empty:
                issues.append(f"发现 {len(negative_prices)} 条负价格记录")
            
            # 检查高低价关系
            invalid_high_low = data[
                (data['high'] < data['low']) | 
                (data['high'] < data['open']) | 
                (data['high'] < data['close'])
            ]
            if not invalid_high_low.empty:
                issues.append(f"发现 {len(invalid_high_low)} 条高价低于低价/开盘价/收盘价的记录")
        
        return issues
    
    def _check_date_continuity(self, data: pd.DataFrame) -> List[str]:
        """检查日期连续性"""
        if len(data) < 2:
            return []
        
        issues = []
        
        # 检查日期是否连续
        date_diff = pd.Series(data.index).diff().dt.days
        gaps = date_diff[date_diff > 1]  # 超过1天的间隔
        
        if len(gaps) > 0:
            max_gap = gaps.max()
            issues.append(f"发现日期不连续，最大间隔: {max_gap} 天")
        
        return issues
    
    def validate_batch_data(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        批量验证股票数据
        
        Args:
            data_dict: 股票代码到数据的映射
            
        Returns:
            Dict[str, Dict]: 每只股票的验证结果
        """
        results = {}
        
        for stock_code, data in data_dict.items():
            is_valid, validation_result = self.validate_stock_data(data, stock_code)
            results[stock_code] = validation_result
        
        # 统计整体验证结果
        valid_count = sum(1 for result in results.values() if result["is_valid"])
        total_count = len(results)
        
        info(f"批量验证完成: {valid_count}/{total_count} 只股票数据有效")
        
        return results