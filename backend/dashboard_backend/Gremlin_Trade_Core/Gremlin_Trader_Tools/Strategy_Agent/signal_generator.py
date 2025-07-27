#!/usr/bin/env python3

# ─────────────────────────────────────────────────────────────
# © 2025 StatikFintechLLC
# Contact: ascend.gremlin@gmail.com
# ─────────────────────────────────────────────────────────────

# GremlinGPT v1.0.3 :: Module Integrity Directive
# This script is a component of the GremlinGPT system, under Alpha expansion.

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for centralized imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dashboard_backend.Gremlin_Trade_Core.globals import (
    apply_signal_rules, 
    get_live_penny_stocks,
    package_embedding,
    embed_text,
    setup_module_logger,
    CFG, MEM, recursive_scan
)

# Initialize module-specific logger
logger = setup_module_logger("trading_core", "signal_generator")

WATERMARK = "source:GremlinGPT"
ORIGIN = "signal_generator"

# --- Main Signal Generator (API-facing) ---

def generate_signals(limit=50, embed=True):
    """
    Generate and return actionable trading signals, persist embeddings, and support dashboard API.
    :param limit: max number of signals to return
    :param embed: if True, store signals as vector embeddings in memory
    :return: list of signal dicts
    """
    try:
        # Get strategy configuration
        strategy_config = CFG.get("strategy", {})
        scanner_config = CFG.get("agents", {}).get("scanner", {})
        
        # Use recursive scanning if enabled
        if strategy_config.get("recursive_scanning", {}).get("enabled", True):
            symbols = ["GPRO", "IXHL", "SAVA", "BBIG", "PROG", "ATER"]  # Example symbols
            timeframes = scanner_config.get("timeframes", ["1min", "5min", "15min"])
            
            # Run recursive scan
            raw_signals = recursive_scan(symbols, timeframes)
            
            # Process recursive signals
            signals = []
            for signal in raw_signals:
                processed_signal = process_recursive_signal(signal)
                if processed_signal:
                    signals.append(processed_signal)
                    
                    if embed:
                        store_signal_embedding(processed_signal)
                    
                    if len(signals) >= limit:
                        break
        else:
            # Use traditional scanning
            stocks = get_live_penny_stocks()
            signals = []
            n = 0

            for stock in stocks:
                signal = apply_signal_rules(stock)
                if signal:
                    n += 1
                    result = {**stock, **signal}
                    signals.append(result)

                    summary = (
                        f"{stock['symbol']} @ ${stock['price']:.2f} | "
                        f"Signal: {', '.join(signal['signal'])}"
                    )

                    if embed:
                        vector = embed_text(summary)
                        package_embedding(
                            text=summary,
                            vector=vector,
                            meta={
                                "symbol": stock["symbol"],
                                "signal": signal["signal"],
                                "price": stock["price"],
                                "ema": stock.get("ema"),
                                "vwap": stock.get("vwap"),
                                "rsi": stock.get("rsi"),
                                "volume": stock.get("volume"),
                                "timestamp": datetime.utcnow().isoformat(),
                                "origin": ORIGIN,
                                "watermark": WATERMARK,
                            },
                        )
                        inject_watermark(origin=ORIGIN)

                    logger.info(f"[SIGNAL] {summary}")

                    if n >= limit:
                        break

        logger.info(f"[SIGNAL_GENERATOR] Generated {len(signals)} signals.")
        return signals

    except Exception as e:
        logger.error(f"[SIGNAL_GENERATOR] Error: {e}")
        return []

def process_recursive_signal(signal):
    """Process signal from recursive scanning"""
    try:
        # Extract key information
        processed = {
            "symbol": signal.get("symbol"),
            "price": signal.get("price"),
            "volume": signal.get("volume"),
            "rotation": signal.get("rotation"),
            "up_pct": signal.get("up_pct"),
            "signal": signal.get("signal", []),
            "confidence": signal.get("confidence", 0.5),
            "timeframe": signal.get("timeframe"),
            "timestamp": signal.get("timestamp", datetime.utcnow().isoformat()),
            "ema": signal.get("ema", {}),
            "vwap": signal.get("vwap"),
            "rsi": signal.get("rsi"),
            "risk_score": calculate_risk_score(signal),
            "strategy_score": calculate_strategy_score(signal)
        }
        
        # Enhanced signal analysis
        processed["pattern_type"] = identify_pattern_type(signal)
        processed["momentum_score"] = calculate_momentum_score(signal)
        processed["spoof_probability"] = detect_spoof_probability(signal)
        
        return processed
        
    except Exception as e:
        logger.error(f"Error processing recursive signal: {e}")
        return None

