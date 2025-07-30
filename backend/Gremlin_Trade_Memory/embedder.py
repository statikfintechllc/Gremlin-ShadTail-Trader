#!/usr/bin/env python3

# ─────────────────────────────────────────────────────────────
# © 2025 StatikFintechLLC
# Contact: ascend.gremlin@gmail.com
# ─────────────────────────────────────────────────────────────

# Gremlin Trader Memory Embedder & Vector Store Core
# Autonomous Trading System with Real Memory Management

import os
import json
import sqlite3
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import threading
import time
import uuid

# Import from centralized globals
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Gremlin_Trade_Core.globals import (
    CFG, MEM, logger, setup_module_logger, resolve_path, DATA_DIR,
    METADATA_DB_PATH, CHROMA_DIR, CHROMA_DB_PATH, VECTOR_STORE_DIR
)

# Module logger
embedder_logger = setup_module_logger("memory", "embedder")

# Initialize chromadb if available
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
    embedder_logger.info("ChromaDB available")
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False
    embedder_logger.warning("ChromaDB not available - using fallback storage")

# Initialize sentence transformers if available
try:
    from sentence_transformers import SentenceTransformer
    ML_AVAILABLE = True
    embedder_logger.info("SentenceTransformers available")
except ImportError:
    SentenceTransformer = None
    ML_AVAILABLE = False
    embedder_logger.warning("SentenceTransformers not available - using dummy encoder")

# Trading libraries
try:
    import yfinance as yf
    import ta
    TRADING_LIBS_AVAILABLE = True
    embedder_logger.info("Trading libraries available")
except ImportError:
    yf = None
    ta = None
    TRADING_LIBS_AVAILABLE = False
    embedder_logger.warning("Trading libraries not available")

# Configuration & Paths - Use unified ChromaDB configuration from globals
# Unified path configuration - use only one ChromaDB database
LOCAL_INDEX_PATH = VECTOR_STORE_DIR / "local_index"

# Ensure directories exist using centralized CHROMA_DIR
for path in [CHROMA_DIR, LOCAL_INDEX_PATH, VECTOR_STORE_DIR]:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        embedder_logger.error(f"[EMBEDDER] Failed to create directory {path}: {e}")

embedder_logger.info(f"Using unified ChromaDB at: {CHROMA_DIR}")
embedder_logger.info(f"Using metadata DB at: {METADATA_DB_PATH}")

# Global variables for autonomous operation
memory_vectors = {}
active_positions = {}
trade_signals = {}
market_data_cache = {}
autonomous_mode = False
trading_thread = None
monitoring_thread = None

# Initialize transformer model
_model = None

def get_model():
    """Get or initialize the sentence transformer model"""
    global _model
    if _model is None and ML_AVAILABLE:
        try:
            model_name = MEM.get("embedding", {}).get("model", "all-MiniLM-L6-v2")
            _model = SentenceTransformer(model_name)
            embedder_logger.info(f"Initialized SentenceTransformer model: {model_name}")
        except Exception as e:
            embedder_logger.error(f"Error initializing model: {e}")
            _model = None
    return _model

def encode(text: str) -> np.ndarray:
    """Encode text to vector embedding"""
    try:
        model = get_model()
        if model is not None:
            return model.encode(text)
        else:
            return dummy_encode(text)
    except Exception as e:
        embedder_logger.error(f"Error encoding text: {e}")
        return dummy_encode(text)

def dummy_encode(text):
    """Dummy encoder when sentence_transformers not available"""
    dimension = MEM.get("embedding", {}).get("dimension", 384)
    # Create a simple hash-based encoding for consistency
    hash_val = hash(text) % (2**31)
    np.random.seed(hash_val)
    return np.random.rand(dimension).astype(np.float32)

# Enhanced ChromaDB Setup with proper SQLite configuration
_chroma_client = None
_collection = None

