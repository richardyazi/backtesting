"""
股票数据缓存脚本安装配置
"""

from setuptools import setup, find_packages

setup(
    name="stock-cache",
    version="1.0.0",
    description="智能股票数据缓存脚本，专为聚宽研究环境设计",
    author="Stock Cache Team",
    author_email="stock-cache@example.com",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "pyarrow>=5.0.0",
        "pyyaml>=5.4.0",
    ],
    extras_require={
        "dev": [
            "ipython>=7.0.0",
            "jupyter>=1.0.0",
            "matplotlib>=3.3.0",
            "seaborn>=0.11.0",
        ],
        "test": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "stock-cache=stock_cache:main",
        ],
    },
)