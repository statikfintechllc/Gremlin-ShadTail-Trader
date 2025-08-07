#!/usr/bin/env python3

# Import ALL dependencies through globals.py (required)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from Gremlin_Trade_Core.globals import (
    # Core imports
    os, time, choice, logging, pd, schedule,
    # Trading libraries
    IB, Stock, Contract, ScannerSubscription, MarketOrder, LimitOrder, StopOrder, 
    Trade, Fill, CommissionReport, OrderStatusEvent, PortfolioItem,
    # Configuration
    IBKR_CONFIG, TRADING_PARAMS, SCANNER_PARAMS,
    get_scanner_subscription, setup_agent_logging,
    # Dependencies
    TRADING_LIBS_AVAILABLE, RotatingFileHandler
)

# Use centralized logging
logger = setup_agent_logging(Path(__file__).stem)

if not TRADING_LIBS_AVAILABLE:
    raise ImportError("Trading libraries not available - cannot run IBKR trader")

### ─── CONFIG ───────────────────────────────────────────────────────────────
# Use centralized configuration from globals
IB_HOST       = IBKR_CONFIG['HOST']
IB_PORT       = IBKR_CONFIG['PORT'] 
IB_CLIENT_ID  = IBKR_CONFIG['CLIENT_ID']

# Trade sizing & targets from globals
MAX_RISK_PER_TRADE = TRADING_PARAMS['MAX_RISK_PER_TRADE']
STOP_LOSS_PCT      = TRADING_PARAMS['STOP_LOSS_PCT']
TP_PCTS            = TRADING_PARAMS['TAKE_PROFIT_LEVELS']

# Scanner parameters from globals  
EQUITY_SCAN = get_scanner_subscription("equity")
CRYPTO_SCAN = get_scanner_subscription("crypto")

# In-memory state
ib        = IB()
POSITIONS = {}  # { conId: {qty, entryPrice, stopPrice, tpPrice, orders} }

### ─── HELPERS ──────────────────────────────────────────────────────────────

def connect_ibkr():
    ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
    ib.reqAccountUpdates(True, '')  # start account updates

def get_net_liquidation() -> float:
    # waits until accountSummary is populated
    summary = ib.accountSummary()
    for item in summary:
        if item.tag == 'NetLiquidation':
            return float(item.value)
    return 0.0

def make_bracket(contract, qty, entryPrice, stopLossPrice, takeProfitPrice):
    """Return [parent, takeProfit, stopLoss] orders linked as a bracket."""
    parent = MarketOrder('BUY', qty)
    tp     = LimitOrder('SELL', qty, takeProfitPrice,
                       parentId=parent.orderId, tif='GTC')
    sl     = StopOrder('SELL',  qty, stopLossPrice,
                       parentId=parent.orderId, tif='GTC')
    return [parent, tp, sl]

### ─── SCANNER & SIGNAL HANDLING ────────────────────────────────────────────

def run_scanner():
    # 1) scan equities
    eq_hits = ib.reqScannerSubscription(EQUITY_SCAN)
    # 2) scan crypto
    cr_hits = ib.reqScannerSubscription(CRYPTO_SCAN)

    # give it a couple seconds to fill
    ib.sleep(2)

    for hit in eq_hits + cr_hits:
        sym = hit.contractDetails.summary.symbol
        secType = hit.contractDetails.summary.secType
        exch = hit.contractDetails.summary.exchange
        currency = hit.contractDetails.summary.currency
        contract = Contract(symbol=sym, secType=secType, exchange=exch, currency=currency)

        # skip if already in flight
        if contract.conId in POSITIONS:
            continue

        # fetch live price
        ticker = ib.reqMktData(contract, '', False, False)
        ib.sleep(1)
        price = float(ticker.marketPrice())

        on_signal(contract, price)

    # cancel subscriptions
    ib.cancelScannerSubscription(EQUITY_SCAN)
    ib.cancelScannerSubscription(CRYPTO_SCAN)

def on_signal(contract, price):
    cash = get_net_liquidation()
    risk_amt = cash * MAX_RISK_PER_TRADE
    qty = int(risk_amt // price)
    if qty < 1:
        return

    # choose a random TP% (or implement your own logic)
    tp_pct = choice(TP_PCTS)
    tp_price = price * (1 + tp_pct)
    sl_price = price * (1 - STOP_LOSS_PCT)

    bracket = make_bracket(contract, qty, price, sl_price, tp_price)
    orders = [ib.placeOrder(contract, o) for o in bracket]

    POSITIONS[contract.conId] = {
        'contract': contract,
        'qty': qty,
        'entry': price,
        'stop': sl_price,
        'tp': tp_price,
        'orders': orders
    }
    print(f"[ENTER] {contract.symbol} x{qty} @ {price:.2f} TP@{tp_price:.2f} SL@{sl_price:.2f}")

### ─── POSITION MONITOR ────────────────────────────────────────────────────

def manage_positions():
    for cid, pos in list(POSITIONS.items()):
        # check if any leg is filled or cancelled
        statuses = [o.orderStatus.status for o in pos['orders']]
        # if all legs done or cancelled → clean up
        if all(s in ('Filled','Cancelled') for s in statuses):
            POSITIONS.pop(cid)


# ─── (1) SETUP LOGGING ─────────────────────────────────────────────────────
# Use centralized logging from globals
logger = setup_agent_logging("ibkr_trader")


# ─── (2) EVENT CALLBACKS ───────────────────────────────────────────────────
def onFill(trade: Trade, fill: Fill, cr: CommissionReport):
    s = trade.contract.symbol
    qty = fill.execution.shares
    price = fill.execution.avgPrice
    side = "BUY" if qty>0 else "SELL"
    logger.info(f"[FILL] {s} {side} {abs(qty)} @ {price:.2f}")

def onOrderStatus(order, status: OrderStatusEvent):
    logger.info(f"[ORDER] {order.action} {order.totalQuantity} {order.symbol} → status={status.status}")

def onPortfolioUpdate(item: PortfolioItem):
    s = item.contract.symbol
    pos = item.position
    pnl = item.marketValue - item.averageCost * pos
    logger.info(f"[PORTF] {s} pos={pos} avgCost={item.averageCost:.2f} unrealPnl={pnl:.2f}")

# attach callbacks after connecting:
ib = IB()
ib.orderStatusEvent += onOrderStatus
ib.tradeEvent       += onFill
ib.updatePortfolioEvent += onPortfolioUpdate


# ─── (3) PERIODIC STATUS REPORT ────────────────────────────────────────────
def report_status():
    if not POSITIONS:
        logger.info("No open positions.")
        return
    rows = []
    for pos in POSITIONS.values():
        c = pos['contract']
        sym = c.symbol
        cur = ib.reqMktData(c, '', False, False); ib.sleep(0.5)
        price = float(cur.marketPrice())
        entry = pos['entry']
        qty   = pos['qty']
        unreal = (price - entry) * qty
        rows.append({
            "symbol": sym,
            "qty":    qty,
            "entry":  entry,
            "current":price,
            "unreal P/L": round(unreal,2),
            "stop":   round(pos['stop'],2),
            "tp":     round(pos['tp'],2)
        })
    df = pd.DataFrame(rows).set_index("symbol")
    logger.info(f"\n{df}\n")

# schedule it every 5 min:
schedule.every(5).minutes.do(report_status)


### ─── SCHEDULER ───────────────────────────────────────────────────────────

def main():
    connect_ibkr()
    # initial scan
    run_scanner()

    # schedule
    schedule.every(5).minutes.do(run_scanner)
    schedule.every(1).minutes.do(manage_positions)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()


