import requests
import csv
import os
from datetime import datetime, timezone


P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
SPOT_URL = "https://api.binance.com/api/v3/ticker/price"
CSV_PATH = os.path.join(os.path.dirname(__file__), "prices.csv")

FIELDNAMES = [
    "timestamp",
    "p2p_best_buy_bob",
    "p2p_best_sell_bob",
    "p2p_avg_buy_bob",
    "p2p_avg_sell_bob",
    "p2p_spread_bob",
    "btc_usdt",
    "eth_usdt",
]


def fetch_p2p(trade_type, rows=5):
    """
    Fetch top P2P ads for USDT/BOB.
    trade_type BUY  = merchants buying  USDT (user sells USDT, gets BOB)
    trade_type SELL = merchants selling USDT (user buys  USDT, pays BOB)
    """
    payload = {
        "fiat": "BOB",
        "page": 1,
        "rows": rows,
        "tradeType": trade_type,
        "asset": "USDT",
        "countries": [],
        "proMerchantAds": False,
        "shieldMerchantAds": False,
        "filterType": "all",
        "periods": [],
        "additionalKycVerifyFilter": 0,
        "publisherType": None,
        "payTypes": [],
        "classifies": ["mass", "profession"],
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
    resp = requests.post(P2P_URL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return [float(ad["adv"]["price"]) for ad in data["data"]]


def fetch_spot(symbol):
    resp = requests.get(SPOT_URL, params={"symbol": symbol}, timeout=10)
    resp.raise_for_status()
    return float(resp.json()["price"])


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # P2P BOB/USDT
    buy_prices  = fetch_p2p("BUY")   # merchants buying  USDT → price = BOB per USDT they pay
    sell_prices = fetch_p2p("SELL")  # merchants selling USDT → price = BOB per USDT they ask

    best_buy  = min(sell_prices)   # cheapest ask  (best price to BUY  USDT with BOB)
    best_sell = max(buy_prices)    # highest bid   (best price to SELL USDT for BOB)
    avg_buy   = round(sum(sell_prices) / len(sell_prices), 4)
    avg_sell  = round(sum(buy_prices)  / len(buy_prices),  4)
    spread    = round(best_buy - best_sell, 4)

    # Spot prices
    btc_usdt = fetch_spot("BTCUSDT")
    eth_usdt = fetch_spot("ETHUSDT")

    row = {
        "timestamp":        timestamp,
        "p2p_best_buy_bob":  best_buy,
        "p2p_best_sell_bob": best_sell,
        "p2p_avg_buy_bob":   avg_buy,
        "p2p_avg_sell_bob":  avg_sell,
        "p2p_spread_bob":    spread,
        "btc_usdt":          btc_usdt,
        "eth_usdt":          eth_usdt,
    }

    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(
        f"[{timestamp}] "
        f"BOB buy:{best_buy} sell:{best_sell} spread:{spread} | "
        f"BTC:{btc_usdt} ETH:{eth_usdt}"
    )


if __name__ == "__main__":
    main()