def calculate_risk_score(signal):
    """Calculate risk score for signal"""
    try:
        risk_score = 0.0
        
        price = signal.get("price", 0)
        volume = signal.get("volume", 0)
        confidence = signal.get("confidence", 0.5)
        
        # Price risk
        if price > 8.0:
            risk_score += 0.3
        elif price < 0.5:
            risk_score += 0.4
        
        # Volume risk
        if volume < 500000:
            risk_score += 0.3
        
        # Confidence risk
        if confidence < 0.3:
            risk_score += 0.4
        
        return min(risk_score, 1.0)
        
    except Exception as e:
        logger.error(f"Error calculating risk score: {e}")
        return 0.5

def calculate_strategy_score(signal):
    """Calculate strategy score for signal"""
    try:
        strategy_score = 0.0
        
        signals = signal.get("signal", [])
        
        # EMA cross bonus
        if "ema_cross_bullish" in signals:
            strategy_score += 0.3
        
        # VWAP break bonus
        if "vwap_break" in signals:
            strategy_score += 0.2
        
        # Volume spike bonus
        if "volume_spike" in signals:
            strategy_score += 0.3
        
        # Confidence bonus
        confidence = signal.get("confidence", 0.5)
        strategy_score += confidence * 0.2
        
        return min(strategy_score, 1.0)
        
    except Exception as e:
        logger.error(f"Error calculating strategy score: {e}")
        return 0.5

def identify_pattern_type(signal):
    """Identify the pattern type of the signal"""
    try:
        signals = signal.get("signal", [])
        
        if "ema_cross_bullish" in signals and "volume_spike" in signals:
            return "momentum_breakout"
        elif "vwap_break" in signals:
            return "vwap_breakout"
        elif "volume_spike" in signals:
            return "volume_surge"
        elif "ema_cross_bullish" in signals:
            return "trend_following"
        else:
            return "consolidation"
            
    except Exception as e:
        logger.error(f"Error identifying pattern type: {e}")
        return "unknown"

def calculate_momentum_score(signal):
    """Calculate momentum score"""
    try:
        momentum_score = 0.0
        
        up_pct = signal.get("up_pct", 0)
        volume = signal.get("volume", 0)
        rotation = signal.get("rotation", 0)
        
        # Price momentum
        if up_pct > 20:
            momentum_score += 0.4
        elif up_pct > 10:
            momentum_score += 0.3
        elif up_pct > 5:
            momentum_score += 0.2
        
        # Volume momentum
        if volume > 2000000:
            momentum_score += 0.3
        elif volume > 1000000:
            momentum_score += 0.2
        
        # Rotation momentum
        if rotation > 5.0:
            momentum_score += 0.3
        elif rotation > 2.0:
            momentum_score += 0.2
        
        return min(momentum_score, 1.0)
        
    except Exception as e:
        logger.error(f"Error calculating momentum score: {e}")
        return 0.5

def detect_spoof_probability(signal):
    """Detect probability of spoofing"""
    try:
        # This would integrate with Level II data in a real implementation
        spoof_score = 0.0
        
        volume = signal.get("volume", 0)
        price = signal.get("price", 0)
        up_pct = signal.get("up_pct", 0)
        
        # High volume with low price movement could indicate spoofing
        if volume > 3000000 and up_pct < 5:
            spoof_score += 0.3
        
        # Rapid price changes without fundamentals
        if up_pct > 50 and price < 2.0:
            spoof_score += 0.4
        
        # Penny stock manipulation patterns
        if price < 1.0 and volume > 5000000:
            spoof_score += 0.3
        
        return min(spoof_score, 1.0)
        
    except Exception as e:
        logger.error(f"Error detecting spoof probability: {e}")
        return 0.0

