# Scout — specification

**Scout watches the markets for the owner's "pause, then stop order" setup and says where to put the order.** In a running trend, every time price pauses for profit taking, the owner places a Buy Stop above the pause (up-trend) or a Sell Stop below it (down-trend). Scout finds these pauses on many symbols and timeframes and alerts the owner. Later, on the owner's click, it places the orders itself and hands them to TM.

| Item | Value |
|---|---|
| Status | **Phase 1 built** (29-Oct-2026): `Scout_Pine` compiles and runs on TradingView (ICMARKETS:EURUSD 1H). Owner review on more charts is due (§6 Phase 2) |
| Document version | v1.0 (29-Oct-2026) — history in §8 |
| Owner | Zeeshan |
| Repository | `~/code/Scout` (not on GitHub yet) — separate from [Trader](https://github.com/ziash/Trader), [Rewind](https://github.com/ziash/Rewind) and [Levels](https://github.com/ziash/Levels) |
| Family | **Scout_Pine** (Phase 1): TradingView indicator, `pine/Scout_Pine.pine`. **Scout** (later): a bot on Ubuntu that watches cTrader prices and places orders on the owner's click |
| Accounts | Scout_Pine never trades. Scout: demo accounts only until a go-live is decided (Trader shared.md §4) |

---

## 1. Idea

The owner trades by hand on the 1H chart (also 4H and 1D). The setup is simple to see and hard to watch for across many charts:

1. A market is moving (trending).
2. It pauses: a few small candles, or a small pull-back, where traders take profit.
3. A stop order just beyond the pause, in the trend's direction, catches the next leg.

The owner takes **every** such pause while the trend runs. Some lose; nobody knows in advance which, so the rule stays the same. Scout's job is to see the pauses on every chart the owner names (e.g. BTCUSD 1D/4H/1H, GBPJPY 4H) and say "place a Buy Stop at X" in time.

## 2. The setup

Learned from the owner's chart and markups (29-Oct-2026), not from fixed numbers: *"if markets were mathematical, many would be profitable traders."* The settings in §3.2 are a translation of these points, tuned against the markups.

### 2.1 Rules

| # | Rule | Owner's words / evidence |
|---|---|---|
| 1 | **Trend direction first.** At a pause, the stop goes in the direction of the move: Buy Stop above in an up-trend, Sell Stop below in a down-trend | Original chart: one Buy Stop in the rally, four Sell Stops in the fall |
| 2 | **Every pause gets an order** while the trend runs — a staircase of entries. Losers are part of it | *"In real time the trader would not know which entries would become profitable… the trader needs to take all entries where the price goes a little back (profit taking)."* BTCUSD_Modified: 4 entries per trend, one a loser |
| 3 | **A pause** is 2 or more small candles, or a small bounce against the trend; it stays near the end of the move | Markups: pauses of 2–5 candles; the EURUSD top range ~12 candles |
| 4 | **Level** at the wick high/low of the pause candles; a candle whose wick sticks out far beyond its body counts at its body | Matches most lines (EURUSD 1.1194, GBPJPY 211.98, BTC 81,000). Not confirmed by the owner — §7 q4 |
| 5 | **Reversal = a failed pause.** If the trend-direction stop does not fill and the pause rolls over (lower highs at a top, higher lows at a bottom), place the opposite stop under/over the pause. If it fills, the trend has turned | Owner on the EURUSD top (6–7 Oct): *"I would have made a buy stop first which would not have triggered, giving the picture"* |
| 6 | **The end of a trend needs no call.** The last order of a trend does not fill, or loses | EURUSD 1.1215 and 1.1174, GBPJPY 210.03 |

### 2.2 Markups

`research/setup-examples/`: `<SYMBOL>.png` are the 10 first examples (blue lines, one long and one short per chart); `<SYMBOL>_Modified.png` / `_modified.png` carry the owner's red lines (BTCUSD, EURUSD, GBPJPY). On BTCUSD_Modified the two "Sell Stop" labels on 14 Sep (77,700 and 78,180) are Buy Stops (owner, 29-Oct-2026).

### 2.3 Prototype

`research/prototype/proto.py` runs the same rules as Scout_Pine bar by bar in Python, on candles from `fetch.py` (Binance for BTC/ETH; Yahoo for EURUSD, GBPJPY, gold futures — not the brokers' own prices). It was used to tune §3.2 against the markups:

| Owner's line | Prototype | |
|---|---|---|
| GBPJPY 213.06 / 213.50 / 214.44 / 214.99 | 213.10 / 213.50 / 214.42 / 214.99 | match |
| GBPJPY 215.32 | 215.33 | match |
| EURUSD 1.1165 (first long off the bottom) | reversal Buy Stop 1.1165, filled | match |
| EURUSD 1.1194 / 1.1215 | 1.1194 / 1.1215 | match (1.1215 touched exactly: counts as filled; owner had it unfilled) |
| EURUSD top 1.1252 | Buy Stop above the top range first, then reversal Sell Stop 1.1249, filled | match, the owner's way (rule 5) |
| BTC 77,700 / 78,180 / 78,450 / 81,350 | within ~50 | close |
| BTC 77,920 | 77,750 | off: drawn at the bodies there |

It also finds pauses the owner did not mark: about 2–3 setups per chart per day on 1H.

## 3. Scout_Pine (Phase 1)

A TradingView indicator, Pine Script v6 (TradingView's own scripting language), one file `pine/Scout_Pine.pine`. Chart title "Scout_Pine", legend "Scout".

### 3.1 How it works

Only closed candles change the state, so marks never repaint. On each closed candle:

1. **Fills.** A pending stop whose level the candle touched is filled (▲ / ▼). A filled reversal stop turns the trend.
2. **First trend.** Until the first strong candle, the trend is unknown.
3. **Trend turns** without a fill when price is ≥ 3 ATR (ATR = average candle range, 14 candles) away from the trend's extreme, pushed there by at least 2 strong candles of the last 3; or when a strong candle closes beyond the last 20 candles' range. A single spike that is bought back does not turn it.
4. **Pause.** After a move of ≥ 1.5 ATR, the first candle that is not a strong candle in the trend's direction starts a pause. A new extreme before the order exists restarts it. From the 2nd candle the stop is placed (§2.1 rules 1, 4). From the 4th, if the pause rolls over, the reversal stop is placed too (rule 5). The pause is cancelled when it gives back more than 60 % of the move, gets taller than 3 ATR, or lasts more than 16 candles; the pull-back then becomes the base of the next move.

### 3.2 Settings (defaults)

| Group | Setting | Default |
|---|---|---|
| Setup | Strong candle: body ≥ × ATR | 0.6 |
| | Move before a pause ≥ × ATR | 1.5 |
| | Pause: min / max candles | 2 / 16 |
| | Pause: max height × ATR | 3.0 |
| | Pause: max pull-back of the move | 0.6 |
| | Reversal stop: after this many pause candles | 4 |
| | Trend turns: move against it ≥ × ATR | 3.0 |
| | Trend turns: strong candle closes beyond last N candles | 20 |
| | ATR length | 14 |
| Order level | Level at: Smart / Wicks / Bodies | Smart |
| | Smart: long wick ≥ × ATR | 0.6 |
| | Extra distance beyond the level (ticks) | 0 |
| Display | Show setups in the last X candles | 500 |
| | Reversal stops / cancelled levels / pause shading | on |
| Alerts | New level, level moved, reversal stop, level hit, cancelled | on |
| | Trend turned | off |

### 3.3 Chart

Blue line = Buy Stop, red = Sell Stop, from the pause's first candle; the pause shaded yellow; dotted = reversal stop; ▲/▼ = filled; dashed = cancelled. Pending levels also show in the Data Window.

### 3.4 Alerts

One TradingView alert per chart and timeframe, condition **Scout_Pine → "Any alert() function call"**. Messages start with symbol and timeframe, e.g. `EURUSD 60: new Buy Stop at 1.11645`. "Level hit" fires as it happens; the rest at the candle's close. Alerts run on TradingView's servers (laptop can be off); how many are allowed depends on the TradingView plan.

### 3.5 Use

Chart the broker's own symbol (e.g. `ICMARKETS:EURUSD`) so levels match cTrader. Place the order by hand in cTrader: an order without a label is taken over by TM (`takeOver: [""]`, Trader tm.md §2.1). TradingView's own IC Markets trading link likely uses a separate account that TM does not watch — do not rely on it.

### 3.6 Check (29-Oct-2026)

Compiled and added to the chart in TradingView: ICMARKETS:EURUSD 1H — "Compiled. Added to chart.", no runtime error. Recent candles (27–29 Oct) showed the staircase of Sell Stops in the fall, reversal Buy Stops at the bottom and a reversal Sell Stop after the bounce. Not yet compared with the markups on IC Markets prices.

## 4. Scout bot (later — proposal, not agreed)

| Part | Proposal |
|---|---|
| What | Watches a list of symbol × timeframe (e.g. BTCUSD 1D/4H/1H, GBPJPY 4H) on the broker's own candles; shows setups on a web page; on the owner's click, places one stop order per pause until stopped |
| Prices and orders | cTrader Open API, demo only. Orders carry the label `Scout-<instance>-…`; TM takes them over once `"Scout-"` is in TM's `takeOver` (Trader tm.md §2.1, v1.6), so TM mirrors, hedges and manages them |
| Language | C# / .NET 10 (open source, runs on Linux) — the rest of the owner's bots use it |
| Web page | ASP.NET Core inside the bot, `http://localhost:5080`, live updates (SignalR), TradingView Lightweight Charts (free, open source) — laptop only at first; a login and HTTPS before it is reachable from elsewhere (VPS later) |
| Storage | JSON files under `~/tradebot/` like TM; no database |
| Tests | The owner's markups (§2.2) as test cases |

## 5. Separation

- Scout_Pine never trades and needs nothing from Trader.
- Scout (bot) will place orders, so it falls under Trader's safety rules (demo only, labels, ownership, protection). Where its code lives is open (§7 q1). Until decided, nothing in this repository connects to a broker, and nothing of Trader's (`~/code/Trader`, `~/tradebot/`, `~/.config/trader/`) is read or changed from here.

## 6. Phases

| Phase | Name | Status |
|---|---|---|
| 0 | Repo and spec | Done 29-Oct-2026 |
| 1 | Scout_Pine: marks and alerts on TradingView | Built 29-Oct-2026; compiles (§3.6) |
| 2 | Owner review on more charts; tune §3.2 | Due |
| 3 | Scout detector in C#, tested against the markups | — |
| 4 | Scout live watch + alerts (cTrader prices) | — |
| 5 | Web page: watchlist, setups, Start/Stop | — |
| 6 | Orders on the owner's click, handed to TM | — |

## 7. Open questions

| # | Question | Notes |
|---|---|---|
| 1 | Where does the Scout bot's code live? | (a) `src/Trader.Scout` in Trader, reusing Trader.Core (connection, tokens, orders, notifications) and its safety rules; (b) here, with Trader.Core pieces copied. Recommendation: (a) for the bot, this repo for Scout_Pine, spec and research |
| 2 | Lot size | TM's mirror doubles it: a 0.5 Scout order becomes 1.0 once filled |
| 3 | Stop-loss on Scout's orders | If set at the far side of the pause, TM uses it as the hedge level H; without one, TM uses 15 % of the 3-day range |
| 4 | Level: wicks or bodies? | Smart default fits most markups; owner to confirm |
| 5 | Unfilled stop when the next pause forms | Scout_Pine keeps one pending stop per trend; a new pause replaces a cancelled one. Bot: move or cancel? |
| 6 | Number of setups | ~2–3 per chart per day on 1H; stricter settings if too many |

## 8. History

| Version | Date | Change |
|---|---|---|
| v1.0 | 29-Oct-2026 | Repo created. Setup rules from the owner's markups (§2), Scout_Pine Phase 1 (§3), bot proposal (§4), open questions (§7) |