def get_chroma_client():
    """Get or initialize ChromaDB client with proper SQLite backend"""
    global _chroma_client, _collection
    
    if not CHROMA_AVAILABLE:
        return None, None
        
    if _chroma_client is None:
        try:
            # Ensure chroma directory and SQLite file exist
            CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB with SQLite backend
            settings = Settings(
                persist_directory=str(CHROMA_DIR),
                anonymized_telemetry=False,
                is_persistent=True
            )
            
            _chroma_client = chromadb.PersistentClient(
                path=str(CHROMA_DIR),
                settings=settings
            )
            
            # Create or get the main collection
            _collection = _chroma_client.get_or_create_collection(
                name="gremlin_memory",
                metadata={"description": "Gremlin ShadTail Trader Memory Store"}
            )
            
            embedder_logger.info(f"ChromaDB client initialized at {CHROMA_DIR}")
            embedder_logger.info(f"Collection count: {_collection.count()}")
            
        except Exception as e:
            embedder_logger.error(f"Failed to initialize Chroma client: {e}")
            _chroma_client = None
            _collection = None
            
    return _chroma_client, _collection

def init_metadata_database():
    """Initialize enhanced metadata database for autonomous trading"""
    try:
        conn = sqlite3.connect(METADATA_DB_PATH)
        cursor = conn.cursor()
        
        # Enhanced signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                price REAL NOT NULL,
                volume INTEGER,
                timestamp TEXT NOT NULL,
                timeframe TEXT,
                indicators TEXT,
                metadata TEXT,
                processed BOOLEAN DEFAULT FALSE,
                INDEX(symbol, timestamp),
                INDEX(signal_type, confidence)
            )
        ''')
        
        # Enhanced trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                pnl REAL DEFAULT 0,
                fees REAL DEFAULT 0,
                strategy TEXT,
                signal_id TEXT,
                metadata TEXT,
                status TEXT DEFAULT 'pending',
                INDEX(symbol, timestamp),
                INDEX(status, timestamp),
                FOREIGN KEY(signal_id) REFERENCES signals(id)
            )
        ''')
        
        # Enhanced positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                current_price REAL,
                unrealized_pnl REAL,
                realized_pnl REAL DEFAULT 0,
                timestamp TEXT NOT NULL,
                last_updated TEXT,
                stop_loss REAL,
                take_profit REAL,
                status TEXT DEFAULT 'open',
                metadata TEXT,
                INDEX(symbol, status),
                INDEX(timestamp)
            )
        ''')
        
        # Market data cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER,
                timestamp TEXT NOT NULL,
                timeframe TEXT DEFAULT '1min',
                ohlcv TEXT,
                indicators TEXT,
                INDEX(symbol, timestamp),
                INDEX(timeframe, timestamp)
            )
        ''')
        
        # Strategy performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_performance (
                id TEXT PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                max_drawdown REAL DEFAULT 0,
                sharpe_ratio REAL DEFAULT 0,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                INDEX(strategy_name, timestamp)
            )
        ''')
        
        # Memory embeddings metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embedding_metadata (
                id TEXT PRIMARY KEY,
                text_hash TEXT NOT NULL,
                content_type TEXT NOT NULL,
                source TEXT,
                importance_score REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                created_at TEXT NOT NULL,
                tags TEXT,
                metadata TEXT
            )
        ''')
        
        # Create indexes separately
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_embedding_content_importance 
            ON embedding_metadata(content_type, importance_score)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_embedding_source_created 
            ON embedding_metadata(source, created_at)
        ''')
        
        conn.commit()
        conn.close()
        embedder_logger.info("Enhanced metadata database initialized")
        
    except Exception as e:
        embedder_logger.error(f"Error initializing metadata database: {e}")

def store_embedding(embedding: Dict[str, Any]) -> Dict[str, Any]:
    """Store embedding in both ChromaDB and metadata database"""
    try:
        emb_id = embedding["id"]
        text = embedding["text"]
        vector = np.array(embedding["vector"])
        meta = embedding["meta"]
        
        # Store in memory
        memory_vectors[emb_id] = embedding
        
        # Store in ChromaDB
        client, collection = get_chroma_client()
        if collection is not None:
            try:
                collection.add(
                    documents=[text],
                    embeddings=[vector.tolist() if hasattr(vector, "tolist") else list(vector)],
                    metadatas=[meta],
                    ids=[emb_id]
                )
                embedder_logger.debug(f"Added to ChromaDB: {emb_id}")
            except Exception as e:
                embedder_logger.error(f"ChromaDB add failed for {emb_id}: {e}")
        
        # Store metadata in SQLite
        try:
            conn = sqlite3.connect(METADATA_DB_PATH)
            cursor = conn.cursor()
            
            text_hash = str(hash(text))
            cursor.execute('''
                INSERT OR REPLACE INTO embedding_metadata 
                (id, text_hash, content_type, source, importance_score, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                emb_id, 
                text_hash,
                meta.get("content_type", "general"),
                meta.get("source", "system"),
                meta.get("importance_score", 0.5),
                datetime.now(timezone.utc).isoformat(),
                json.dumps(meta)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            embedder_logger.error(f"Failed to store embedding metadata: {e}")
        
        # Always store locally as backup
        _write_to_disk(embedding)
        
        embedder_logger.info(f"Stored embedding: {emb_id}")
        return embedding
        
    except Exception as e:
        embedder_logger.error(f"Error storing embedding: {e}")
        return embedding

def package_embedding(text: str, vector: np.ndarray, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Package embedding with metadata and store it"""
    try:
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
        
        # Store the embedding
        return store_embedding(embedding)
        
    except Exception as e:
        embedder_logger.error(f"Error packaging embedding: {e}")
        return {}

# Autonomous Trading Functions

def get_live_market_data(symbol: str, timeframe: str = "1min") -> Optional[Dict[str, Any]]:
    """Get live market data for a symbol"""
    if not TRADING_LIBS_AVAILABLE:
        embedder_logger.warning("Trading libraries not available")
        return None
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Get recent data
        if timeframe == "1min":
            data = ticker.history(period="1d", interval="1m")
        elif timeframe == "5min":
            data = ticker.history(period="5d", interval="5m")
        elif timeframe == "15min":
            data = ticker.history(period="1mo", interval="15m")
        else:
            data = ticker.history(period="1d", interval="1m")
        
        if data.empty:
            return None
        
        latest = data.iloc[-1]
        
        # Calculate technical indicators
        indicators = {}
        if len(data) >= 20:
            # Moving averages
            indicators["sma_5"] = data["Close"].rolling(5).mean().iloc[-1]
            indicators["sma_20"] = data["Close"].rolling(20).mean().iloc[-1]
            indicators["ema_12"] = data["Close"].ewm(span=12).mean().iloc[-1]
            indicators["ema_26"] = data["Close"].ewm(span=26).mean().iloc[-1]
            
            # MACD
            macd_line = indicators["ema_12"] - indicators["ema_26"]
            signal_line = data["Close"].ewm(span=9).mean().iloc[-1]
            indicators["macd"] = macd_line
            indicators["macd_signal"] = signal_line
            indicators["macd_histogram"] = macd_line - signal_line
            
            # RSI
            if len(data) >= 14:
                indicators["rsi"] = ta.momentum.RSIIndicator(data["Close"]).rsi().iloc[-1]
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(data["Close"])
            indicators["bb_upper"] = bb.bollinger_hband().iloc[-1]
            indicators["bb_middle"] = bb.bollinger_mavg().iloc[-1]
            indicators["bb_lower"] = bb.bollinger_lband().iloc[-1]
        
        market_data = {
            "symbol": symbol,
            "price": float(latest["Close"]),
            "volume": int(latest["Volume"]),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timeframe": timeframe,
            "indicators": indicators
        }
        
        # Cache the data
        market_data_cache[f"{symbol}_{timeframe}"] = market_data
        
        # Store in database
        try:
            conn = sqlite3.connect(METADATA_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO market_data 
                (id, symbol, price, volume, timestamp, timeframe, indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(uuid.uuid4()),
                symbol,
                market_data["price"],
                market_data["volume"],
                market_data["timestamp"],
                timeframe,
                json.dumps(indicators)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            embedder_logger.error(f"Failed to store market data: {e}")
        
        return market_data
        
    except Exception as e:
        embedder_logger.error(f"Error getting market data for {symbol}: {e}")
        return None

def analyze_signal(market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Analyze market data and generate trading signals"""
    try:
        symbol = market_data["symbol"]
        price = market_data["price"]
        indicators = market_data.get("indicators", {})
        
        signals = []
        confidence = 0.0
        
        # RSI signals
        rsi = indicators.get("rsi")
        if rsi is not None:
            if rsi < 30:
                signals.append("oversold")
                confidence += 0.3
            elif rsi > 70:
                signals.append("overbought")
                confidence += 0.3
        
        # MACD signals
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                signals.append("macd_bullish")
                confidence += 0.25
            else:
                signals.append("macd_bearish")
                confidence += 0.25
        
        # Moving average signals
        sma_5 = indicators.get("sma_5")
        sma_20 = indicators.get("sma_20")
        if sma_5 is not None and sma_20 is not None:
            if sma_5 > sma_20:
                signals.append("ma_golden_cross")
                confidence += 0.2
            elif sma_5 < sma_20:
                signals.append("ma_death_cross")
                confidence += 0.2
        
        # Bollinger Bands signals
        bb_upper = indicators.get("bb_upper")
        bb_lower = indicators.get("bb_lower")
        if bb_upper is not None and bb_lower is not None:
            if price > bb_upper:
                signals.append("bb_overbought")
                confidence += 0.15
            elif price < bb_lower:
                signals.append("bb_oversold")
                confidence += 0.15
        
        # Volume analysis
        volume = market_data.get("volume", 0)
        if volume > 1000000:  # High volume threshold
            signals.append("high_volume")
            confidence += 0.1
        
        if not signals:
            return None
        
        # Determine overall signal type
        bullish_signals = ["oversold", "macd_bullish", "ma_golden_cross", "bb_oversold"]
        bearish_signals = ["overbought", "macd_bearish", "ma_death_cross", "bb_overbought"]
        
        bullish_count = sum(1 for s in signals if s in bullish_signals)
        bearish_count = sum(1 for s in signals if s in bearish_signals)
        
        if bullish_count > bearish_count:
            signal_type = "BUY"
        elif bearish_count > bullish_count:
            signal_type = "SELL"
        else:
            signal_type = "HOLD"
        
        signal_data = {
            "id": str(uuid.uuid4()),
            "symbol": symbol,
            "signal_type": signal_type,
            "confidence": min(confidence, 1.0),
            "price": price,
            "volume": volume,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "timeframe": market_data.get("timeframe", "1min"),
            "indicators": indicators,
            "signals": signals,
            "metadata": {
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "analysis_version": "1.0"
            }
        }
        
        # Store signal in database
        try:
            conn = sqlite3.connect(METADATA_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signals 
                (id, symbol, signal_type, confidence, price, volume, timestamp, timeframe, indicators, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_data["id"],
                symbol,
                signal_type,
                signal_data["confidence"],
                price,
                volume,
                signal_data["timestamp"],
                signal_data["timeframe"],
                json.dumps(indicators),
                json.dumps(signal_data["metadata"])
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            embedder_logger.error(f"Failed to store signal: {e}")
        
        # Store signal in memory and as embedding
        trade_signals[signal_data["id"]] = signal_data
        
        # Create embedding for the signal
        signal_text = f"Trading signal for {symbol}: {signal_type} with {confidence:.2f} confidence at ${price:.2f}"
        signal_vector = encode(signal_text)
        signal_embedding = package_embedding(
            signal_text,
            signal_vector,
            {
                "content_type": "trading_signal",
                "source": "autonomous_analyzer",
                "symbol": symbol,
                "signal_type": signal_type,
                "confidence": signal_data["confidence"],
                "importance_score": signal_data["confidence"]
            }
        )
        
        embedder_logger.info(f"Generated {signal_type} signal for {symbol} with confidence {confidence:.2f}")
        
        return signal_data
        
    except Exception as e:
        embedder_logger.error(f"Error analyzing signal: {e}")
        return None

def execute_trade(signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Execute a trade based on a signal (simulation for now)"""
    try:
        symbol = signal["symbol"]
        signal_type = signal["signal_type"]
        price = signal["price"]
        confidence = signal["confidence"]
        
        # Risk management
        max_risk_per_trade = CFG.get("agents", {}).get("risk_management", {}).get("max_risk_per_trade", 0.10)
        
        if confidence < 0.7:  # Minimum confidence threshold
            embedder_logger.info(f"Signal confidence {confidence:.2f} below threshold for {symbol}")
            return None
        
        if signal_type == "HOLD":
            return None
        
        # Calculate position size (simplified)
        account_balance = 10000  # Simulated account balance
        risk_amount = account_balance * max_risk_per_trade
        quantity = int(risk_amount / price)
        
        if quantity <= 0:
            return None
        
        # Create trade record
        trade_data = {
            "id": str(uuid.uuid4()),
            "symbol": symbol,
            "action": signal_type,
            "quantity": quantity,
            "price": price,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_id": signal["id"],
            "strategy": "autonomous_v1",
            "status": "executed",  # Simulated execution
            "metadata": {
                "confidence": confidence,
                "risk_amount": risk_amount,
                "account_balance": account_balance
            }
        }
        
        # Store trade in database
        try:
            conn = sqlite3.connect(METADATA_DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades 
                (id, symbol, action, quantity, price, timestamp, signal_id, strategy, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade_data["id"],
                symbol,
                signal_type,
                quantity,
                price,
                trade_data["timestamp"],
                signal["id"],
                "autonomous_v1",
                "executed",
                json.dumps(trade_data["metadata"])
            ))
            
            # Update or create position
            if signal_type == "BUY":
                cursor.execute('''
                    INSERT OR REPLACE INTO positions 
                    (id, symbol, quantity, avg_price, current_price, timestamp, last_updated, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    symbol,
                    quantity,
                    price,
                    price,
                    trade_data["timestamp"],
                    trade_data["timestamp"],
                    "open"
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            embedder_logger.error(f"Failed to store trade: {e}")
        
        # Create embedding for the trade
        trade_text = f"Executed {signal_type} trade for {quantity} shares of {symbol} at ${price:.2f}"
        trade_vector = encode(trade_text)
        trade_embedding = package_embedding(
            trade_text,
            trade_vector,
            {
                "content_type": "trade_execution",
                "source": "autonomous_trader",
                "symbol": symbol,
                "action": signal_type,
                "quantity": quantity,
                "price": price,
                "importance_score": 0.9
            }
        )
        
        embedder_logger.info(f"Executed {signal_type} trade: {quantity} shares of {symbol} at ${price:.2f}")
        
        return trade_data
        
    except Exception as e:
        embedder_logger.error(f"Error executing trade: {e}")
        return None

def monitor_positions():
    """Monitor open positions and update their status"""
    try:
        conn = sqlite3.connect(METADATA_DB_PATH)
        cursor = conn.cursor()
        
        # Get open positions
        cursor.execute('''
            SELECT id, symbol, quantity, avg_price, current_price 
            FROM positions 
            WHERE status = 'open'
        ''')
        
        positions = cursor.fetchall()
        
        for position in positions:
            pos_id, symbol, quantity, avg_price, current_price = position
            
            # Get current market data
            market_data = get_live_market_data(symbol)
            if market_data:
                new_price = market_data["price"]
                unrealized_pnl = (new_price - avg_price) * quantity
                
                # Update position
                cursor.execute('''
                    UPDATE positions 
                    SET current_price = ?, unrealized_pnl = ?, last_updated = ?
                    WHERE id = ?
                ''', (
                    new_price,
                    unrealized_pnl,
                    datetime.now(timezone.utc).isoformat(),
                    pos_id
                ))
                
                embedder_logger.debug(f"Updated position {symbol}: PnL ${unrealized_pnl:.2f}")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        embedder_logger.error(f"Error monitoring positions: {e}")

def autonomous_trading_loop():
    """Main autonomous trading loop"""
    embedder_logger.info("Starting autonomous trading loop...")
    
    # Watchlist of penny stocks to monitor
    watchlist = ["SIRI", "F", "NOK", "VALE", "GOLD", "SNAP", "PLUG", "WISH", "SOFI", "PLTR"]
    
    while autonomous_mode:
        try:
            for symbol in watchlist:
                if not autonomous_mode:
                    break
                
                # Get market data
                market_data = get_live_market_data(symbol)
                if market_data:
                    # Analyze for signals
                    signal = analyze_signal(market_data)
                    if signal and signal["signal_type"] != "HOLD":
                        # Execute trade
                        trade = execute_trade(signal)
                        if trade:
                            embedder_logger.info(f"Autonomous trade executed: {trade['action']} {trade['symbol']}")
                
                # Monitor existing positions
                monitor_positions()
                
                # Brief pause between symbols
                time.sleep(1)
            
            # Longer pause between complete cycles
            time.sleep(60)  # 1 minute between cycles
            
        except Exception as e:
            embedder_logger.error(f"Error in autonomous trading loop: {e}")
            time.sleep(10)  # Brief pause on error
    
    embedder_logger.info("Autonomous trading loop stopped")

def start_autonomous_trading():
    """Start the autonomous trading system"""
    global autonomous_mode, trading_thread, monitoring_thread
    
    if autonomous_mode:
        embedder_logger.warning("Autonomous trading is already running")
        return
    
    embedder_logger.info("Starting autonomous trading system...")
    
    autonomous_mode = True
    
    # Start trading thread
    trading_thread = threading.Thread(target=autonomous_trading_loop, daemon=True)
    trading_thread.start()
    
    embedder_logger.info("Autonomous trading system started")

def stop_autonomous_trading():
    """Stop the autonomous trading system"""
    global autonomous_mode, trading_thread, monitoring_thread
    
    if not autonomous_mode:
        embedder_logger.warning("Autonomous trading is not running")
        return
    
    embedder_logger.info("Stopping autonomous trading system...")
    
    autonomous_mode = False
    
    # Wait for threads to finish
    if trading_thread and trading_thread.is_alive():
        trading_thread.join(timeout=5)
    
    embedder_logger.info("Autonomous trading system stopped")

def get_trading_status():
    """Get current trading system status"""
    return {
        "autonomous_mode": autonomous_mode,
        "active_positions": len([p for p in active_positions.values() if p.get("status") == "open"]),
        "pending_signals": len([s for s in trade_signals.values() if not s.get("processed", False)]),
        "market_data_cache_size": len(market_data_cache),
        "memory_vectors_count": len(memory_vectors),
        "chroma_available": CHROMA_AVAILABLE,
        "trading_libs_available": TRADING_LIBS_AVAILABLE
    }

# Enhanced existing functions

def query_embeddings(query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Query embeddings by similarity using ChromaDB if available"""
    try:
        # Try ChromaDB first
        client, collection = get_chroma_client()
        if collection is not None:
            query_vector = encode(query_text)
            results = collection.query(
                query_embeddings=[query_vector.tolist()],
                n_results=limit
            )
            
            embeddings = []
            for i in range(len(results['ids'][0])):
                embeddings.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
            
            return embeddings
        
        # Fallback to memory search
        if not memory_vectors:
            _load_from_disk()
        
        query_vector = encode(query_text)
        all_embeddings = get_all_embeddings()
        
        similarities = []
        for emb in all_embeddings:
            try:
                emb_vector = np.array(emb["vector"])
                similarity = np.dot(query_vector, emb_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(emb_vector)
                )
                similarities.append((similarity, emb))
            except Exception as e:
                embedder_logger.error(f"Error calculating similarity: {e}")
                continue
        
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [emb for _, emb in similarities[:limit]]
        
    except Exception as e:
        embedder_logger.error(f"Error querying embeddings: {e}")
        return []

def get_all_embeddings(limit=50):
    """Get all embeddings from memory and ChromaDB"""
    embeddings = []
    
    # Get from ChromaDB
    try:
        client, collection = get_chroma_client()
        if collection is not None:
            results = collection.get(limit=limit)
            for i in range(len(results['ids'])):
                embeddings.append({
                    "id": results['ids'][i],
                    "text": results['documents'][i] if 'documents' in results else "",
                    "metadata": results['metadatas'][i] if 'metadatas' in results else {},
                    "vector": results['embeddings'][i] if 'embeddings' in results else []
                })
    except Exception as e:
        embedder_logger.error(f"Error getting embeddings from ChromaDB: {e}")
    
    # Get from memory
    if not memory_vectors:
        _load_from_disk()
    
    memory_embeddings = list(memory_vectors.values())[:limit - len(embeddings)]
    embeddings.extend(memory_embeddings)
    
    return embeddings[:limit]

def get_backend_status():
    """Get comprehensive status of all backends and systems"""
    chroma_count = 0
    try:
        client, collection = get_chroma_client()
        if collection is not None:
            chroma_count = collection.count()
    except Exception:
        pass
    
    return {
        "chromadb_available": CHROMA_AVAILABLE,
        "chroma_collection_count": chroma_count,
        "local_index_count": len(memory_vectors),
        "trading_libs_available": TRADING_LIBS_AVAILABLE,
        "autonomous_trading": autonomous_mode,
        "active_positions": len(active_positions),
        "trade_signals": len(trade_signals),
        "market_data_cache": len(market_data_cache),
        "metadata_db_path": str(METADATA_DB_PATH),
        "chroma_db_path": str(CHROMA_DIR),
        "vector_store_path": str(VECTOR_STORE_DIR)
    }

# Utility functions

def _write_to_disk(embedding: Dict[str, Any]):
    """Write embedding to local disk storage"""
    try:
        path = LOCAL_INDEX_PATH / f"{embedding['id']}.json"
        with open(path, "w") as f:
            json.dump(embedding, f, indent=2)
    except Exception as e:
        embedder_logger.error(f"Failed to write {embedding['id']} to disk: {e}")

def _load_from_disk():
    """Load embeddings from local disk storage"""
    if not LOCAL_INDEX_PATH.exists():
        embedder_logger.warning(f"Local index missing: {LOCAL_INDEX_PATH}")
        return
        
    for fname in LOCAL_INDEX_PATH.iterdir():
        if not fname.name.endswith(".json"):
            continue
            
        try:
            with open(fname, "r") as f:
                emb = json.load(f)
            memory_vectors[emb["id"]] = emb
        except Exception as e:
            embedder_logger.warning(f"Failed to load {fname}: {e}")

# Initialize enhanced vector databases and trading system
def init_vector_databases():
    """Initialize vector databases and trading system"""
    try:
        # Initialize metadata database
        init_metadata_database()
        
        # Initialize ChromaDB
        client, collection = get_chroma_client()
        if collection is not None:
            embedder_logger.info(f"ChromaDB initialized with {collection.count()} embeddings")
        
        # Initialize local storage
        LOCAL_INDEX_PATH.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        _load_from_disk()
        
        embedder_logger.info("Enhanced vector databases initialized")
        
        # Initialize autonomous trading system
        if CFG.get("agents", {}).get("autonomous", {}).get("enabled", False):
            start_autonomous_trading()
        
    except Exception as e:
        embedder_logger.error(f"Error initializing vector databases: {e}")

# Initialize on import
try:
    init_vector_databases()
    embedder_logger.info("Enhanced embedder initialization complete")
except Exception as e:
    embedder_logger.error(f"Enhanced embedder initialization failed: {e}")

# Export main functions for use by other modules
__all__ = [
    'store_embedding', 'package_embedding', 'query_embeddings', 'get_all_embeddings',
    'get_backend_status', 'get_trading_status', 'start_autonomous_trading', 'stop_autonomous_trading',
    'get_live_market_data', 'analyze_signal', 'execute_trade', 'monitor_positions'
]
