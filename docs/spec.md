# Scout — specification

**Scout watches the markets for the owner's "pause, then stop order" setup and says where to put the order.** In a running trend, every time price pauses for profit taking, the owner places a Buy Stop above the pause (up-trend) or a Sell Stop below it (down-trend). Scout finds these pauses on many symbols and timeframes and alerts the owner (**Watch** mode), or places the entry stop order itself (**Trade** mode). Scout's job ends with that first order: TM manages everything after it (mirror, hedges, break-even, trailing stop).

| Item | Value |
|---|---|
| Status | **Phase 1 built** (29-Oct-2026): `Scout_Pine` compiles and runs on TradingView (ICMARKETS:EURUSD 1H). **Scout bot agreed** (03-Nov-2026, §4): Open API service in the Trader repository, Watch and Trade modes; nothing built yet (§6 Phase 3) |
| Document version | v1.1 (03-Nov-2026) — history in §8 |
| Owner | Zeeshan |
| Repository | [github.com/ziash/Scout](https://github.com/ziash/Scout) (public) — separate from [Trader](https://github.com/ziash/Trader), [Rewind](https://github.com/ziash/Rewind) and [Levels](https://github.com/ziash/Levels) |
| Family | **Scout_Pine** (Phase 1): TradingView indicator, `pine/Scout_Pine.pine`. **Scout** (Phases 3–5): a C# bot on Ubuntu that watches cTrader prices; code in Trader as `src/Trader.Scout` (§4, §5) |
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
| 4 | **Level** at the wick high/low of the pause candles; a candle whose wick sticks out far beyond its body counts at its body ("Smart") | Matches most lines (EURUSD 1.1194, GBPJPY 211.98, BTC 81,000). **Confirmed by the owner 03-Nov-2026** (§7 q4) |
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

## 4. Scout bot (agreed 03-Nov-2026)

A C# program that runs the same detector as Scout_Pine (§3.1, §3.2) on the broker's own candles and either alerts or places the first order. Scout_Pine stays as the chart view on TradingView.

### 4.1 Modes

| Mode | What Scout does on a new setup | Orders |
|---|---|---|
| **Watch** | Sends an alert: symbol, timeframe, side, level, e.g. `EURUSD 1H: new Buy Stop at 1.11645` | None |
| **Trade** | Places the entry stop order at the level (Buy Stop above the pause, Sell Stop below), label `Scout-<instance>-…`, and sends the same alert saying it was placed | One pending stop per setup |

The mode is set per symbol × timeframe in Scout's config, so a chart can be watched before it is traded.

### 4.2 Scout places the first order; TM does the rest (owner, 03-Nov-2026)

- Scout only **alerts or places the entry order**. It never moves, amends or closes an order or a position afterwards, and sets no trailing stop.
- TM takes the order over by its label (`"Scout-"` in TM's `takeOver`, Trader tm.md §2.1 v1.6): mirror order beside it, hedges once filled, break-even at 1R, trailing stop (tm.md §3.1, §5).
- **Gap:** TM never changes an order it did not place (tm.md §2), so nobody removes a Scout stop whose setup is gone (pause cancelled, trend turned) and that never filled. See §7 q7.

### 4.3 Alerts

Channel open (§7 q8). First: the desktop pop-ups and `events.csv` of Trader's shared notifications (`Trader.Core/Notifications`, `notifications.json`), which TM already uses; Telegram or another channel later, as a new channel there, without a change to Scout. Alert kinds as Scout_Pine's (§3.4); in Trade mode also "order placed" and "order rejected".

### 4.4 Improvements over Scout_Pine v1.0 (owner, 03-Nov-2026)

| # | Improvement | First idea, to be tuned against the markups (§2.2) |
|---|---|---|
| I1 | **Higher-timeframe trend** | A 1H pause is checked against the trend on 4H (and 1D) from the same detector. A setup against it is marked weaker, or skipped in Trade mode — which of the two, and which pairs of timeframes, is §7 q9. A setting, off/on, so its effect on the markups can be seen |
| I2 | Level: Smart rule | Confirmed (§2.1 rule 4, §7 q4); stays the default |
| I3 | No moving stops | §4.2: Scout's order is never moved; TM manages it |

Entry rules will be refined further by the owner ("we will further refine its entries"); each change is checked against the markups before it becomes a default (CLAUDE.md rule 3).

### 4.5 How it runs

| Part | Decision |
|---|---|
| Prices and orders | cTrader **Open API** (Spotware's interface that programs use to talk to cTrader's servers), demo accounts only (Trader shared.md §4); trendbars (candles) of the broker's own symbols, closed candles only, as in Scout_Pine |
| Code | `src/Trader.Scout` in the Trader repository (§7 q1), reusing Trader.Core: connection, tokens, market data, orders, notifications, instance registry; Trader's safety rules (labels, ownership, demo only) apply |
| Language | C# / .NET 10 LTS |
| Service | A systemd user service `trader-scout` like `trader-tm`, from a published build in `~/tradebot/bin/Scout` |
| Storage | JSON files under `~/tradebot/` like TM; no database |
| Tests | The detector as a library with no broker connection, tested against the owner's markups (§2.2, §2.3 table) and against the prototype on the same candles |
| Web page | Not needed for Watch or Trade; maybe later (§6 Phase 6) |

## 5. Separation

- Scout_Pine never trades and needs nothing from Trader.
- The Scout bot places orders, so its code lives in the Trader repository (`src/Trader.Scout`) under Trader's rules, with its own bot document `docs/bots/scout.md` there for running details (config, labels, service) that points back here for the setup rules. This repository keeps Scout_Pine, this spec (setup, modes, improvements), the markups and the prototype.
- Nothing in this repository connects to a broker, and nothing of Trader's (`~/code/Trader`, `~/tradebot/`, `~/.config/trader/`) is read or changed from here. Trader changes are made in the Trader repository on the owner's go.

## 6. Phases

| Phase | Name | Status |
|---|---|---|
| 0 | Repo and spec | Done 29-Oct-2026 |
| 1 | Scout_Pine: marks and alerts on TradingView | Built 29-Oct-2026; compiles (§3.6) |
| 2 | Owner review on more charts; tune §3.2 | Due |
| 3 | Scout detector in C# (`src/Trader.Scout`, no broker), same results as Scout_Pine / the prototype on the markups; then I1 higher-timeframe trend (§4.4) | — |
| 4 | **Watch** mode: live cTrader demo candles, alerts (§4.1, §4.3); `trader-scout` service | — |
| 5 | **Trade** mode: Scout places the entry stop; `"Scout-"` added to TM's `takeOver` (Trader change); checked on Rewind, then on a demo | — |
| 6 | Optional: web page (watchlist, setups, Start/Stop) | — |

## 7. Open questions

| # | Question | Notes |
|---|---|---|
| 1 | ~~Where does the Scout bot's code live?~~ — **answered 03-Nov-2026: (a)** an Open API service, `src/Trader.Scout` in Trader, reusing Trader.Core; this repo for Scout_Pine, spec and research (§4.5, §5) | — |
| 2 | Lot size | TM's mirror doubles it: a 0.5 Scout order becomes 1.0 once filled |
| 3 | Stop-loss on Scout's orders | If set at the far side of the pause, TM uses it as the hedge level H; without one, TM uses 15 % of the 3-day range |
| 4 | ~~Level: wicks or bodies?~~ — **answered 03-Nov-2026: Smart** (owner) | — |
| 5 | ~~Unfilled stop when the next pause forms: move or cancel?~~ — **answered 03-Nov-2026**: Scout never moves stops; it only places the first order or alerts; TM manages after that (§4.2) | Leaves q7 |
| 6 | Number of setups | ~2–3 per chart per day on 1H; stricter settings if too many |
| 7 | Who removes a Scout stop that never filled once its setup is gone? TM does not touch orders it did not place (tm.md §2) | Options: (a) Scout gives each order an expiry time on the server (e.g. after N candles) — no later action by Scout; (b) the owner cancels by hand after an alert; (c) a new TM rule for `Scout-` orders. Recommendation: (a) |
| 8 | Alert channel | Desktop pop-ups via Trader's notifications first; Telegram or other later (§4.3) |
| 9 | Higher-timeframe trend (I1): skip the setup or only mark it? Which timeframe checks which (1H←4H, 4H←1D)? | Decided from the markups once I1 is built |
| 10 | Trade mode: are reversal stops (§2.1 rule 5) placed as orders too, or only alerted? | Each is the first order of a new trend |

## 8. History

| Version | Date | Change |
|---|---|---|
| v1.0 | 29-Oct-2026 | Repo created. Setup rules from the owner's markups (§2), Scout_Pine Phase 1 (§3), bot proposal (§4), open questions (§7) |
| v1.1 | 03-Nov-2026 | **Scout bot agreed** (owner, §4): Open API service in Trader (`src/Trader.Scout`, q1 answered); **Watch** and **Trade** modes; Scout only alerts or places the first order, TM manages the rest (q5 answered); Smart level confirmed (q4); improvement I1 higher-timeframe trend; alert channel open. Phases 3–6 reshaped (§6). New open questions q7–q10 |
