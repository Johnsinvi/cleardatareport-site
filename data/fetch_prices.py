import requests
import csv
import os
from datetime import datetime, timezone


P2P_URL    = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
CSV_PATH = os.path.join(os.path.dirname(__file__), "prices.csv")

FIELDNAMES = [
    "timestamp",
    "p2p_buy_bob",
    "p2p_sell_bob",
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


def fetch_spot_prices():
    """Fetch BTC and ETH prices in USD from CoinGecko (no geo-restrictions)."""
    resp = requests.get(
        COINGECKO_URL,
        params={"ids": "bitcoin,ethereum", "vs_currencies": "usd"},
        timeout=15,
    )
    print(f"  CoinGecko status: {resp.status_code}")
    resp.raise_for_status()
    data = resp.json()
    btc = float(data["bitcoin"]["usd"])
    eth = float(data["ethereum"]["usd"])
    print(f"  BTC: {btc}  ETH: {eth}")
    return btc, eth


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # P2P BOB/USDT
    buy_prices  = fetch_p2p("BUY")   # merchants buying  USDT → price = BOB per USDT they pay
    sell_prices = fetch_p2p("SELL")  # merchants selling USDT → price = BOB per USDT they ask

    # Sort to get 4th lowest/highest
    sell_prices_sorted = sorted(sell_prices)  # ascending: cheapest first
    buy_prices_sorted = sorted(buy_prices, reverse=True)  # descending: highest first

    # 4th lowest buy price (4th cheapest ask), 4th highest sell price (4th highest bid)
    p2p_buy  = round(sell_prices_sorted[3], 4)  # price you pay to BUY  USDT with BOB
    p2p_sell = round(buy_prices_sorted[3], 4)   # price you get to SELL USDT for BOB

    # Spot prices (via CoinGecko — no geo-restrictions)
    btc_usdt, eth_usdt = fetch_spot_prices()

    row = {
        "timestamp":     timestamp,
        "p2p_buy_bob":   p2p_buy,
        "p2p_sell_bob":  p2p_sell,
        "btc_usdt":      btc_usdt,
        "eth_usdt":      eth_usdt,
    }

    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(
        f"[{timestamp}] "
        f"BOB buy:{p2p_buy} sell:{p2p_sell} | "
        f"BTC:{btc_usdt} ETH:{eth_usdt}"
    )


if __name__ == "__main__":
    main()
