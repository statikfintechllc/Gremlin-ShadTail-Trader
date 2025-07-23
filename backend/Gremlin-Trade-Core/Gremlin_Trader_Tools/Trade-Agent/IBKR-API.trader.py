#!/usr/bin/env python3
import os
import time
from random import choice
from ib_insync import IB, Stock, Contract, ScannerSubscription, MarketOrder, LimitOrder, StopOrder, Trade, Fill, CommissionReport, OrderStatusEvent, PortfolioItem
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import schedule

### ─── CONFIG ───────────────────────────────────────────────────────────────
IB_HOST       = os.getenv("IBKR_HOST", "127.0.0.1")
IB_PORT       = int(os.getenv("IBKR_PORT", 7497))
IB_CLIENT_ID  = int(os.getenv("IBKR_CLIENT_ID", 1))

# Trade sizing & targets
MAX_RISK_PER_TRADE = 0.10   # 10% of net liquidation
STOP_LOSS_PCT      = 0.15   # 15% stop loss
TP_PCTS            = [0.05, 0.10, 0.25, 0.50, 1.00]  # choose one per trade

# Scanner parameters
EQUITY_SCAN = ScannerSubscription(
    instrument    = 'STK',
    locationCode  = 'STK.US.MAJOR',
    scanCode      = 'TOP_PERC_GAIN',  # top % gainers
    numberOfRows  = 20,
    abovePrice    = None,
    belowPrice    = 10.0,             # penny stocks < $10
    aboveVolume   = 1_000_000,
    aboveChangePercent = 5.0          # up > 5%
)
CRYPTO_SCAN = ScannerSubscription(
    instrument    = 'CRYPTO',
    locationCode  = 'PAXOS.BTC.USD',  # or your crypto data source/exchange
    scanCode      = 'HOT_BY_PRICE',
    numberOfRows  = 10
)

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
logger = logging.getLogger("TradeBot")
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

# Console
ch = logging.StreamHandler()
ch.setFormatter(fmt)
logger.addHandler(ch)

# File (rotates at 1 MB, keeps 3 backups)
fh = RotatingFileHandler("trade_bot.log", maxBytes=1e6, backupCount=3)
fh.setFormatter(fmt)
logger.addHandler(fh)


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


