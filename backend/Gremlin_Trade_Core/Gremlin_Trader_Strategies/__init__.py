#!/usr/bin/env python3
"""
Gremlin Trader Strategies Package
Comprehensive trading strategies for penny stock detection and analysis
"""

from .recursive_scanner import run_recursive_strategy, get_strategy_config
from .penny_stock_strategy import scan_penny_stocks, get_penny_strategy_config
from .strategy_manager import (
    run_all_strategies, 
    get_performance_metrics, 
    update_weights, 
    run_backtest,
    strategy_manager
)

__all__ = [
    'run_recursive_strategy',
    'get_strategy_config', 
    'scan_penny_stocks',
    'get_penny_strategy_config',
    'run_all_strategies',
    'get_performance_metrics',
    'update_weights',
    'run_backtest',
    'strategy_manager'
]
