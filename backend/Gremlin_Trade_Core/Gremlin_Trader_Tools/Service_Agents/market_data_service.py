#!/usr/bin/env python3

# ─────────────────────────────────────────────────────────────
# © 2025 StatikFintechLLC  
# Real Market Data Service - Replacing Placeholder Data
# Contact: ascend.gremlin@gmail.com
# ─────────────────────────────────────────────────────────────

import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import logging
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from Gremlin_Trade_Core.globals import setup_module_logger

# Initialize logger
market_logger = setup_module_logger("market_data", "market_service")

class RealMarketDataService:
    """Real-time market data service using yfinance and other data sources"""
    
    def __init__(self):
        self.cache = {}
        self.cache_timeout = 60  # Cache for 60 seconds
        
    async def get_live_penny_stocks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get real live penny stock data with technical indicators"""
        try:
            # Popular penny stock symbols to scan
            penny_symbols = [
                "GPRO", "SAVA", "BBIG", "PROG", "ATER", "MULN", "XELA", "IXHL",
                "BOXL", "GNUS", "INPX", "JAGX", "NAKD", "NVCN", "OBSV", "OZSC",
                "PASO", "PFLC", "RGBP", "RKDA", "RWLK", "SNPW", "SOLO", "TSNP",
                "UONE", "VXRT", "WDLF", "XSPA", "YCBD", "ZSAN", "ADXS", "AGTC",
                "AHPI", "ALPP", "AMPE", "ASRT", "AVGR", "AYTU", "BBRW", "BCDA",
                "BDGR", "BFCH", "BIOL", "BLSP", "BMIC", "BNGO", "BOXD", "BPTS"
            ]
            
            real_stocks = []
            
            # Process symbols in batches to avoid rate limiting
            batch_size = 10
            for i in range(0, min(len(penny_symbols), limit), batch_size):
                batch = penny_symbols[i:i+batch_size]
                batch_data = await self._process_symbol_batch(batch)
                real_stocks.extend(batch_data)
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            # Filter for actual penny stocks (under $10)
            penny_stocks = [stock for stock in real_stocks if stock.get('price', 0) < 10.0]
            
            market_logger.info(f"Retrieved {len(penny_stocks)} real penny stocks")
            return penny_stocks[:limit]
            
        except Exception as e:
            market_logger.error(f"Error getting live penny stocks: {e}")
            return self._get_fallback_data()
    
    async def _process_symbol_batch(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of symbols concurrently"""
        tasks = [self.get_stock_data(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result.get('price'):
                valid_results.append(result)
        
        return valid_results
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive stock data for a single symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Get data from yfinance
            ticker = yf.Ticker(symbol)
            
            # Get recent data (last 2 days to ensure we have data)
            hist = ticker.history(period="2d", interval="1m")
            if hist.empty:
                return None
                
            # Get current price
            current_price = float(hist['Close'].iloc[-1])
            
            # Calculate technical indicators
            indicators = self._calculate_indicators(hist)
            
            # Get volume data
            current_volume = int(hist['Volume'].iloc[-1])
            avg_volume = int(hist['Volume'].tail(50).mean()) if len(hist) > 50 else current_volume
            
            # Calculate price change
            if len(hist) > 1:
                prev_close = float(hist['Close'].iloc[-2])
                price_change = ((current_price - prev_close) / prev_close) * 100
            else:
                price_change = 0.0
            
            stock_data = {
                "symbol": symbol,
                "price": round(current_price, 2),
                "volume": current_volume,
                "avg_volume": avg_volume,
                "rotation": round(current_volume / avg_volume if avg_volume > 0 else 1.0, 2),
                "up_pct": round(price_change, 2),
                "ema": {
                    "5": round(indicators.get('ema_5', current_price), 2),
                    "20": round(indicators.get('ema_20', current_price), 2)
                },
                "sma": {
                    "5": round(indicators.get('sma_5', current_price), 2),
                    "20": round(indicators.get('sma_20', current_price), 2)
                },
                "vwap": round(indicators.get('vwap', current_price), 2),
                "rsi": round(indicators.get('rsi', 50), 1),
                "macd": indicators.get('macd', {}),
                "bollinger": indicators.get('bollinger', {}),
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.cache[cache_key] = stock_data
            
            return stock_data
            
        except Exception as e:
            market_logger.error(f"Error getting data for {symbol}: {e}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators from price data"""
        try:
            indicators = {}
            
            if len(df) < 5:
                return indicators
                
            # Moving averages
            if len(df) >= 5:
                indicators['sma_5'] = df['Close'].rolling(5).mean().iloc[-1]
                indicators['ema_5'] = df['Close'].ewm(span=5).mean().iloc[-1]
            
            if len(df) >= 20:
                indicators['sma_20'] = df['Close'].rolling(20).mean().iloc[-1]
                indicators['ema_20'] = df['Close'].ewm(span=20).mean().iloc[-1]
            
            # VWAP
            if 'Volume' in df.columns:
                vwap = (df['Close'] * df['Volume']).sum() / df['Volume'].sum()
                indicators['vwap'] = vwap
            
            # RSI
            if len(df) >= 14:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = rsi.iloc[-1]
            
            # MACD
            if len(df) >= 26:
                exp1 = df['Close'].ewm(span=12).mean()
                exp2 = df['Close'].ewm(span=26).mean()
                macd = exp1 - exp2
                signal = macd.ewm(span=9).mean()
                histogram = macd - signal
                
                indicators['macd'] = {
                    'macd': macd.iloc[-1],
                    'signal': signal.iloc[-1],
                    'histogram': histogram.iloc[-1]
                }
            
            # Bollinger Bands
            if len(df) >= 20:
                sma_20 = df['Close'].rolling(20).mean()
                std_20 = df['Close'].rolling(20).std()
                
                indicators['bollinger'] = {
                    'upper': (sma_20 + (std_20 * 2)).iloc[-1],
                    'lower': (sma_20 - (std_20 * 2)).iloc[-1],
                    'middle': sma_20.iloc[-1]
                }
            
            return indicators
            
        except Exception as e:
            market_logger.error(f"Error calculating indicators: {e}")
            return {}
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get general market overview data"""
        try:
            # Major indices
            indices = ["^GSPC", "^DJI", "^IXIC", "^RUT"]  # S&P 500, Dow, NASDAQ, Russell 2000
            index_data = {}
            
            for index in indices:
                ticker = yf.Ticker(index)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = float(hist['Close'].iloc[-1])
                    prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
                    change_pct = ((current - prev) / prev) * 100 if prev != 0 else 0
                    
                    index_data[index] = {
                        "price": round(current, 2),
                        "change_pct": round(change_pct, 2)
                    }
            
            # VIX (Volatility Index)
            vix_ticker = yf.Ticker("^VIX")
            vix_hist = vix_ticker.history(period="1d")
            vix_value = float(vix_hist['Close'].iloc[-1]) if not vix_hist.empty else 20.0
            
            return {
                "indices": index_data,
                "vix": round(vix_value, 2),
                "market_sentiment": "bullish" if vix_value < 20 else "bearish" if vix_value > 30 else "neutral",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            market_logger.error(f"Error getting market overview: {e}")
            return {"error": "Unable to fetch market overview"}
    
    def _get_fallback_data(self) -> List[Dict[str, Any]]:
        """Fallback data when real data is unavailable"""
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
                "error": "Real data unavailable - showing sample"
            }
        ]

# Global instance
real_market_service = RealMarketDataService()

# Convenience functions for backward compatibility
async def get_live_penny_stocks_real(limit: int = 50) -> List[Dict[str, Any]]:
    """Get real live penny stocks - replaces placeholder function"""
    return await real_market_service.get_live_penny_stocks(limit)

async def get_stock_data_real(symbol: str) -> Optional[Dict[str, Any]]:
    """Get real stock data for a symbol"""
    return await real_market_service.get_stock_data(symbol)

async def get_market_overview_real() -> Dict[str, Any]:
    """Get real market overview"""
    return await real_market_service.get_market_overview()
