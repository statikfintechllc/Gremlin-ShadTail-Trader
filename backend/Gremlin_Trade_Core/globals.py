#!/usr/bin/env python3
"""
Centralized imports and configuration for Gremlin ShadTail Trader
Handles all system-wide imports, configuration, logging, and shared utilities
"""

import os
import sys
import json
import logging
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import shutil
import asyncio
import uuid

# Core trading and data libraries
try:
    from ib_insync import IB, Stock, Contract, ScannerSubscription, MarketOrder, LimitOrder, StopOrder
except ImportError:
    print("Warning: ib_insync not available - IBKR functionality disabled")

# Vector and ML libraries
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    CHROMA_AVAILABLE = True
    ML_AVAILABLE = True
except ImportError:
    print("Warning: chromadb/sentence_transformers not available - using fallback")
    chromadb = None
    SentenceTransformer = None
    CHROMA_AVAILABLE = False
    ML_AVAILABLE = False

# System paths and configuration
BASE_DIR = Path(__file__).parent.parent.parent.parent  # Root of Gremlin-ShadTail-Trader
BACKEND_DIR = BASE_DIR / "backend"
CONFIG_DIR = BACKEND_DIR / "Gremlin_Trade_Core" / "config"
MEMORY_DIR = BACKEND_DIR / "Gremlin_Trade_Memory"
VECTOR_STORE_DIR = MEMORY_DIR / "vector_store"
LOGS_DIR = CONFIG_DIR / "Gremlin_Trade_Logs"
STRATEGIES_DIR = BACKEND_DIR / "Gremlin_Trade_Core" / "Gremlin_Trader_Strategies"

