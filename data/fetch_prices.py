import requests
import csv
import os
from datetime import datetime, timezone


P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
CSV_PATH = os.path.join(os.path.dirname(__file__), "prices.csv")

FIELDNAMES = [
    "timestamp",
    "p2p_sell_bob",
    "p2p_buy_bob",
]


def fetch_p2p(trade_type, rows=20):
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    resp = requests.post(P2P_URL, json=payload, headers=headers, timeout=15)
    print(f"  P2P {trade_type} status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"  P2P {trade_type} response: {resp.text[:500]}")
    resp.raise_for_status()
    data = resp.json()
    if not data.get("data"):
        raise ValueError(f"P2P {trade_type} returned empty data: {data}")
    prices = [float(ad["adv"]["price"]) for ad in data["data"]]
    print(f"  P2P {trade_type} prices: {prices}")
    return prices


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # P2P BOB/USDT
    buy_side  = fetch_p2p("BUY")   # BUY type ads (merchants buying from you = you're selling)
    sell_side = fetch_p2p("SELL")  # SELL type ads (merchants selling to you = you're buying)

    # Get 4th item from the lists (Binance returns them sorted by best offers)
    # NOTE: API parameter names can be counterintuitive
    # buy_side ("BUY" param) = merchants bidding to buy from you
    # sell_side ("SELL" param) = merchants asking to sell to you

    p2p_sell = round(sell_side[3], 4)  # 4th price point on the sell side (what you get)
    p2p_buy  = round(buy_side[3], 4)   # 4th price point on the buy side (what you pay)

    row = {
        "timestamp":     timestamp,
        "p2p_sell_bob":  p2p_sell,
        "p2p_buy_bob":   p2p_buy,
    }

    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(f"[{timestamp}] BOB sell:{p2p_sell} buy:{p2p_buy}")


if __name__ == "__main__":
    main()
