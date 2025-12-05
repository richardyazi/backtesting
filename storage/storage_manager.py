"""
存储管理模块
负责数据文件的存储、读取和格式转换
"""

import os
import pandas as pd
from typing import Dict, Optional
import pyarrow as pa
import pyarrow.parquet as pq


class StorageManager:
    """存储管理器"""
    
    def __init__(self, base_path: str = "./data", format: str = "parquet", 
                 compression: str = "snappy"):
        """
        初始化存储管理器
        
        Args:
            base_path: 存储根目录
            format: 存储格式（parquet/csv）
            compression: 压缩方式
        """
        self.base_path = base_path
        self.format = format.lower()
        self.compression = compression
        
        # 确保基础目录存在
        os.makedirs(base_path, exist_ok=True)
    
    def get_file_path(self, stock_code: str, year_dir: Optional[str] = None) -> str:
        """
        获取文件存储路径
        
        Args:
            stock_code: 股票代码
            year_dir: 年份目录（可选）
            
        Returns:
            str: 文件路径
        """
        if year_dir:
            file_dir = os.path.join(self.base_path, str(year_dir))
            os.makedirs(file_dir, exist_ok=True)
        else:
            file_dir = self.base_path
        
        # 生成文件名（去除交易所后缀中的点）
        file_name = stock_code.replace('.', '_') + f'.{self.format}'
        return os.path.join(file_dir, file_name)
    
    def save_data(self, data: pd.DataFrame, stock_code: str, 
                  year_dir: Optional[str] = None) -> str:
        """
        保存数据到文件
        
        Args:
            data: 股票数据
            stock_code: 股票代码
            year_dir: 年份目录（可选）
            
        Returns:
            str: 保存的文件路径
        """
        if data is None or data.empty:
            raise ValueError("数据为空，无法保存")
        
        file_path = self.get_file_path(stock_code, year_dir)
        
        try:
            if self.format == "parquet":
                # 保存为Parquet格式
                table = pa.Table.from_pandas(data)
                pq.write_table(table, file_path, compression=self.compression)
                
            elif self.format == "csv":
                # 保存为CSV格式
                data.to_csv(file_path, index=True, encoding='utf-8-sig')
                
            else:
                raise ValueError(f"不支持的存储格式: {self.format}")
            
            print(f"数据已保存到: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"保存数据失败 {stock_code}: {e}")
            raise
    
    def load_data(self, stock_code: str, year_dir: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        从文件加载数据
        
        Args:
            stock_code: 股票代码
            year_dir: 年份目录（可选）
            
        Returns:
            Optional[pd.DataFrame]: 股票数据，如果文件不存在返回None
        """
        file_path = self.get_file_path(stock_code, year_dir)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            if self.format == "parquet":
                # 从Parquet文件加载
                table = pq.read_table(file_path)
                data = table.to_pandas()
                
            elif self.format == "csv":
                # 从CSV文件加载
                data = pd.read_csv(file_path, index_col=0, parse_dates=True)
                
            else:
                raise ValueError(f"不支持的存储格式: {self.format}")
            
            print(f"数据已从 {file_path} 加载")
            return data
            
        except Exception as e:
            print(f"加载数据失败 {stock_code}: {e}")
            return None
    
    def file_exists(self, stock_code: str, year_dir: Optional[str] = None) -> bool:
        """
        检查文件是否存在
        
        Args:
            stock_code: 股票代码
            year_dir: 年份目录（可选）
            
        Returns:
            bool: 文件是否存在
        """
        file_path = self.get_file_path(stock_code, year_dir)
        return os.path.exists(file_path)
    
    def get_file_size(self, stock_code: str, year_dir: Optional[str] = None) -> int:
        """
        获取文件大小（字节）
        
        Args:
            stock_code: 股票代码
            year_dir: 年份目录（可选）
            
        Returns:
            int: 文件大小，如果文件不存在返回0
        """
        file_path = self.get_file_path(stock_code, year_dir)
        
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        else:
            return 0
    
    def delete_data(self, stock_code: str, year_dir: Optional[str] = None) -> bool:
        """
        删除数据文件
        
        Args:
            stock_code: 股票代码
            year_dir: 年份目录（可选）
            
        Returns:
            bool: 是否删除成功
        """
        file_path = self.get_file_path(stock_code, year_dir)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"已删除文件: {file_path}")
                return True
            except Exception as e:
                print(f"删除文件失败 {file_path}: {e}")
                return False
        else:
            print(f"文件不存在: {file_path}")
            return False
    
    def convert_format(self, stock_code: str, new_format: str, 
                      year_dir: Optional[str] = None) -> bool:
        """
        转换文件格式
        
        Args:
            stock_code: 股票代码
            new_format: 新格式（parquet/csv）
            year_dir: 年份目录（可选）
            
        Returns:
            bool: 是否转换成功
        """
        # 加载原数据
        data = self.load_data(stock_code, year_dir)
        if data is None:
            return False
        
        # 保存原格式
        old_format = self.format
        
        try:
            # 临时更改格式并保存
            self.format = new_format
            new_file_path = self.save_data(data, stock_code, year_dir)
            
            # 恢复原格式
            self.format = old_format
            
            print(f"格式转换成功: {old_format} -> {new_format}")
            return True
            
        except Exception as e:
            # 恢复原格式
            self.format = old_format
            print(f"格式转换失败: {e}")
            return False
    
    def list_files(self, year_dir: Optional[str] = None) -> list:
        """
        列出存储的文件
        
        Args:
            year_dir: 年份目录（可选）
            
        Returns:
            list: 文件列表
        """
        if year_dir:
            target_dir = os.path.join(self.base_path, str(year_dir))
        else:
            target_dir = self.base_path
        
        if not os.path.exists(target_dir):
            return []
        
        files = []
        for file_name in os.listdir(target_dir):
            if file_name.endswith(f'.{self.format}'):
                files.append(file_name)
        
        return sorted(files)


def main():
    """测试存储管理器"""
    # 创建测试数据
    test_data = pd.DataFrame({
        'open': [100, 101, 102],
        'close': [101, 102, 103],
        'volume': [1000000, 1200000, 1100000]
    }, index=pd.date_range('2024-01-01', periods=3))
    
    storage_mgr = StorageManager(base_path="./test_data", format="parquet")
    
    # 测试保存和加载
    file_path = storage_mgr.save_data(test_data, "601888_XSHG", "2024")
    print(f"文件保存路径: {file_path}")
    
    loaded_data = storage_mgr.load_data("601888_XSHG", "2024")
    if loaded_data is not None:
        print(f"加载的数据形状: {loaded_data.shape}")
    
    # 测试文件存在性检查
    exists = storage_mgr.file_exists("601888_XSHG", "2024")
    print(f"文件存在: {exists}")
    
    # 清理测试文件
    storage_mgr.delete_data("601888_XSHG", "2024")


if __name__ == "__main__":
    main()