# Bar-by-bar prototype of Scout_Pine's rules (spec §3), used to tune them against the owner's markups (spec §2.3).
# Same rules and order as pine/Scout_Pine.pine; keep both in step.
# Usage: python proto.py <data dir> <MARKET> <from> <to>   e.g.  python proto.py data EURUSD 2026-10-06T00:00 2026-10-07T20:00
import sys, pandas as pd, numpy as np
P = dict(atrLen=14, pushBody=0.6, minMove=1.5, minPause=2, maxPause=16, maxPauseH=3.0,
         maxRetrace=0.6, revMin=4, flipATR=3.0, wickTol=0.6, channel=20, mode="smart")

def load(m):
    df = pd.read_csv(f"{sys.argv[1]}/{m}.csv", parse_dates=["t"]).iloc[:-1].reset_index(drop=True)
    tr = np.maximum(df.h - df.l, np.maximum(abs(df.h - df.c.shift()), abs(df.l - df.c.shift())))
    df["atr"] = tr.ewm(alpha=1 / P["atrLen"], adjust=False).mean()   # = ta.atr (RMA)
    return df

def level(df, a, b, d, atr):
    """Order level for pause bars a..b: above them for d=1, below for d=-1."""
    w = df.iloc[a:b + 1]
    if d == 1:
        ext, body = w.h.values, np.maximum(w.o, w.c).values
    else:
        ext, body = -w.l.values, np.maximum(-w.o, -w.c).values    # mirror lows into "highs"
    if P["mode"] == "wick":   v = ext.max()
    elif P["mode"] == "body": v = body.max()
    else:
        v = np.where(ext - body > P["wickTol"] * atr, body, ext).max()
    return v * d

def run(df):
    ev = []
    trend, ext, moveStart, lastOpp = 0, np.nan, np.nan, np.nan
    ps, main, ctr = None, np.nan, np.nan
    for i in range(1, len(df)):
        o, h, l, c, atr = df.o[i], df.h[i], df.l[i], df.c[i], df.atr[i - 1]
        if np.isnan(atr): continue
        d = trend
        # 1. orders placed after earlier bars
        hitMain = d != 0 and not np.isnan(main) and (h >= main if d == 1 else l <= main)
        hitCtr = d != 0 and not np.isnan(ctr) and (l <= ctr if d == 1 else h >= ctr)
        if hitMain:
            ev.append((i, "TRIG", d, main))
            lastOpp = df.l[ps:i].min() if d == 1 else df.h[ps:i].max()
            ps, main, ctr = None, np.nan, np.nan
        elif hitCtr:
            ev.append((i, "TRIG-REV", -d, ctr))
            trend = d = -d
            lastOpp = df.l[ps:i].min() if d == 1 else df.h[ps:i].max()
            ext = h if d == 1 else l
            moveStart = lastOpp
            ps, main, ctr = None, np.nan, np.nan
        # 2. trend start
        body = c - o
        push = abs(body) >= P["pushBody"] * atr
        if trend == 0:
            if push:
                trend = d = 1 if body > 0 else -1
                ext, moveStart = (h, l) if d == 1 else (l, h)
            continue
        ext = max(ext, h) if d == 1 else min(ext, l)
        # 3. trend flip: close beyond the last pause, or a big move against the trend
        if not (hitMain or hitCtr):
            # flip: far from the trend's extreme, pushed there by >= 2 strong candles of the last 3
            pushes = sum((df.o[j] - df.c[j]) * d >= P["pushBody"] * df.atr[j - 1] for j in range(i - 2, i + 1))
            # or a strong candle against the trend closing beyond the last N candles' range
            N = P["channel"]
            breakout = i > N and (o - c) * d >= P["pushBody"] * atr and \
                (c < df.l[i - N:i].min() if d == 1 else c > df.h[i - N:i].max())
            if ((ext - c) * d >= P["flipATR"] * atr and pushes >= 2) or breakout:
                if not np.isnan(main): ev.append((i, "CANCEL", d, main))
                trend = d = -d
                ext, moveStart, lastOpp = (h if d == 1 else l), (ext), np.nan
                ps, main, ctr = None, np.nan, np.nan
                ev.append((i, "FLIP", d, c))
                continue
        # 4. pause
        if hitMain or hitCtr:
            continue                                   # breakout bar is part of the move
        # a new extreme before any order exists: the move is still going, restart the pause here
        if ps is not None and np.isnan(main):
            prev = df.iloc[ps:i]
            if (h > prev.h.max()) if d == 1 else (l < prev.l.min()):
                ps = None
        if ps is None:
            move = (ext - moveStart) * d
            if not (push and np.sign(body) == d) and move >= P["minMove"] * atr:
                ps = i
        if ps is None: continue
        w = df.iloc[ps:i + 1]
        n = len(w)
        height = w.h.max() - w.l.min()
        retr = ((ext - (w.l.min() if d == 1 else w.h.max())) * d) / max((ext - moveStart) * d, 1e-12)
        if n > P["maxPause"] or height > P["maxPauseH"] * atr or retr > P["maxRetrace"]:
            if not np.isnan(main): ev.append((i, "CANCEL", d, main))
            # the pullback low becomes the base of the next move
            moveStart = w.l.min() if d == 1 else w.h.max()
            ext = h if d == 1 else l
            ps, main, ctr = None, np.nan, np.nan
            continue
        if n >= P["minPause"]:
            lv = level(df, ps, i, d, atr)
            if np.isnan(main) or lv != main:
                ev.append((i, "SET" if np.isnan(main) else "MOVE", d, lv))
            main = lv
        if n >= P["revMin"]:
            half = n // 2
            first, last = w.iloc[:n - half], w.iloc[n - half:]
            roll = (last.h.max() < first.h.max()) if d == 1 else (last.l.min() > first.l.min())
            if roll:
                cv = level(df, ps, i, -d, atr)
                if np.isnan(ctr) or cv != ctr:
                    ev.append((i, "REV-SET", -d, cv))
                ctr = cv
    return ev

if __name__ == "__main__":
    m, a, b = sys.argv[2:5]
    df = load(m)
    for i, k, d, v in run(df):
        if pd.Timestamp(a) <= df.t[i] <= pd.Timestamp(b) and k in ("TRIG", "TRIG-REV", "FLIP", "SET", "CANCEL", "REV-SET"):
            print(f"{df.t[i]:%m-%d %H:%M} {k:8} {'BUY ' if d == 1 else 'SELL'} {v:.6g}")
