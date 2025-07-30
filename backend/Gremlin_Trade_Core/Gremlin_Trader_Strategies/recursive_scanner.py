#!/usr/bin/env python3
"""
Recursive Scanner Strategy - Multi-timeframe penny stock scanning
Implements the recursive scanning strategy defined in trade_strategy.config
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
    recursive_scan, run_scanner, get_live_penny_stocks,
    embed_text, package_embedding
)

# Set up logging
strategy_logger = setup_module_logger("strategy", "recursive_scanner")

class RecursiveScannerStrategy:
    """
    Recursive scanner strategy for penny stock detection
    Implements multi-timeframe analysis with hierarchical refinement
    """
    
    def __init__(self):
        self.config = CFG.get("strategy", {}).get("gremlin_scanner", {})
        self.recursive_config = self.config.get("recursive_scanning", {})
        self.signal_filters = self.config.get("signal_filters", {})
        self.scanner_criteria = self.config.get("scanner_criteria", {})
        self.active_scans = {}
        self.refinement_stages = []
        
        # Initialize refinement stages from config
        recursive_features = CFG.get("strategy", {}).get("recursive_features", {})
        hierarchical_config = recursive_features.get("hierarchical_refinement", {})
        
        if hierarchical_config.get("enabled", True):
            self.refinement_stages = hierarchical_config.get("stages", [])
        
        strategy_logger.info("Recursive scanner strategy initialized")
    
    async def run_recursive_scan(self, symbols: List[str] = None, max_depth: int = None) -> List[Dict[str, Any]]:
        """
        Run recursive scanning with multiple timeframes and refinement stages
        """
        try:
            # Use config defaults if not provided
            if symbols is None:
                symbols = ["GPRO", "IXHL", "SAVA", "BBIG", "PROG", "ATER", "MULN", "BBBY"]
            
            if max_depth is None:
                max_depth = self.recursive_config.get("max_depth", 3)
            
            strategy_logger.info(f"Starting recursive scan - {len(symbols)} symbols, depth {max_depth}")
            
            # Get timeframes from config
            timeframes = self.recursive_config.get("timeframe_cascade", ["1min", "5min", "15min", "1h"])
            
            # Stage 1: Initial broad scan
            stage1_results = await self._run_initial_scan(symbols)
            strategy_logger.info(f"Stage 1 complete: {len(stage1_results)} candidates")
            
            # Stage 2: Recursive refinement
            stage2_results = await self._run_recursive_refinement(stage1_results, timeframes, max_depth)
            strategy_logger.info(f"Stage 2 complete: {len(stage2_results)} refined candidates")
            
            # Stage 3: Final filtering with memory guidance
            final_results = await self._run_final_filtering(stage2_results)
            strategy_logger.info(f"Final scan complete: {len(final_results)} qualified signals")
            
            return final_results
            
        except Exception as e:
            strategy_logger.error(f"Error in recursive scan: {e}")
            return []
    
    async def _run_initial_scan(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Run initial broad scan to identify candidates"""
        try:
            # Use the first refinement stage criteria if available
            if self.refinement_stages:
                criteria = self.refinement_stages[0].get("criteria", {})
            else:
                criteria = self.scanner_criteria
            
            # Run scanner with initial criteria
            results = run_scanner(symbols)
            
            # Filter by initial criteria
            filtered_results = []
            for result in results:
                if self._meets_initial_criteria(result, criteria):
                    result["stage"] = "initial"
                    result["timestamp"] = datetime.now(timezone.utc).isoformat()
                    filtered_results.append(result)
            
            return filtered_results
            
        except Exception as e:
            strategy_logger.error(f"Error in initial scan: {e}")
            return []
    
    async def _run_recursive_refinement(self, candidates: List[Dict[str, Any]], 
                                       timeframes: List[str], max_depth: int) -> List[Dict[str, Any]]:
        """Run recursive refinement across multiple timeframes"""
        try:
            refined_results = []
            
            for candidate in candidates:
                symbol = candidate.get("symbol")
                if not symbol:
                    continue
                
                # Run recursive scan on single symbol across timeframes
                recursive_hits = recursive_scan([symbol], timeframes[:max_depth])
                
                # Combine with original candidate data
                for hit in recursive_hits:
                    combined_result = {**candidate, **hit}
                    combined_result["stage"] = "recursive"
                    combined_result["refinement_depth"] = len(timeframes[:max_depth])
                    
                    # Apply signal filters
                    if self._apply_signal_filters(combined_result):
                        refined_results.append(combined_result)
            
            return refined_results
            
        except Exception as e:
            strategy_logger.error(f"Error in recursive refinement: {e}")
            return candidates  # Return original candidates if refinement fails
    
    async def _run_final_filtering(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run final filtering with memory guidance and pattern recognition"""
        try:
            final_results = []
            
            # Check if memory-guided filtering is enabled
            memory_features = CFG.get("strategy", {}).get("recursive_features", {}).get("memory_guided_filtering", {})
            memory_enabled = memory_features.get("enabled", True)
            
            for candidate in candidates:
                # Apply final stage criteria if available
                if len(self.refinement_stages) > 2:
                    final_criteria = self.refinement_stages[2].get("criteria", {})
                    if not self._meets_final_criteria(candidate, final_criteria):
                        continue
                
                # Memory-guided filtering
                if memory_enabled:
                    similarity_score = await self._calculate_memory_similarity(candidate)
                    candidate["memory_similarity"] = similarity_score
                    
                    similarity_threshold = memory_features.get("similarity_threshold", 0.8)
                    if similarity_score < similarity_threshold:
                        continue
                
                # Calculate final confidence score
                candidate["final_confidence"] = self._calculate_final_confidence(candidate)
                candidate["stage"] = "final"
                
                final_results.append(candidate)
            
            # Sort by confidence
            final_results.sort(key=lambda x: x.get("final_confidence", 0), reverse=True)
            
            return final_results
            
        except Exception as e:
            strategy_logger.error(f"Error in final filtering: {e}")
            return candidates
    
    def _meets_initial_criteria(self, result: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if result meets initial scan criteria"""
        try:
            # Check rotation
            rotation = result.get("rotation", 0)
            min_rotation = criteria.get("rotation", self.scanner_criteria.get("rotation_over", 2.0))
            if rotation < min_rotation:
                return False
            
            # Check volume
            volume = result.get("volume", 0)
            min_volume = criteria.get("volume", self.scanner_criteria.get("volume_over", 1000000))
            if volume < min_volume:
                return False
            
            # Check price
            price = result.get("price", 0)
            max_price = self.scanner_criteria.get("price_under", 10.0)
            if price > max_price:
                return False
            
            return True
            
        except Exception as e:
            strategy_logger.error(f"Error checking initial criteria: {e}")
            return False
    
    def _apply_signal_filters(self, result: Dict[str, Any]) -> bool:
        """Apply signal filters from configuration"""
        try:
            signals = result.get("signal", [])
            
            # Check for required signal types
            if self.signal_filters.get("ema_cross", True):
                if not any("ema" in str(signal).lower() for signal in signals):
                    return False
            
            if self.signal_filters.get("vwap_break", True):
                if not any("vwap" in str(signal).lower() for signal in signals):
                    # Allow if other strong signals are present
                    if not any("volume_spike" in str(signal).lower() for signal in signals):
                        return False
            
            if self.signal_filters.get("volume_spike", True):
                volume_ratio = result.get("volume_ratio", 1.0)
                if volume_ratio < 2.0:  # Require at least 2x volume
                    return False
            
            return True
            
        except Exception as e:
            strategy_logger.error(f"Error applying signal filters: {e}")
            return True  # Allow through if filter check fails
    
    def _meets_final_criteria(self, result: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if result meets final filtering criteria"""
        try:
            # Pattern confirmation
            if criteria.get("pattern_confirmation", True):
                signals = result.get("signal", [])
                if len(signals) < 2:  # Require multiple confirming signals
                    return False
            
            # Sentiment check (if available)
            if criteria.get("sentiment_positive", True):
                sentiment = result.get("sentiment_score", 0.5)
                if sentiment < 0.5:
                    return False
            
            return True
            
        except Exception as e:
            strategy_logger.error(f"Error checking final criteria: {e}")
            return True
    
    async def _calculate_memory_similarity(self, candidate: Dict[str, Any]) -> float:
        """Calculate similarity with historical patterns in memory"""
        try:
            # Create text summary for similarity comparison
            symbol = candidate.get("symbol", "")
            signals = candidate.get("signal", [])
            price = candidate.get("price", 0)
            
            summary = f"{symbol} signals: {', '.join(signals)} at ${price:.2f}"
            
            # Generate embedding
            vector = embed_text(summary)
            
            # TODO: Query memory store for similar patterns
            # For now, return a mock similarity score based on signal strength
            signal_count = len(signals)
            confidence = candidate.get("confidence", 0.5)
            
            # Simple heuristic for similarity
            similarity = min(1.0, (signal_count * 0.2) + confidence)
            
            return similarity
            
        except Exception as e:
            strategy_logger.error(f"Error calculating memory similarity: {e}")
            return 0.5  # Default similarity
    
    def _calculate_final_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate final confidence score for the signal"""
        try:
            confidence = 0.0
            
            # Base confidence from signal generation
            base_confidence = result.get("confidence", 0.5)
            confidence += base_confidence * 0.4
            
            # Signal count bonus
            signal_count = len(result.get("signal", []))
            confidence += min(0.3, signal_count * 0.1)
            
            # Volume factor
            volume_ratio = result.get("volume_ratio", 1.0)
            confidence += min(0.2, (volume_ratio - 1.0) * 0.1)
            
            # Memory similarity factor
            memory_similarity = result.get("memory_similarity", 0.5)
            confidence += memory_similarity * 0.1
            
            return min(1.0, confidence)
            
        except Exception as e:
            strategy_logger.error(f"Error calculating final confidence: {e}")
            return 0.5

# Global strategy instance
recursive_scanner = RecursiveScannerStrategy()

# Export functions for use by other modules
async def run_recursive_strategy(symbols: List[str] = None, max_depth: int = None) -> List[Dict[str, Any]]:
    """Run the recursive scanner strategy"""
    return await recursive_scanner.run_recursive_scan(symbols, max_depth)

def get_strategy_config() -> Dict[str, Any]:
    """Get strategy configuration"""
    return recursive_scanner.config

if __name__ == "__main__":
    # Test the strategy
    import asyncio
    
    async def test_strategy():
        results = await run_recursive_strategy(["GPRO", "IXHL"])
        print(f"Strategy test complete: {len(results)} results")
        for result in results:
            print(f"  {result.get('symbol')}: {result.get('final_confidence', 0):.2f} confidence")
    
    asyncio.run(test_strategy())