def store_signal_embedding(signal):
    """Store signal as embedding in memory"""
    try:
        # Create comprehensive text summary
        summary = (
            f"{signal['symbol']} {signal['pattern_type']} signal at ${signal['price']:.2f} "
            f"({signal['up_pct']:.1f}% up) with {signal['volume']:,} volume. "
            f"Confidence: {signal['confidence']:.2f}, Risk: {signal['risk_score']:.2f}, "
            f"Strategy: {signal['strategy_score']:.2f}. Signals: {', '.join(signal['signal'])}"
        )
        
        # Generate embedding
        vector = embed_text(summary)
        
        # Package with comprehensive metadata
        package_embedding(
            text=summary,
            vector=vector,
            meta={
                "symbol": signal["symbol"],
                "pattern_type": signal["pattern_type"],
                "signal_types": signal["signal"],
                "price": signal["price"],
                "volume": signal["volume"],
                "confidence": signal["confidence"],
                "risk_score": signal["risk_score"],
                "strategy_score": signal["strategy_score"],
                "momentum_score": signal["momentum_score"],
                "spoof_probability": signal["spoof_probability"],
                "timeframe": signal["timeframe"],
                "timestamp": signal["timestamp"],
                "origin": ORIGIN,
                "watermark": WATERMARK,
            }
        )
        
        logger.debug(f"Stored embedding for {signal['symbol']}")
        
    except Exception as e:
        logger.error(f"Error storing signal embedding: {e}")

def inject_watermark(origin=ORIGIN):
    """Inject watermark for tracking"""
    try:
        text = f"Watermark from {origin} @ {datetime.utcnow().isoformat()}"
        vector = embed_text(text)
        meta = {"origin": origin, "timestamp": datetime.utcnow().isoformat()}
        return package_embedding(text, vector, meta)
    except Exception as e:
        logger.error(f"Error injecting watermark: {e}")

# --- Optional: For self-healing/mutation, dashboard, or agent tasks ---

def get_signal_history(limit=100):
    """
    Return signal embedding history for dashboard/graph.
    """
    try:
        from dashboard_backend.Gremlin_Trade_Memory.embedder import get_all_embeddings

        signals = []
        for emb in get_all_embeddings(limit):
            if emb["meta"].get("origin") == ORIGIN:
                signals.append(emb)
        return signals
    except Exception as e:
        logger.error(f"Error getting signal history: {e}")
        return []

def repair_signal_index():
    """
    Self-repair for embeddings relevant to signals.
    """
    try:
        from dashboard_backend.Gremlin_Trade_Memory.embedder import repair_index

        repair_index()
        logger.info("[SIGNAL_GENERATOR] Signal embedding index repaired.")
    except Exception as e:
        logger.error(f"Error repairing signal index: {e}")

def get_signal_performance_metrics():
    """Get performance metrics for generated signals"""
    try:
        signals = get_signal_history(500)  # Get more for analysis
        
        if not signals:
            return {}
        
        metrics = {
            "total_signals": len(signals),
            "avg_confidence": 0,
            "avg_risk_score": 0,
            "avg_strategy_score": 0,
            "pattern_distribution": {},
            "timeframe_distribution": {}
        }
        
        confidence_sum = 0
        risk_sum = 0
        strategy_sum = 0
        
        for signal in signals:
            meta = signal.get("meta", {})
            
            # Calculate averages
            confidence_sum += meta.get("confidence", 0)
            risk_sum += meta.get("risk_score", 0)
            strategy_sum += meta.get("strategy_score", 0)
            
            # Pattern distribution
            pattern = meta.get("pattern_type", "unknown")
            metrics["pattern_distribution"][pattern] = metrics["pattern_distribution"].get(pattern, 0) + 1
            
            # Timeframe distribution
            timeframe = meta.get("timeframe", "unknown")
            metrics["timeframe_distribution"][timeframe] = metrics["timeframe_distribution"].get(timeframe, 0) + 1
        
        # Calculate averages
        metrics["avg_confidence"] = confidence_sum / len(signals)
        metrics["avg_risk_score"] = risk_sum / len(signals)
        metrics["avg_strategy_score"] = strategy_sum / len(signals)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting signal performance metrics: {e}")
        return {}
