# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Add current directory to path for imports
backend_dir = Path.cwd()
sys.path.insert(0, str(backend_dir))

# Manual dependency list from pyproject.toml since poetry export fails
hidden_imports = [
    # Core FastAPI dependencies
    'fastapi',
    'uvicorn',
    'uvicorn.main',
    'uvicorn.server',
    'uvicorn.config',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
    'starlette',
    'starlette.applications',
    'starlette.routing',
    'starlette.middleware',
    'starlette.responses',
    
    # Data processing
    'numpy',
    'pandas',
    'pandas._libs.tslibs.base',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.timestamps',
    'pandas._libs.tslibs.nattype',
    
    # HTTP clients
    'httpx',
    'httpx._client',
    'httpx._config',
    'httpx._exceptions',
    'requests',
    'requests.packages',
    'requests.packages.urllib3',
    
    # Vector database and embeddings
    'chromadb',
    'chromadb.api',
    'chromadb.config',
    'sentence_transformers',
    'sentence_transformers.models',
    
    # Trading APIs
    'ib_insync',
    'yfinance',
    'python_binance',
    'ccxt',
    
    # WebSockets and async
    'websockets',
    'websocket_client',
    'aiofiles',
    'aiohttp',
    'aiohttp.web',
    'asyncio_mqtt',
    
    # Machine learning
    'scikit_learn',
    'sklearn',
    'sklearn.preprocessing',
    'sklearn.model_selection',
    'sklearn.metrics',
    
    # Technical analysis
    'ta',
    'ta.trend',
    'ta.momentum',
    'ta.volatility',
    'ta.volume',
    
    # Configuration and environment
    'python_dotenv',
    'dotenv',
    'pydantic_settings',
    'pydantic',
    'pydantic.dataclasses',
    'pydantic.json_schema',
    
    # Image processing
    'PIL',
    'PIL.Image',
    'pillow',
    
    # Web forms and templates
    'python_multipart',
    'jinja2',
    'jinja2.runtime',
    
    # Scheduling
    'schedule',
    'apscheduler',
    'apscheduler.schedulers',
    'apscheduler.schedulers.background',
    
    # Authentication and security
    'python_jose',
    'jose',
    'cryptography',
    'passlib',
    'bcrypt',
    
    # Database
    'pymongo',
    'motor',
    'redis',
    
    # Task queue
    'celery',
    'celery.app',
    
    # Web scraping
    'playwright',
    'playwright.sync_api',
    'playwright.async_api',
    'beautifulsoup4',
    'bs4',
    'selenium',
    'selenium.webdriver',
    
    # Communication
    'python_telegram_bot',
    'telegram',
    
    # Local modules - all Gremlin Trade Core components
    'Gremlin_Trade_Core',
    'Gremlin_Trade_Core.agent_coordinator',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent.base_memory_agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Service_Agents',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Service_Agents.market_data_service',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Service_Agents.simple_market_service',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Tool_Control_Agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Tool_Control_Agent.portfolio_tracker',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Tool_Control_Agent.tool_control_agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.signal_generator',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Strategy_Agent.strategy_agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Rule_Set_Agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Rule_Set_Agent.rule_set_agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Rule_Set_Agent.rules_engine',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Timing_Agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Timing_Agent.market_timing',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Financial_Agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Financial_Agent.tax_estimator',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Agents_out',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Run_Time_Agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Run_Time_Agent.stock_scraper',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Run_Time_Agent.runtime_agent',
    'Gremlin_Trade_Core.Gremlin_Trader_Tools.Trade_Agents',
    'Gremlin_Trade_Core.Gremlin_Trader_Strategies',
    'Gremlin_Trade_Memory',
]

# Data files to include
datas = [
    ('Gremlin_Trade_Core', 'Gremlin_Trade_Core'),
    ('Gremlin_Trade_Memory', 'Gremlin_Trade_Memory'),
]

# Binary files to include (if any)
binaries = []

a = Analysis(
    ['main.py'],
    pathex=[str(backend_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude GUI frameworks we don't need
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        # Exclude test frameworks
        'pytest',
        'nose',
        'unittest2',
        # Exclude development tools
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='gremlin-trader-main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)