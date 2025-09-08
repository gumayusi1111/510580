#!/usr/bin/env python3
"""
ETF数据管理系统启动脚本
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etf_manager import main

if __name__ == "__main__":
    main()