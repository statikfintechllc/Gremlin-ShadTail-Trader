#!/usr/bin/env python3

# ─────────────────────────────────────────────────────────────
# ⚠️ GremlinGPT Fair Use Only | Commercial Use Requires License
# Built under the GremlinGPT Dual License v1.0
# © 2025 StatikFintechLLC / AscendAI Project
# Contact: ascend.gremlin@gmail.com
# ─────────────────────────────────────────────────────────────

# GremlinGPT v1.0.3 :: Module Integrity Directive
# This script is a component of the GremlinGPT system, under Alpha expansion.

# Refactored to use centralized imports  
from Gremlin_Trade_Core.globals import (
    # Core imports
    logging, datetime, setup_agent_logging
)

# Use centralized logging
logger = setup_agent_logging("tax_estimator")

DEFAULT_TAX_RATE = 0.15  # Can be made dynamic via config or input


def estimate_tax(position, tax_rate=None, log=True, persist=False):
    """
    Estimate tax for a single position.
    :param position: dict with 'symbol', 'price', 'shares', optional 'side', 'open_date', etc.
    :param tax_rate: override tax rate (float 0..1), else use DEFAULT_TAX_RATE.
    :param log: if True, log the estimate.
    :param persist: if True, store result for audit/training.
    :return: dict {symbol, shares, price, value, tax, tax_rate, meta}
    """
    try:
        shares = float(position.get("shares", 0))
        price = float(position.get("price", 0))
        symbol = position.get("symbol", "UNKNOWN")
        side = position.get("side", "long")
        open_date = position.get("open_date")
        close_date = position.get("close_date")
        meta = {
            k: v
            for k, v in position.items()
            if k not in {"symbol", "price", "shares", "side", "open_date", "close_date"}
        }

        total_value = shares * price
        rate = float(tax_rate) if tax_rate is not None else DEFAULT_TAX_RATE
        tax = round(total_value * rate, 2)

        result = {
            "symbol": symbol,
            "shares": shares,
            "price": price,
            "value": round(total_value, 2),
            "tax": tax,
            "tax_rate": rate,
            "side": side,
            "open_date": open_date,
            "close_date": close_date,
            "meta": meta,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if log:
            logger.info(
                f"[TAX_ESTIMATE] {symbol}: value=${total_value:.2f}, tax=${tax:.2f} at {rate*100:.1f}%"
            )

        if persist:
            _persist_tax_estimate(result)

        return result

    except Exception as e:
        logger.error(f"[TAX_ESTIMATE] Error for {position}: {e}")
        return {"error": str(e), "position": position}


def estimate_batch(positions, tax_rate=None, log=True, persist=False):
    """
    Estimate taxes for a batch of positions.
    :param positions: list of position dicts
    :return: list of estimate results
    """
    return [
        estimate_tax(pos, tax_rate=tax_rate, log=log, persist=persist)
        for pos in positions
    ]


def _persist_tax_estimate(result):
    """
    Persist a single tax estimate to memory/log for audit/self-training.
    """
    try:
        from Gremlin_Trade_Core.globals import package_embedding, embed_text

        text = f"TAX {result['symbol']} {result['shares']} @ {result['price']} = Tax ${result['tax']} ({result['tax_rate']*100:.1f}%)"
        vector = embed_text(text)
        package_embedding(text=text, vector=vector, meta=result)
        logger.debug(f"[TAX_ESTIMATE] Persisted embedding for {result['symbol']}")
    except Exception as e:
        logger.warning(f"[TAX_ESTIMATE] Persist failed: {e}")


class TaxEstimator:
    """Tax Estimator Agent for trading system"""
    
    def __init__(self):
        from Gremlin_Trade_Core.globals import setup_module_logger
        self.logger = setup_module_logger("financial", "tax_estimator")
        self.name = "TaxEstimator"
        self.initialized = True
        
    def initialize(self):
        """Initialize the tax estimator"""
        try:
            self.logger.info("TaxEstimator initialized")
            return True
        except Exception as e:
            self.logger.error(f"Error initializing TaxEstimator: {e}")
            return False
    
    def process(self, data=None):
        """Process tax calculations"""
        try:
            if data:
                if isinstance(data, list):
                    result = estimate_tax_bulk(data)
                else:
                    result = estimate_tax(data)
                self.logger.info(f"Tax estimation result: {result}")
                return result
            return None
        except Exception as e:
            self.logger.error(f"Error processing tax estimation: {e}")
            return None
    
    def get_status(self):
        """Get agent status"""
        return {
            "name": self.name,
            "initialized": self.initialized,
            "active": True
        }
