#!/usr/bin/env python3
"""
Gremlin ShadTail Trader - Strategy Agent
Advanced trading strategy agent with memory-based learning and signal generation
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Import base memory agent
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from Gremlin_Trade_Core.Gremlin_Trader_Tools.Memory_Agent.base_memory_agent import BaseMemoryAgent
from Gremlin_Trade_Core.market_data_service import MarketDataService

class StrategyType(Enum):
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    SWING = "swing"
    TREND_FOLLOWING = "trend_following"
    ARBITRAGE = "arbitrage"

class SignalStrength(Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class TradingSignal:
    symbol: str
    strategy_type: StrategyType
    signal_strength: SignalStrength
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_level: RiskLevel
    position_size: float
    reasoning: str
    indicators: Dict[str, float]
    timestamp: datetime
    expected_duration: timedelta

@dataclass
class StrategyPerformance:
    strategy_type: StrategyType
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float

class StrategyAgent(BaseMemoryAgent):
    """
    Advanced strategy agent that develops, tests, and executes trading strategies
    with memory-based learning and performance optimization
    """
    
    def __init__(self):
        super().__init__("StrategyAgent", "strategy")
        
        # Market data service
        self.market_service = MarketDataService()
        
        # Strategy configurations
        self.strategies = {
            StrategyType.MOMENTUM: {
                'enabled': True,
                'parameters': {
                    'rsi_threshold': 70,
                    'volume_multiplier': 2.0,
                    'momentum_period': 14,
                    'min_price_change': 0.02
                }
            },
            StrategyType.MEAN_REVERSION: {
                'enabled': True,
                'parameters': {
                    'rsi_oversold': 30,
                    'rsi_overbought': 70,
                    'bollinger_std': 2.0,
                    'lookback_period': 20
                }
            },
            StrategyType.BREAKOUT: {
                'enabled': True,
                'parameters': {
                    'volume_threshold': 1.5,
                    'price_threshold': 0.05,
                    'consolidation_period': 10,
                    'breakout_confirmation': 3
                }
            },
            StrategyType.SCALPING: {
                'enabled': True,
                'parameters': {
                    'quick_profit_target': 0.01,
                    'tight_stop_loss': 0.005,
                    'max_hold_time': 300,  # seconds
                    'min_spread': 0.001
                }
            }
        }
        
        # Performance tracking
        self.strategy_performance: Dict[StrategyType, StrategyPerformance] = {}
        self.active_signals: Dict[str, TradingSignal] = {}
        
        # Strategy learning parameters
        self.min_confidence_threshold = 0.6
        self.max_position_size = 0.1  # 10% of portfolio
        self.risk_adjustment_factor = 0.8
        
        # Load strategy performance from memory
        self._load_strategy_performance()
        
        self.logger.info("Strategy Agent initialized with memory integration")
    
    def _load_strategy_performance(self):
        """Load historical strategy performance from memory"""
        try:
            # Retrieve strategy performance memories
            performance_memories = self.retrieve_memories(
                query="strategy performance trades win_rate profit",
                memory_type="strategy_performance",
                limit=50
            )
            
            # Initialize performance tracking
            for strategy_type in StrategyType:
                self.strategy_performance[strategy_type] = StrategyPerformance(
                    strategy_type=strategy_type,
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    avg_profit=0.0,
                    avg_loss=0.0,
                    profit_factor=1.0,
                    max_drawdown=0.0,
                    sharpe_ratio=0.0
                )
            
            # Load from memories
            for memory in performance_memories:
                metadata = memory.get('metadata', {})
                strategy_type_str = metadata.get('strategy_type')
                
                if strategy_type_str:
                    try:
                        strategy_type = StrategyType(strategy_type_str)
                        perf = self.strategy_performance[strategy_type]
                        
                        # Update performance metrics from memory
                        perf.total_trades = metadata.get('total_trades', 0)
                        perf.winning_trades = metadata.get('winning_trades', 0)
                        perf.losing_trades = metadata.get('losing_trades', 0)
                        perf.win_rate = metadata.get('win_rate', 0.0)
                        perf.avg_profit = metadata.get('avg_profit', 0.0)
                        perf.avg_loss = metadata.get('avg_loss', 0.0)
                        perf.profit_factor = metadata.get('profit_factor', 1.0)
                        
                    except ValueError:
                        continue
            
            self.logger.info(f"Loaded performance data for {len(self.strategy_performance)} strategies")
            
        except Exception as e:
            self.logger.error(f"Error loading strategy performance: {e}")
    
    async def analyze_market_conditions(self) -> Dict[str, Any]:
        """Analyze current market conditions for strategy selection"""
        try:
            # Get market data for major indices
            spy_data = await self.market_service.get_historical_data("SPY", days=30)
            vix_data = await self.market_service.get_current_price("VIX")
            
            if not spy_data:
                return {"error": "Unable to get market data"}
            
            # Calculate market metrics
            prices = [float(d['close']) for d in spy_data]
            volumes = [float(d['volume']) for d in spy_data]
            
            current_price = prices[-1]
            prev_price = prices[-2] if len(prices) > 1 else current_price
            price_change = (current_price - prev_price) / prev_price
            
            # Calculate volatility (20-day)
            if len(prices) >= 20:
                returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                volatility = np.std(returns[-20:]) * np.sqrt(252)  # Annualized
            else:
                volatility = 0.2  # Default
            
            # Average volume
            avg_volume = np.mean(volumes[-10:]) if len(volumes) >= 10 else volumes[-1]
            
            # Market trend
            sma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else current_price
            sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else current_price
            
            trend = "bullish" if sma_20 > sma_50 else "bearish"
            
            market_conditions = {
                'price_change': price_change,
                'volatility': volatility,
                'trend': trend,
                'volume': avg_volume,
                'vix': vix_data.get('price', 20) if vix_data else 20,
                'market_regime': self._determine_market_regime(volatility, price_change, trend)
            }
            
            # Store market analysis in memory
            self.store_memory(
                content=f"Market analysis: {trend} trend with {volatility:.2%} volatility, VIX {market_conditions['vix']:.1f}",
                memory_type="market_analysis",
                metadata=market_conditions
            )
            
            return market_conditions
            
        except Exception as e:
            self.logger.error(f"Error analyzing market conditions: {e}")
            return {}
    
    def _determine_market_regime(self, volatility: float, price_change: float, trend: str) -> str:
        """Determine current market regime"""
        if volatility > 0.25:
            return "high_volatility"
        elif volatility < 0.15:
            if abs(price_change) < 0.005:
                return "low_volatility_consolidation"
            else:
                return "trending"
        else:
            return "normal"
    
    async def generate_signals(self, symbols: List[str]) -> List[TradingSignal]:
        """Generate trading signals for given symbols"""
        signals = []
        market_conditions = await self.analyze_market_conditions()
        
        for symbol in symbols:
            try:
                # Get market data
                price_data = await self.market_service.get_historical_data(symbol, days=50)
                if not price_data or len(price_data) < 20:
                    continue
                
                # Try each enabled strategy
                for strategy_type, config in self.strategies.items():
                    if not config['enabled']:
                        continue
                    
                    signal = await self._generate_strategy_signal(
                        symbol, strategy_type, price_data, market_conditions
                    )
                    
                    if signal and signal.confidence >= self.min_confidence_threshold:
                        # Adjust signal based on strategy performance
                        signal = self._adjust_signal_for_performance(signal)
                        
                        # Get similar past experiences
                        situation = f"strategy:{strategy_type.value} symbol:{symbol} confidence:{signal.confidence:.2f}"
                        similar_experiences = self.get_similar_experiences(situation, limit=5)
                        
                        # Adjust confidence based on past performance
                        if similar_experiences:
                            successful_similar = sum(1 for exp in similar_experiences 
                                                   if exp['metadata'].get('success', False))
                            similarity_accuracy = successful_similar / len(similar_experiences)
                            
                            # Blend current confidence with historical accuracy
                            signal.confidence = (signal.confidence * 0.7) + (similarity_accuracy * 0.3)
                        
                        signals.append(signal)
                        
                        # Store signal in memory
                        await self._store_signal_memory(signal, similar_experiences)
                
            except Exception as e:
                self.logger.error(f"Error generating signals for {symbol}: {e}")
        
        # Filter and rank signals
        signals = self._filter_and_rank_signals(signals)
        
        # Update active signals
        for signal in signals:
            self.active_signals[f"{signal.symbol}_{signal.strategy_type.value}"] = signal
        
        self.logger.info(f"Generated {len(signals)} trading signals")
        return signals
    
    async def _generate_strategy_signal(self, symbol: str, strategy_type: StrategyType, 
                                      price_data: List[Dict], market_conditions: Dict) -> Optional[TradingSignal]:
        """Generate signal for specific strategy"""
        try:
            if strategy_type == StrategyType.MOMENTUM:
                return await self._momentum_strategy(symbol, price_data, market_conditions)
            elif strategy_type == StrategyType.MEAN_REVERSION:
                return await self._mean_reversion_strategy(symbol, price_data, market_conditions)
            elif strategy_type == StrategyType.BREAKOUT:
                return await self._breakout_strategy(symbol, price_data, market_conditions)
            elif strategy_type == StrategyType.SCALPING:
                return await self._scalping_strategy(symbol, price_data, market_conditions)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error in {strategy_type.value} strategy for {symbol}: {e}")
            return None
    
    async def _momentum_strategy(self, symbol: str, price_data: List[Dict], 
                               market_conditions: Dict) -> Optional[TradingSignal]:
        """Momentum strategy implementation"""
        try:
            params = self.strategies[StrategyType.MOMENTUM]['parameters']
            
            # Calculate indicators
            prices = [float(d['close']) for d in price_data]
            volumes = [float(d['volume']) for d in price_data]
            
            current_price = prices[-1]
            
            # RSI calculation
            rsi = self._calculate_rsi(prices, 14)
            
            # Volume analysis
            avg_volume = np.mean(volumes[-20:])
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume
            
            # Price momentum
            price_momentum = (current_price - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            
            # Signal conditions
            momentum_signal = (
                rsi > params['rsi_threshold'] and
                volume_ratio > params['volume_multiplier'] and
                price_momentum > params['min_price_change']
            )
            
            if not momentum_signal:
                return None
            
            # Calculate confidence
            confidence = 0.5
            confidence += min(0.2, (rsi - 70) / 30)  # RSI contribution
            confidence += min(0.2, (volume_ratio - 2) / 3)  # Volume contribution
            confidence += min(0.1, price_momentum * 10)  # Momentum contribution
            
            # Market condition adjustment
            if market_conditions.get('trend') == 'bullish':
                confidence += 0.1
            if market_conditions.get('volatility', 0) > 0.3:
                confidence -= 0.1
            
            confidence = max(0.1, min(0.95, confidence))
            
            # Calculate stops and targets
            atr = self._calculate_atr(price_data)
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * 3)
            
            return TradingSignal(
                symbol=symbol,
                strategy_type=StrategyType.MOMENTUM,
                signal_strength=self._determine_signal_strength(confidence),
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_level=self._determine_risk_level(confidence, market_conditions),
                position_size=self._calculate_position_size(confidence, stop_loss, current_price),
                reasoning=f"Momentum signal: RSI {rsi:.1f}, Volume {volume_ratio:.1f}x, Momentum {price_momentum:.2%}",
                indicators={'rsi': rsi, 'volume_ratio': volume_ratio, 'momentum': price_momentum, 'atr': atr},
                timestamp=datetime.now(timezone.utc),
                expected_duration=timedelta(hours=4)
            )
            
        except Exception as e:
            self.logger.error(f"Error in momentum strategy: {e}")
            return None
    
    async def _mean_reversion_strategy(self, symbol: str, price_data: List[Dict], 
                                     market_conditions: Dict) -> Optional[TradingSignal]:
        """Mean reversion strategy implementation"""
        try:
            params = self.strategies[StrategyType.MEAN_REVERSION]['parameters']
            
            prices = [float(d['close']) for d in price_data]
            current_price = prices[-1]
            
            # Calculate indicators
            rsi = self._calculate_rsi(prices, 14)
            bollinger_upper, bollinger_lower = self._calculate_bollinger_bands(prices)
            sma_20 = np.mean(prices[-20:])
            
            # Mean reversion signals
            oversold_signal = (
                rsi < params['rsi_oversold'] and
                current_price < bollinger_lower
            )
            
            overbought_signal = (
                rsi > params['rsi_overbought'] and
                current_price > bollinger_upper
            )
            
            if not (oversold_signal or overbought_signal):
                return None
            
            # Determine signal direction
            is_buy = oversold_signal
            
            # Calculate confidence
            confidence = 0.5
            if is_buy:
                confidence += min(0.3, (30 - rsi) / 30)
                confidence += min(0.2, (bollinger_lower - current_price) / bollinger_lower)
            else:
                confidence += min(0.3, (rsi - 70) / 30)
                confidence += min(0.2, (current_price - bollinger_upper) / bollinger_upper)
            
            confidence = max(0.1, min(0.95, confidence))
            
            # Calculate stops and targets
            if is_buy:
                stop_loss = current_price * 0.95
                take_profit = sma_20
            else:
                stop_loss = current_price * 1.05
                take_profit = sma_20
            
            return TradingSignal(
                symbol=symbol,
                strategy_type=StrategyType.MEAN_REVERSION,
                signal_strength=self._determine_signal_strength(confidence),
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_level=self._determine_risk_level(confidence, market_conditions),
                position_size=self._calculate_position_size(confidence, stop_loss, current_price),
                reasoning=f"Mean reversion: RSI {rsi:.1f}, Price vs Bollinger {'below' if is_buy else 'above'}",
                indicators={'rsi': rsi, 'bollinger_upper': bollinger_upper, 'bollinger_lower': bollinger_lower},
                timestamp=datetime.now(timezone.utc),
                expected_duration=timedelta(hours=8)
            )
            
        except Exception as e:
            self.logger.error(f"Error in mean reversion strategy: {e}")
            return None
    
    async def _breakout_strategy(self, symbol: str, price_data: List[Dict], 
                               market_conditions: Dict) -> Optional[TradingSignal]:
        """Breakout strategy implementation"""
        try:
            params = self.strategies[StrategyType.BREAKOUT]['parameters']
            
            prices = [float(d['close']) for d in price_data]
            volumes = [float(d['volume']) for d in price_data]
            highs = [float(d['high']) for d in price_data]
            lows = [float(d['low']) for d in price_data]
            
            current_price = prices[-1]
            current_volume = volumes[-1]
            
            # Calculate resistance and support levels
            lookback = params['consolidation_period']
            resistance = max(highs[-lookback:])
            support = min(lows[-lookback:])
            
            # Volume confirmation
            avg_volume = np.mean(volumes[-20:])
            volume_ratio = current_volume / avg_volume
            
            # Breakout conditions
            upward_breakout = (
                current_price > resistance * (1 + params['price_threshold']) and
                volume_ratio > params['volume_threshold']
            )
            
            downward_breakout = (
                current_price < support * (1 - params['price_threshold']) and
                volume_ratio > params['volume_threshold']
            )
            
            if not (upward_breakout or downward_breakout):
                return None
            
            is_buy = upward_breakout
            
            # Calculate confidence
            confidence = 0.6
            if is_buy:
                confidence += min(0.2, (current_price - resistance) / resistance * 10)
            else:
                confidence += min(0.2, (support - current_price) / support * 10)
            
            confidence += min(0.2, (volume_ratio - 1.5) / 2)
            confidence = max(0.1, min(0.95, confidence))
            
            # Calculate stops and targets
            range_size = resistance - support
            if is_buy:
                stop_loss = resistance * 0.98  # Just below breakout level
                take_profit = current_price + (range_size * 1.5)
            else:
                stop_loss = support * 1.02  # Just above breakdown level
                take_profit = current_price - (range_size * 1.5)
            
            return TradingSignal(
                symbol=symbol,
                strategy_type=StrategyType.BREAKOUT,
                signal_strength=self._determine_signal_strength(confidence),
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_level=self._determine_risk_level(confidence, market_conditions),
                position_size=self._calculate_position_size(confidence, stop_loss, current_price),
                reasoning=f"{'Upward' if is_buy else 'Downward'} breakout with {volume_ratio:.1f}x volume",
                indicators={'resistance': resistance, 'support': support, 'volume_ratio': volume_ratio},
                timestamp=datetime.now(timezone.utc),
                expected_duration=timedelta(hours=6)
            )
            
        except Exception as e:
            self.logger.error(f"Error in breakout strategy: {e}")
            return None
    
    async def _scalping_strategy(self, symbol: str, price_data: List[Dict], 
                               market_conditions: Dict) -> Optional[TradingSignal]:
        """Scalping strategy implementation"""
        try:
            params = self.strategies[StrategyType.SCALPING]['parameters']
            
            # Only scalp in high volatility, high volume conditions
            if market_conditions.get('volatility', 0) < 0.2:
                return None
            
            prices = [float(d['close']) for d in price_data]
            current_price = prices[-1]
            
            # Quick momentum check
            short_momentum = (prices[-1] - prices[-3]) / prices[-3] if len(prices) >= 3 else 0
            
            if abs(short_momentum) < 0.005:  # Minimum movement for scalping
                return None
            
            is_buy = short_momentum > 0
            
            # Tight risk management for scalping
            profit_target = params['quick_profit_target']
            stop_loss_pct = params['tight_stop_loss']
            
            if is_buy:
                take_profit = current_price * (1 + profit_target)
                stop_loss = current_price * (1 - stop_loss_pct)
            else:
                take_profit = current_price * (1 - profit_target)
                stop_loss = current_price * (1 + stop_loss_pct)
            
            confidence = 0.7 + min(0.2, abs(short_momentum) * 100)
            
            return TradingSignal(
                symbol=symbol,
                strategy_type=StrategyType.SCALPING,
                signal_strength=SignalStrength.MODERATE,
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_level=RiskLevel.HIGH,
                position_size=0.02,  # Small size for scalping
                reasoning=f"Scalping opportunity: {short_momentum:.3%} short-term momentum",
                indicators={'short_momentum': short_momentum},
                timestamp=datetime.now(timezone.utc),
                expected_duration=timedelta(minutes=5)
            )
            
        except Exception as e:
            self.logger.error(f"Error in scalping strategy: {e}")
            return None
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            sma = np.mean(prices)
            std = np.std(prices)
        else:
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return upper_band, lower_band
    
    def _calculate_atr(self, price_data: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(price_data) < period:
            return 0.02  # Default ATR
        
        true_ranges = []
        for i in range(1, len(price_data)):
            high = float(price_data[i]['high'])
            low = float(price_data[i]['low'])
            prev_close = float(price_data[i-1]['close'])
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return np.mean(true_ranges[-period:]) if true_ranges else 0.02
    
    def _determine_signal_strength(self, confidence: float) -> SignalStrength:
        """Determine signal strength based on confidence"""
        if confidence >= 0.85:
            return SignalStrength.VERY_STRONG
        elif confidence >= 0.75:
            return SignalStrength.STRONG
        elif confidence >= 0.65:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _determine_risk_level(self, confidence: float, market_conditions: Dict) -> RiskLevel:
        """Determine risk level"""
        volatility = market_conditions.get('volatility', 0.2)
        
        if volatility > 0.35 or confidence < 0.6:
            return RiskLevel.HIGH
        elif volatility > 0.25 or confidence < 0.7:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _calculate_position_size(self, confidence: float, stop_loss: float, entry_price: float) -> float:
        """Calculate position size based on risk management"""
        # Risk per trade (1-2% of portfolio)
        risk_per_trade = 0.01 + (confidence * 0.01)
        
        # Calculate position size based on stop loss distance
        stop_distance = abs(entry_price - stop_loss) / entry_price
        
        if stop_distance == 0:
            return 0.01
        
        position_size = risk_per_trade / stop_distance
        
        # Cap position size
        return min(position_size, self.max_position_size)
    
    def _adjust_signal_for_performance(self, signal: TradingSignal) -> TradingSignal:
        """Adjust signal based on strategy performance"""
        try:
            performance = self.strategy_performance[signal.strategy_type]
            
            # Adjust confidence based on historical performance
            if performance.total_trades > 10:
                performance_factor = performance.win_rate
                signal.confidence *= (0.7 + (performance_factor * 0.6))
            
            # Adjust position size based on recent performance
            if performance.profit_factor < 1.0:
                signal.position_size *= self.risk_adjustment_factor
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error adjusting signal for performance: {e}")
            return signal
    
    def _filter_and_rank_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Filter and rank signals by confidence and strategy performance"""
        # Remove duplicate symbols (keep highest confidence)
        symbol_signals = {}
        for signal in signals:
            if signal.symbol not in symbol_signals or signal.confidence > symbol_signals[signal.symbol].confidence:
                symbol_signals[signal.symbol] = signal
        
        # Convert back to list and sort by confidence
        filtered_signals = list(symbol_signals.values())
        filtered_signals.sort(key=lambda s: s.confidence, reverse=True)
        
        # Limit to top signals to avoid overtrading
        return filtered_signals[:10]
    
    async def _store_signal_memory(self, signal: TradingSignal, similar_experiences: List):
        """Store signal in memory"""
        content = f"Strategy signal: {signal.strategy_type.value} for {signal.symbol} at ${signal.entry_price:.2f} with {signal.confidence:.2%} confidence"
        
        metadata = {
            'symbol': signal.symbol,
            'strategy_type': signal.strategy_type.value,
            'signal_strength': signal.signal_strength.value,
            'confidence': signal.confidence,
            'entry_price': signal.entry_price,
            'risk_level': signal.risk_level.value,
            'position_size': signal.position_size,
            'similar_experiences_count': len(similar_experiences)
        }
        
        self.store_memory(content, "strategy_signal", metadata)
    
    async def record_strategy_outcome(self, symbol: str, strategy_type: StrategyType, 
                                    success: bool, profit_loss: float):
        """Record outcome of a strategy signal"""
        try:
            # Update strategy performance
            if strategy_type not in self.strategy_performance:
                self.strategy_performance[strategy_type] = StrategyPerformance(
                    strategy_type=strategy_type,
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    avg_profit=0.0,
                    avg_loss=0.0,
                    profit_factor=1.0,
                    max_drawdown=0.0,
                    sharpe_ratio=0.0
                )
            
            perf = self.strategy_performance[strategy_type]
            perf.total_trades += 1
            
            if success:
                perf.winning_trades += 1
                perf.avg_profit = ((perf.avg_profit * (perf.winning_trades - 1)) + profit_loss) / perf.winning_trades
            else:
                perf.losing_trades += 1
                perf.avg_loss = ((perf.avg_loss * (perf.losing_trades - 1)) + abs(profit_loss)) / perf.losing_trades
            
            perf.win_rate = perf.winning_trades / perf.total_trades
            perf.profit_factor = perf.avg_profit / perf.avg_loss if perf.avg_loss > 0 else 1.0
            
            # Learn from outcome
            decision = f"Strategy signal: {strategy_type.value} for {symbol}"
            outcome = f"Result: {'profit' if success else 'loss'} of ${profit_loss:.2f}"
            
            self.learn_from_outcome(decision, outcome, success, profit_loss)
            
            # Store performance update in memory
            content = f"Strategy performance update: {strategy_type.value} now has {perf.win_rate:.2%} win rate over {perf.total_trades} trades"
            
            metadata = {
                'strategy_type': strategy_type.value,
                'total_trades': perf.total_trades,
                'winning_trades': perf.winning_trades,
                'losing_trades': perf.losing_trades,
                'win_rate': perf.win_rate,
                'avg_profit': perf.avg_profit,
                'avg_loss': perf.avg_loss,
                'profit_factor': perf.profit_factor
            }
            
            self.store_memory(content, "strategy_performance", metadata)
            
            # Remove from active signals
            signal_key = f"{symbol}_{strategy_type.value}"
            if signal_key in self.active_signals:
                del self.active_signals[signal_key]
            
            self.logger.info(f"Recorded {strategy_type.value} outcome for {symbol}: {'SUCCESS' if success else 'FAILURE'} ${profit_loss:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error recording strategy outcome: {e}")
    
    async def get_strategy_overview(self) -> Dict:
        """Get comprehensive strategy overview"""
        return {
            'agent_status': self.get_agent_state(),
            'strategy_performance': {
                strategy_type.value: {
                    'total_trades': perf.total_trades,
                    'win_rate': perf.win_rate,
                    'profit_factor': perf.profit_factor,
                    'avg_profit': perf.avg_profit,
                    'avg_loss': perf.avg_loss
                }
                for strategy_type, perf in self.strategy_performance.items()
            },
            'active_signals': {
                key: {
                    'symbol': signal.symbol,
                    'strategy': signal.strategy_type.value,
                    'confidence': signal.confidence,
                    'risk_level': signal.risk_level.value,
                    'age_minutes': (datetime.now(timezone.utc) - signal.timestamp).total_seconds() / 60
                }
                for key, signal in self.active_signals.items()
            },
            'strategy_configs': {
                strategy_type.value: config
                for strategy_type, config in self.strategies.items()
            }
        }
    
    async def process(self):
        """Main strategy agent processing loop"""
        while self.is_active:
            try:
                # Get market conditions
                market_conditions = await self.analyze_market_conditions()
                
                # Define watchlist (this would come from configuration or other agents)
                watchlist = ["AAPL", "MSFT", "TSLA", "NVDA", "SPY", "QQQ", "IWM"]
                
                # Generate signals
                signals = await self.generate_signals(watchlist)
                
                if signals:
                    self.update_status(f"Generated {len(signals)} signals")
                    
                    # Log top signals
                    for signal in signals[:3]:
                        self.logger.info(f"Top signal: {signal.symbol} {signal.strategy_type.value} {signal.confidence:.2%}")
                
                # Clean up old active signals
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
                expired_signals = [
                    key for key, signal in self.active_signals.items()
                    if signal.timestamp < cutoff_time
                ]
                
                for key in expired_signals:
                    del self.active_signals[key]
                
                # Wait before next cycle
                await asyncio.sleep(600)  # 10 minutes
                
            except Exception as e:
                self.logger.error(f"Error in strategy agent main loop: {e}")
                await asyncio.sleep(60)

# Example usage
if __name__ == "__main__":
    async def main():
        agent = StrategyAgent()
        await agent.start()
        
        # Test signal generation
        signals = await agent.generate_signals(["AAPL", "MSFT"])
        
        for signal in signals:
            print(f"\nStrategy Signal:")
            print(f"  Symbol: {signal.symbol}")
            print(f"  Strategy: {signal.strategy_type.value}")
            print(f"  Strength: {signal.signal_strength.value}")
            print(f"  Confidence: {signal.confidence:.2%}")
            print(f"  Entry: ${signal.entry_price:.2f}")
            print(f"  Stop: ${signal.stop_loss:.2f}")
            print(f"  Target: ${signal.take_profit:.2f}")
            print(f"  Risk: {signal.risk_level.value}")
            print(f"  Size: {signal.position_size:.3f}")
            print(f"  Reasoning: {signal.reasoning}")
        
        await agent.stop()
    
    asyncio.run(main())