# Ensure directories exist
for directory in [CONFIG_DIR, MEMORY_DIR, VECTOR_STORE_DIR, LOGS_DIR, STRATEGIES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Global configuration dictionary
CFG = {}
MEM = {}
DATA_DIR = str(VECTOR_STORE_DIR)

# Database paths - Unified ChromaDB configuration
METADATA_DB_PATH = VECTOR_STORE_DIR / "metadata.db" 
CHROMA_DIR = VECTOR_STORE_DIR / "chroma"  # Directory for ChromaDB persistence
CHROMA_DB_PATH = CHROMA_DIR / "chroma.sqlite3"  # Main ChromaDB file

# Global logging configuration
def setup_module_logger(module_group: str, module_name: str) -> logging.Logger:
    """Setup standardized logging for all modules"""
    logger = logging.getLogger(f"{module_group}.{module_name}")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_file = LOGS_DIR / f"{module_group}_{module_name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Main system logger
logger = setup_module_logger("system", "globals")

def load_configuration():
    """Load all configuration files into global CFG dictionary"""
    global CFG, MEM
    
    try:
        # Load memory configuration
        memory_config_path = CONFIG_DIR / "Gremlin_Trade_Config" / "memory.json"
        if memory_config_path.exists():
            with open(memory_config_path, 'r') as f:
                content = f.read().strip()
                if content:
                    MEM = json.loads(content)
                else:
                    MEM = get_default_memory_config()
        else:
            MEM = get_default_memory_config()
        
        # Load trade agents configuration
        agents_config_path = CONFIG_DIR / "Gremlin_Trade_Config" / "trade_agents.config"
        if agents_config_path.exists():
            with open(agents_config_path, 'r') as f:
                content = f.read().strip()
                if content:
                    CFG['agents'] = json.loads(content)
                else:
                    CFG['agents'] = get_default_agents_config()
        else:
            CFG['agents'] = get_default_agents_config()
        
        # Load trade strategy configuration
        strategy_config_path = CONFIG_DIR / "Gremlin_Trade_Config" / "trade_strategy.config"
        if strategy_config_path.exists():
            with open(strategy_config_path, 'r') as f:
                content = f.read().strip()
                if content:
                    CFG['strategy'] = json.loads(content)
                else:
                    CFG['strategy'] = get_default_strategy_config()
        else:
            CFG['strategy'] = get_default_strategy_config()
        
        # Load FullSpec configuration (new)
        fullspec_config_path = CONFIG_DIR / "FullSpec.config"
        if fullspec_config_path.exists():
            with open(fullspec_config_path, 'r') as f:
                content = f.read().strip()
                if content:
                    CFG['full_spec'] = json.loads(content)
                else:
                    CFG['full_spec'] = get_default_fullspec_config()
        else:
            CFG['full_spec'] = get_default_fullspec_config()
        
        # Set combined config
        CFG['memory'] = MEM
        
        logger.info("Configuration loaded successfully")
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        CFG = get_default_system_config()
        MEM = get_default_memory_config()

def get_default_memory_config():
    """Default memory configuration"""
    return {
        "storage": {
            "vector_store_path": str(VECTOR_STORE_DIR),
            "metadata_db": str(METADATA_DB_PATH),
            "chroma_db": str(CHROMA_DB_PATH)
        },
        "embedding": {
            "model": "all-MiniLM-L6-v2",
            "dimension": 384,
            "batch_size": 32
        },
        "dashboard_selected_backend": "chromadb",
        "retention": {
            "max_embeddings": 10000,
            "cleanup_interval_hours": 24
        }
    }

def get_default_agents_config():
    """Default agents configuration"""
    return {
        "ibkr": {
            "host": "127.0.0.1",
            "port": 7497,
            "client_id": 1,
            "paper_trading": True,
            "username": "",
            "password": ""
        },
        "scanner": {
            "max_results": 50,
            "scan_interval": 300,
            "recursive_depth": 3,
            "timeframes": ["1min", "5min", "15min"],
            "min_volume": 1000000,
            "max_price": 10.0,
            "min_rotation": 2.0
        },
        "risk_management": {
            "max_risk_per_trade": 0.10,
            "stop_loss_pct": 0.15,
            "take_profit_levels": [0.05, 0.10, 0.25, 0.50, 1.00],
            "max_positions": 10
        }
    }

def get_default_strategy_config():
    """Default strategy configuration"""
    return {
        "scanner_criteria": {
            "price_under": 10.0,
            "float_under_mil": 25,
            "volume_over": 1000000,
            "rotation_over": 2.0,
            "up_percent_min": 5.0
        },
        "signal_filters": {
            "ema_cross": True,
            "vwap_break": True,
            "volume_spike": True,
            "spoof_detection": True
        },
        "recursive_scanning": {
            "enabled": True,
            "max_depth": 3,
            "timeout_seconds": 30
        }
    }

def get_default_system_config():
    """Default complete system configuration"""
    return {
        "memory": get_default_memory_config(),
        "agents": get_default_agents_config(),
        "strategy": get_default_strategy_config(),
        "full_spec": get_default_fullspec_config()
    }

def get_default_fullspec_config():
    """Default FullSpec configuration"""
    return {
        "api_keys": {
            "grok": {
                "api_key": "",
                "base_url": "https://api.x.ai/v1",
                "model": "grok-beta",
                "max_tokens": 4000
            },
            "ibkr": {
                "username": "",
                "password": "",
                "paper_username": "",
                "paper_password": ""
            }
        },
        "x_logins": {
            "primary": {
                "username": "",
                "password": "",
                "bearer_token": ""
            }
        },
        "ibkr_logins": {
            "paper": {
                "host": "127.0.0.1",
                "port": 7497,
                "client_id": 1
            },
            "real": {
                "host": "127.0.0.1",
                "port": 7496,
                "client_id": 2
            }
        },
        "other_logins": {
            "tailscale": {
                "auth_key": "",
                "hostname": "gremlin-trader"
            }
        },
        "system_config": {
            "debug_mode": False,
            "plugins": {
                "grok": {"enabled": True},
                "source_editor": {"enabled": True}
            }
        }
    }

def resolve_path(path_str: str) -> Path:
    """Resolve relative paths to absolute paths"""
    path = Path(path_str)
    if path.is_absolute():
        return path
    return BASE_DIR / path

# Database initialization
def init_metadata_db():
    """Initialize metadata database - delegated to embedder module"""
    try:
        # Let the embedder module handle database initialization with the latest schema
        # This prevents schema conflicts between globals and embedder
        logger.info("Metadata database initialization delegated to embedder module")
    except Exception as e:
        logger.error(f"Error during metadata database delegation: {e}")

# Vector embedding functions
def embed_text(text: str) -> np.ndarray:
    """Embed text using sentence transformer"""
    try:
        if ML_AVAILABLE:
            model = SentenceTransformer(MEM.get("embedding", {}).get("model", "all-MiniLM-L6-v2"))
            embedding = model.encode(text)
            return embedding
        else:
            # Fallback to dummy embedding
            dimension = MEM.get("embedding", {}).get("dimension", 384)
            return np.random.rand(dimension).astype(np.float32)
    except Exception as e:
        logger.error(f"Error embedding text: {e}")
        dimension = MEM.get("embedding", {}).get("dimension", 384)
        return np.zeros(dimension, dtype=np.float32)

def package_embedding(text: str, vector: np.ndarray, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Package embedding with metadata"""
    embedding_id = str(uuid.uuid4())
    embedding = {
        "id": embedding_id,
        "text": text,
        "vector": vector.tolist() if hasattr(vector, 'tolist') else list(vector),
        "meta": {
            **meta,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "id": embedding_id
        }
    }
    return embedding

# Trading utility functions
def get_live_penny_stocks() -> List[Dict[str, Any]]:
    """Get live penny stock data - now uses working simple market service"""
    try:
        # Import here to avoid circular imports
        import asyncio
        from Gremlin_Trade_Core.simple_market_service import get_live_penny_stocks_real
        
        # Get real data asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            real_data = loop.run_until_complete(get_live_penny_stocks_real(limit=50))
            return real_data
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error getting penny stocks, falling back to sample data: {e}")
        # Fallback to sample data if real data fails
        return [
            {
                "symbol": "GPRO",
                "price": 2.15,
                "volume": 1500000,
                "rotation": 2.3,
                "up_pct": 12.5,
                "ema": {"5": 2.10, "20": 2.05},
                "vwap": 2.12,
                "rsi": 65.0,
                "error": "Service unavailable - showing fallback"
            }
        ]

def apply_signal_rules(stock: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Apply signal generation rules to stock data"""
    try:
        strategy_config = CFG.get("strategy", {}).get("scanner_criteria", {})
        
        # Basic criteria checks
        if stock["price"] > strategy_config.get("price_under", 10.0):
            return None
        
        if stock["volume"] < strategy_config.get("volume_over", 1000000):
            return None
        
        if stock.get("rotation", 0) < strategy_config.get("rotation_over", 2.0):
            return None
        
        # Generate signals based on criteria
        signals = []
        
        # EMA cross signal
        ema_5 = stock.get("ema", {}).get("5", 0)
        ema_20 = stock.get("ema", {}).get("20", 0)
        if ema_5 > ema_20:
            signals.append("ema_cross_bullish")
        
        # VWAP break signal
        if stock["price"] > stock.get("vwap", 0):
            signals.append("vwap_break")
        
        # Volume spike signal
        if stock["volume"] > 2000000:  # High volume threshold
            signals.append("volume_spike")
        
        if signals:
            return {
                "signal": signals,
                "confidence": len(signals) / 3.0,  # Normalized confidence
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error applying signal rules: {e}")
        return None

# Recursive scanning functions
def recursive_scan(symbols: List[str], timeframes: List[str], level: int = 0, parent_hits: Optional[List[Dict]] = None) -> List[Dict]:
    """Multi-timeframe recursive scanning"""
    if level >= len(timeframes) or level >= CFG.get("strategy", {}).get("recursive_scanning", {}).get("max_depth", 3):
        return parent_hits or []
    
    try:
        tf = timeframes[level]
        hits = run_scanner(symbols, timeframe=tf)
        
        # If there were parent hits, intersect by symbol
        if parent_hits is not None:
            parent_symbols = {h["symbol"] for h in parent_hits}
            hits = [h for h in hits if h["symbol"] in parent_symbols]
        
        # Recurse to next timeframe
        return recursive_scan(symbols, timeframes, level + 1, hits)
        
    except Exception as e:
        logger.error(f"Error in recursive scan: {e}")
        return parent_hits or []

def run_scanner(symbols: List[str], timeframe: str = "1min") -> List[Dict]:
    """Run scanner for given symbols and timeframe"""
    try:
        # This would integrate with real scanning logic
        scanner_config = CFG.get("agents", {}).get("scanner", {})
        stocks = get_live_penny_stocks()
        
        hits = []
        for stock in stocks:
            if stock["symbol"] in symbols:
                signal = apply_signal_rules(stock)
                if signal:
                    result = {**stock, **signal, "timeframe": timeframe}
                    hits.append(result)
        
        return hits
        
    except Exception as e:
        logger.error(f"Error running scanner: {e}")
        return []

# Initialize system on import
try:
    load_configuration()
    init_metadata_db()
    logger.info("Global system initialization complete")
except Exception as e:
    logger.error(f"Error during global initialization: {e}")
    CFG = get_default_system_config()
    MEM = get_default_memory_config()