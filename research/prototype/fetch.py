# Downloads 1H candles for the prototype (spec §2.3): BTC/ETH from Binance, EURUSD/GBPJPY/gold from Yahoo.
# Usage: python fetch.py <data dir>
import json, sys, time, urllib.request
import pandas as pd
out = sys.argv[1]
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))
def binance(sym, n=1500):
    rows, end = [], None
    while len(rows) < n:
        url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=1000" + (f"&endTime={end}" if end else "")
        k = get(url)
        rows = k + rows
        end = k[0][0] - 1
    df = pd.DataFrame(rows, columns=list("tohlcv") + list("abcdef"))[list("tohlc")]
    df["t"] = pd.to_datetime(df.t, unit="ms")
    return df.astype({c: float for c in "ohlc"}).drop_duplicates("t").tail(n)
def yahoo(sym):
    r = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1h&range=90d")["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    df = pd.DataFrame({"t": pd.to_datetime(r["timestamp"], unit="s"), "o": q["open"], "h": q["high"], "l": q["low"], "c": q["close"]})
    return df.dropna()
for name, fn in [("BTCUSD", lambda: binance("BTCUSDT")), ("ETHUSD", lambda: binance("ETHUSDT")),
                 ("EURUSD", lambda: yahoo("EURUSD=X")), ("GBPJPY", lambda: yahoo("GBPJPY=X")), ("XAUUSD", lambda: yahoo("GC=F"))]:
    df = fn(); df.to_csv(f"{out}/{name}.csv", index=False)
    print(name, len(df), df.t.iloc[0], df.t.iloc[-1])
