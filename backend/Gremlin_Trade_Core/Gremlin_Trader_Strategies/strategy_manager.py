#!/usr/bin/env python3
"""
Strategy Manager - Coordinates all trading strategies
Integrates recursive scanner and penny stock strategies with memory and config
"""

# Import ALL dependencies through globals.py (required)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from Gremlin_Trade_Core.globals import (
    # Core imports
    asyncio, np, pd, datetime, timezone,
    # Type imports
    List, Dict, Any, Optional,
    # Configuration and utilities
    CFG, MEM, logger, setup_module_logger,
    embed_text, package_embedding
)

# Set up logging
strategy_logger = setup_module_logger("strategy", "manager")

class StrategyManager:
    """
    Central strategy manager that coordinates all trading strategies
    """
    
    def __init__(self):
        self.config = CFG.get("strategy", {})
        self.active_strategies = []
        self.performance_metrics = {}
        self.strategy_weights = {}
        
        # Initialize strategy weights from config
        self.strategy_weights = {
            "recursive_scanner": 0.6,
            "penny_stock": 0.4
        }
        
        strategy_logger.info("Strategy manager initialized")
    
    async def run_comprehensive_scan(self, symbols: List[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Run comprehensive scan using all available strategies
        """
        try:
            strategy_logger.info(f"Starting comprehensive scan - limit {limit}")
            
            all_results = []
            
            # Run recursive scanner strategy
            try:
                from .recursive_scanner import run_recursive_strategy
                recursive_results = await run_recursive_strategy(symbols)
                
                # Tag results with strategy source
                for result in recursive_results:
                    result["strategy_source"] = "recursive_scanner"
                    result["strategy_weight"] = self.strategy_weights.get("recursive_scanner", 0.6)
                
                all_results.extend(recursive_results)
                strategy_logger.info(f"Recursive scanner: {len(recursive_results)} results")
                
            except Exception as e:
                strategy_logger.error(f"Error in recursive scanner: {e}")
            
            # Run penny stock strategy
            try:
                from .penny_stock_strategy import scan_penny_stocks
                penny_results = await scan_penny_stocks(limit)
                
                # Tag results with strategy source
                for result in penny_results:
                    result["strategy_source"] = "penny_stock"
                    result["strategy_weight"] = self.strategy_weights.get("penny_stock", 0.4)
                
                all_results.extend(penny_results)
                strategy_logger.info(f"Penny stock strategy: {len(penny_results)} results")
                
            except Exception as e:
                strategy_logger.error(f"Error in penny stock strategy: {e}")
            
            # Combine and rank results
            combined_results = await self._combine_strategy_results(all_results)
            
            # Limit results
            final_results = combined_results[:limit]
            
            strategy_logger.info(f"Comprehensive scan complete: {len(final_results)} final results")
            return final_results
            
        except Exception as e:
            strategy_logger.error(f"Error in comprehensive scan: {e}")
            return []
    
    async def _combine_strategy_results(self, all_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combine results from multiple strategies, removing duplicates and ranking
        """
        try:
            # Group by symbol
            symbol_results = {}
            
            for result in all_results:
                symbol = result.get("symbol")
                if not symbol:
                    continue
                
                if symbol not in symbol_results:
                    symbol_results[symbol] = []
                
                symbol_results[symbol].append(result)
            
            # Combine duplicate symbols
            combined_results = []
            
            for symbol, results in symbol_results.items():
                if len(results) == 1:
                    # Single result, use as is
                    combined_results.append(results[0])
                else:
                    # Multiple results, combine them
                    combined_result = await self._merge_symbol_results(results)
                    combined_results.append(combined_result)
            
            # Calculate final scores and sort
            for result in combined_results:
                result["final_strategy_score"] = self._calculate_final_strategy_score(result)
            
            # Sort by final score
            combined_results.sort(key=lambda x: x.get("final_strategy_score", 0), reverse=True)
            
            return combined_results
            
        except Exception as e:
            strategy_logger.error(f"Error combining strategy results: {e}")
            return all_results
    
    async def _merge_symbol_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple results for the same symbol
        """
        try:
            # Start with the first result as base
            merged = results[0].copy()
            
            # Combine strategy sources
            sources = [r.get("strategy_source", "unknown") for r in results]
            merged["strategy_sources"] = list(set(sources))
            
            # Combine signals
            all_signals = []
            for result in results:
                signals = result.get("signal", [])
                all_signals.extend(signals)
            merged["signal"] = list(set(all_signals))  # Remove duplicates
            
            # Use highest confidence
            confidences = [r.get("confidence", 0) for r in results]
            merged["confidence"] = max(confidences) if confidences else 0
            
            # Combine strategy-specific scores
            penny_scores = [r.get("penny_score", 0) for r in results if r.get("strategy_source") == "penny_stock"]
            if penny_scores:
                merged["penny_score"] = max(penny_scores)
            
            final_confidences = [r.get("final_confidence", 0) for r in results if r.get("strategy_source") == "recursive_scanner"]
            if final_confidences:
                merged["final_confidence"] = max(final_confidences)
            
            # Calculate combined weight
            weights = [r.get("strategy_weight", 0) for r in results]
            merged["combined_weight"] = sum(weights)
            
            merged["merged_from"] = len(results)
            merged["merge_timestamp"] = datetime.now(timezone.utc).isoformat()
            
            return merged
            
        except Exception as e:
            strategy_logger.error(f"Error merging symbol results: {e}")
            return results[0] if results else {}
    
    def _calculate_final_strategy_score(self, result: Dict[str, Any]) -> float:
        """
        Calculate final strategy score considering all factors
        """
        try:
            score = 0.0
            
            # Base confidence
            confidence = result.get("confidence", 0.5)
            score += confidence * 0.3
            
            # Strategy-specific scores
            penny_score = result.get("penny_score", 0)
            final_confidence = result.get("final_confidence", 0)
            
            # Weight strategy scores
            if penny_score > 0:
                weight = self.strategy_weights.get("penny_stock", 0.4)
                score += penny_score * weight
            
            if final_confidence > 0:
                weight = self.strategy_weights.get("recursive_scanner", 0.6)
                score += final_confidence * weight
            
            # Signal strength bonus
            signals = result.get("signal", [])
            signal_bonus = min(0.2, len(signals) * 0.05)
            score += signal_bonus
            
            # Multiple strategy bonus
            sources = result.get("strategy_sources", [])
            if len(sources) > 1:
                score += 0.1  # Bonus for multiple strategy confirmation
            
            # Volume factor
            volume = result.get("volume", 0)
            if volume > 5000000:
                score += 0.1
            elif volume > 1000000:
                score += 0.05
            
            # Price momentum factor
            up_pct = result.get("up_pct", 0)
            momentum_bonus = min(0.15, up_pct / 100)
            score += momentum_bonus
            
            return min(1.0, score)
            
        except Exception as e:
            strategy_logger.error(f"Error calculating final strategy score: {e}")
            return 0.5
    
    async def get_strategy_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics for all strategies
        """
        try:
            performance = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "strategies": {},
                "overall": {}
            }
            
            # Get individual strategy performance
            for strategy_name in self.strategy_weights.keys():
                performance["strategies"][strategy_name] = {
                    "weight": self.strategy_weights[strategy_name],
                    "active": True,
                    "last_run": datetime.now(timezone.utc).isoformat()
                }
            
            # Overall performance
            performance["overall"] = {
                "total_strategies": len(self.strategy_weights),
                "combined_weight": sum(self.strategy_weights.values()),
                "status": "active"
            }
            
            return performance
            
        except Exception as e:
            strategy_logger.error(f"Error getting strategy performance: {e}")
            return {}
    
    def update_strategy_weights(self, new_weights: Dict[str, float]):
        """
        Update strategy weights based on performance
        """
        try:
            # Validate weights
            total_weight = sum(new_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                strategy_logger.warning(f"Strategy weights don't sum to 1.0: {total_weight}")
            
            self.strategy_weights.update(new_weights)
            strategy_logger.info(f"Strategy weights updated: {self.strategy_weights}")
            
        except Exception as e:
            strategy_logger.error(f"Error updating strategy weights: {e}")
    
    async def backtest_strategies(self, days: int = 30) -> Dict[str, Any]:
        """
        Run backtesting on strategies (mock implementation)
        """
        try:
            strategy_logger.info(f"Running strategy backtest for {days} days")
            
            # Mock backtest results
            backtest_results = {
                "period_days": days,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "strategies": {
                    "recursive_scanner": {
                        "total_signals": 1247,
                        "profitable_signals": 892,
                        "win_rate": 0.715,
                        "avg_return": 0.127,
                        "max_drawdown": 0.089,
                        "sharpe_ratio": 1.34
                    },
                    "penny_stock": {
                        "total_signals": 834,
                        "profitable_signals": 567,
                        "win_rate": 0.680,
                        "avg_return": 0.156,
                        "max_drawdown": 0.143,
                        "sharpe_ratio": 1.18
                    }
                },
                "combined": {
                    "total_signals": 2081,
                    "profitable_signals": 1459,
                    "win_rate": 0.701,
                    "avg_return": 0.139,
                    "max_drawdown": 0.098,
                    "sharpe_ratio": 1.28
                }
            }
            
            return backtest_results
            
        except Exception as e:
            strategy_logger.error(f"Error in strategy backtesting: {e}")
            return {}

# Global strategy manager instance
strategy_manager = StrategyManager()

# Export functions for use by other modules
async def run_all_strategies(symbols: List[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Run all available strategies"""
    return await strategy_manager.run_comprehensive_scan(symbols, limit)

async def get_performance_metrics() -> Dict[str, Any]:
    """Get strategy performance metrics"""
    return await strategy_manager.get_strategy_performance()

def update_weights(new_weights: Dict[str, float]):
    """Update strategy weights"""
    strategy_manager.update_strategy_weights(new_weights)

async def run_backtest(days: int = 30) -> Dict[str, Any]:
    """Run strategy backtesting"""
    return await strategy_manager.backtest_strategies(days)

if __name__ == "__main__":
    # Test the strategy manager
    import asyncio
    
    async def test_strategy_manager():
        results = await run_all_strategies(limit=20)
        print(f"Strategy manager test complete: {len(results)} results")
        for result in results:
            symbol = result.get('symbol')
            score = result.get('final_strategy_score', 0)
            sources = result.get('strategy_sources', [])
            print(f"  {symbol}: {score:.3f} score from {sources}")
        
        # Test performance
        performance = await get_performance_metrics()
        print(f"\nPerformance: {performance}")
    
    asyncio.run(test_strategy_manager())
