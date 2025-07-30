#!/usr/bin/env python3
"""
Penny Stock Strategy - Specialized penny stock detection and analysis
Implements penny stock specific criteria and momentum detection
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from Gremlin_Trade_Core.globals import (
    CFG, MEM, logger, setup_module_logger,
    get_live_penny_stocks, apply_signal_rules
)

# Set up logging
strategy_logger = setup_module_logger("strategy", "penny_stock")

class PennyStockStrategy:
    """
    Specialized strategy for penny stock detection and analysis
    Focuses on momentum, volume spikes, and gap patterns
    """
    
    def __init__(self):
        self.config = CFG.get("strategy", {}).get("penny_stock_strategies", {})
        self.base_criteria = self.config.get("base_criteria", {})
        self.momentum_filters = self.config.get("momentum_filters", {})
        self.technical_indicators = self.config.get("technical_indicators", {})
        self.spoof_monitoring = CFG.get("strategy", {}).get("spoof_spike_monitoring", {})
        
        strategy_logger.info("Penny stock strategy initialized")
    
    async def scan_penny_stocks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Scan for penny stocks meeting our criteria
        """
        try:
            strategy_logger.info(f"Starting penny stock scan - limit {limit}")
            
            # Get live penny stocks from scanner
            penny_stocks = get_live_penny_stocks(limit=limit * 2)  # Get more to filter
            
            # Apply penny stock specific filtering
            filtered_stocks = []
            for stock in penny_stocks:
                if await self._meets_penny_criteria(stock):
                    # Add penny stock specific analysis
                    enhanced_stock = await self._enhance_penny_analysis(stock)
                    filtered_stocks.append(enhanced_stock)
                    
                    if len(filtered_stocks) >= limit:
                        break
            
            # Sort by penny stock score
            filtered_stocks.sort(key=lambda x: x.get("penny_score", 0), reverse=True)
            
            strategy_logger.info(f"Penny stock scan complete: {len(filtered_stocks)} qualified stocks")
            return filtered_stocks
            
        except Exception as e:
            strategy_logger.error(f"Error in penny stock scan: {e}")
            return []
    
    async def _meets_penny_criteria(self, stock: Dict[str, Any]) -> bool:
        """Check if stock meets penny stock criteria"""
        try:
            # Price criteria
            price = stock.get("price", 0)
            price_range = self.base_criteria.get("price_range", {})
            min_price = price_range.get("min", 0.10)
            max_price = price_range.get("max", 10.0)
            
            if not (min_price <= price <= max_price):
                return False
            
            # Volume criteria
            volume = stock.get("volume", 0)
            volume_criteria = self.base_criteria.get("volume_criteria", {})
            min_volume = volume_criteria.get("min_volume", 1000000)
            
            if volume < min_volume:
                return False
            
            # Float criteria (if available)
            float_mil = stock.get("float_million", 0)
            if float_mil > 0:
                float_criteria = self.base_criteria.get("float_criteria", {})
                max_float = float_criteria.get("max_float_million", 25)
                
                if float_mil > max_float:
                    return False
                
                # Calculate rotation
                rotation = (volume / 1000000) / float_mil if float_mil > 0 else 0
                min_rotation = float_criteria.get("rotation_min", 2.0)
                
                if rotation < min_rotation:
                    return False
                
                stock["rotation"] = rotation
            
            # Momentum criteria
            up_pct = stock.get("up_pct", 0)
            min_gain = self.momentum_filters.get("intraday_gain_min", 5.0)
            
            if up_pct < min_gain:
                return False
            
            return True
            
        except Exception as e:
            strategy_logger.error(f"Error checking penny criteria: {e}")
            return False
    
    async def _enhance_penny_analysis(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Add penny stock specific analysis"""
        try:
            enhanced = stock.copy()
            
            # Calculate penny stock score
            penny_score = await self._calculate_penny_score(stock)
            enhanced["penny_score"] = penny_score
            
            # Add momentum analysis
            momentum_analysis = await self._analyze_momentum(stock)
            enhanced.update(momentum_analysis)
            
            # Add spoof detection
            spoof_analysis = await self._detect_spoofing(stock)
            enhanced.update(spoof_analysis)
            
            # Add gap analysis
            gap_analysis = await self._analyze_gaps(stock)
            enhanced.update(gap_analysis)
            
            # Technical indicator analysis
            tech_analysis = await self._analyze_technical_indicators(stock)
            enhanced.update(tech_analysis)
            
            enhanced["strategy_type"] = "penny_stock"
            enhanced["analysis_timestamp"] = datetime.now(timezone.utc).isoformat()
            
            return enhanced
            
        except Exception as e:
            strategy_logger.error(f"Error enhancing penny analysis: {e}")
            return stock
    
    async def _calculate_penny_score(self, stock: Dict[str, Any]) -> float:
        """Calculate comprehensive penny stock score"""
        try:
            score = 0.0
            
            # Volume factor (higher volume = better)
            volume = stock.get("volume", 0)
            if volume > 10000000:  # 10M+
                score += 0.3
            elif volume > 5000000:  # 5M+
                score += 0.2
            elif volume > 1000000:  # 1M+
                score += 0.1
            
            # Price momentum factor
            up_pct = stock.get("up_pct", 0)
            if up_pct > 50:
                score += 0.25
            elif up_pct > 20:
                score += 0.15
            elif up_pct > 10:
                score += 0.1
            
            # Rotation factor
            rotation = stock.get("rotation", 0)
            if rotation > 10:
                score += 0.2
            elif rotation > 5:
                score += 0.15
            elif rotation > 2:
                score += 0.1
            
            # Float factor (lower float = better for penny stocks)
            float_mil = stock.get("float_million", 0)
            if 0 < float_mil <= 5:
                score += 0.15
            elif 5 < float_mil <= 15:
                score += 0.1
            elif 15 < float_mil <= 25:
                score += 0.05
            
            # Signal strength factor
            signals = stock.get("signal", [])
            signal_count = len(signals)
            score += min(0.1, signal_count * 0.02)
            
            return min(1.0, score)
            
        except Exception as e:
            strategy_logger.error(f"Error calculating penny score: {e}")
            return 0.5
    
    async def _analyze_momentum(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze momentum characteristics"""
        try:
            analysis = {}
            
            up_pct = stock.get("up_pct", 0)
            volume = stock.get("volume", 0)
            avg_volume = stock.get("avg_volume", volume)
            
            # Momentum classification
            if up_pct > 100:
                analysis["momentum_type"] = "explosive"
            elif up_pct > 50:
                analysis["momentum_type"] = "strong"
            elif up_pct > 20:
                analysis["momentum_type"] = "moderate"
            else:
                analysis["momentum_type"] = "weak"
            
            # Volume acceleration
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            analysis["volume_acceleration"] = volume_ratio
            
            # Acceleration factor from config
            acceleration_factor = self.momentum_filters.get("acceleration_factor", 1.5)
            analysis["meets_acceleration"] = volume_ratio >= acceleration_factor
            
            # Gap detection
            gap_up_min = self.momentum_filters.get("gap_up_min", 3.0)
            analysis["gap_up"] = up_pct >= gap_up_min
            
            return analysis
            
        except Exception as e:
            strategy_logger.error(f"Error analyzing momentum: {e}")
            return {}
    
    async def _detect_spoofing(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Detect potential spoofing patterns"""
        try:
            analysis = {}
            
            spoof_config = self.spoof_monitoring.get("spoof_detection", {})
            
            # Volume-based spoof detection
            volume = stock.get("volume", 0)
            avg_volume = stock.get("avg_volume", volume)
            
            wall_multiplier = spoof_config.get("wall_size_multiplier", 3.0)
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            
            # Simple spoof indicators
            analysis["volume_spike_ratio"] = volume_ratio
            analysis["potential_spoof"] = volume_ratio > wall_multiplier * 2
            
            # Bid-ask manipulation check (mock implementation)
            analysis["bid_ask_manipulation"] = False  # Would need Level 2 data
            
            # Pattern recognition (simplified)
            signals = stock.get("signal", [])
            suspicious_patterns = ["wall", "fake", "spoof", "manipulation"]
            analysis["suspicious_signals"] = any(
                any(pattern in str(signal).lower() for pattern in suspicious_patterns)
                for signal in signals
            )
            
            # Overall spoof risk
            spoof_risk = 0.0
            if analysis["potential_spoof"]:
                spoof_risk += 0.4
            if analysis["suspicious_signals"]:
                spoof_risk += 0.3
            if volume_ratio > 10:  # Extreme volume
                spoof_risk += 0.3
                
            analysis["spoof_risk_score"] = min(1.0, spoof_risk)
            
            return analysis
            
        except Exception as e:
            strategy_logger.error(f"Error detecting spoofing: {e}")
            return {}
    
    async def _analyze_gaps(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze gap patterns"""
        try:
            analysis = {}
            
            up_pct = stock.get("up_pct", 0)
            
            # Gap classification
            if up_pct > 20:
                analysis["gap_type"] = "major_gap"
            elif up_pct > 10:
                analysis["gap_type"] = "significant_gap"
            elif up_pct > 5:
                analysis["gap_type"] = "minor_gap"
            else:
                analysis["gap_type"] = "no_gap"
            
            # Gap strength
            gap_strength = min(1.0, up_pct / 50.0)  # Normalize to 50% max
            analysis["gap_strength"] = gap_strength
            
            # Volume confirmation
            volume = stock.get("volume", 0)
            avg_volume = stock.get("avg_volume", volume)
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
            
            analysis["volume_confirmed_gap"] = volume_ratio > 2.0
            
            return analysis
            
        except Exception as e:
            strategy_logger.error(f"Error analyzing gaps: {e}")
            return {}
    
    async def _analyze_technical_indicators(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical indicators for penny stocks"""
        try:
            analysis = {}
            
            # EMA analysis (simplified - would need historical data)
            ema_config = self.technical_indicators.get("ema_settings", {})
            signals = stock.get("signal", [])
            
            ema_signals = [s for s in signals if "ema" in str(s).lower()]
            analysis["ema_signals"] = ema_signals
            analysis["ema_bullish"] = any("bullish" in str(s).lower() for s in ema_signals)
            
            # RSI analysis (mock - would need calculation)
            rsi_config = self.technical_indicators.get("rsi_settings", {})
            # Mock RSI based on momentum
            up_pct = stock.get("up_pct", 0)
            mock_rsi = min(90, 50 + (up_pct / 2))  # Rough approximation
            analysis["rsi_estimate"] = mock_rsi
            analysis["rsi_overbought"] = mock_rsi > rsi_config.get("overbought", 70)
            
            # VWAP analysis
            vwap_config = self.technical_indicators.get("vwap_settings", {})
            vwap_signals = [s for s in signals if "vwap" in str(s).lower()]
            analysis["vwap_signals"] = vwap_signals
            analysis["vwap_breakout"] = any("break" in str(s).lower() for s in vwap_signals)
            
            return analysis
            
        except Exception as e:
            strategy_logger.error(f"Error analyzing technical indicators: {e}")
            return {}

# Global strategy instance
penny_stock_strategy = PennyStockStrategy()

# Export functions for use by other modules
async def scan_penny_stocks(limit: int = 50) -> List[Dict[str, Any]]:
    """Scan for penny stocks using the penny stock strategy"""
    return await penny_stock_strategy.scan_penny_stocks(limit)

def get_penny_strategy_config() -> Dict[str, Any]:
    """Get penny stock strategy configuration"""
    return penny_stock_strategy.config

if __name__ == "__main__":
    # Test the strategy
    import asyncio
    
    async def test_penny_strategy():
        results = await scan_penny_stocks(10)
        print(f"Penny stock strategy test complete: {len(results)} results")
        for result in results:
            symbol = result.get('symbol')
            score = result.get('penny_score', 0)
            momentum = result.get('momentum_type', 'unknown')
            print(f"  {symbol}: {score:.2f} score, {momentum} momentum")
    
    asyncio.run(test_penny_strategy())
