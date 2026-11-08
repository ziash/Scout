# Scout — specification

**Scout watches the markets for the owner's "pause, then stop order" setup and says where to put the order.** In a running trend, every time price pauses for profit taking, the owner places a Buy Stop above the pause (up-trend) or a Sell Stop below it (down-trend). Scout finds these pauses on many symbols and timeframes and alerts the owner (**Watch** mode), or places the entry stop order itself (**Trade** mode). Scout's job ends with that first order: TM manages everything after it (mirror, hedges, break-even, trailing stop).

| Item | Value |
|---|---|
| Status | **Phase 1 built** (29-Oct-2026): `Scout_Pine` compiles and runs on TradingView (ICMARKETS:EURUSD 1H). **Scout bot agreed** (03-Nov-2026, §4): Open API service in the Trader repository, Watch and Trade modes. **Trial run from 03-Nov-2026** (§4.6): Trade mode, 0.1 lot, 1H, TM managing; review after one week. From 04-Nov-2026: IC Markets only, 18 symbols; from 07-Nov-2026: Pepperstone only, same 18 (§4.6). **Daily first** (owner, 07-Nov-2026, §4.7): the daily chart sets direction and the first entry, 4H/1H pauses add on — decided, to be measured on history before the rules change |
| Document version | v1.10 (08-Nov-2026) — history in §8 |
| Owner | Zeeshan |
| Repository | [github.com/ziash/Scout](https://github.com/ziash/Scout) (public) — separate from [Trader](https://github.com/ziash/Trader), [Rewind](https://github.com/ziash/Rewind) and [Levels](https://github.com/ziash/Levels) |
| Family | **Scout_Pine** (Phase 1): TradingView indicator, `pine/Scout_Pine.pine` — **closed for development 07-Nov-2026** (§3). **Scout** (Phases 3–5): a C# bot on Ubuntu that watches cTrader prices; code in Trader as `src/Trader.Scout` (§4, §5) |
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

**Closed for development (owner, 07-Nov-2026).** Scout_Pine stays as built (v1.0 rules, §3.1–3.2) and can still be used on TradingView, but new rules (§4.7, §4.8 and later) go only into the Scout bot's C# code in Trader. The Python prototype (§2.3) is frozen with it; the C# detector, its tests and the replay are the reference from now on.

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

- Scout only **alerts or places the entry order**. It never moves or amends an order, and never touches a position.
- The order carries what the owner would set by hand: a **stop-loss at the far side of the pause** (the other side's level, §2.1 rule 4) and the **trailing switch on**. TM uses the stop-loss as its hedge level H and makes the break-even stops trail (tm.md §3, §5).
- TM takes the order over by its label (`"Scout-"` in TM's `takeOver`, Trader tm.md §2.1): mirror order beside it, hedges once filled, break-even at 1R, trailing stop (tm.md §3.1, §5).
- **An unfilled order whose setup is gone** (q7, decided 03-Nov-2026): Scout **cancels its own unfilled order** when its rules end the setup — trend turned, pause too long or too deep, or the other order of the same pause filled (q10). As a safety net for when Scout is not running, every order has an **expiry on the server**: 16 candles after the candle that gave its level (the longest a pause lasts, §3.2), so a late placement never gives an old setup a fresh 16 candles. A level the live price has already passed gets no order (v1.10). TM cancels its mirror order when Scout's order is cancelled or expires (tm.md §3.1).

### 4.3 Alerts

Channel open (§7 q8). First: the desktop pop-ups and `events.csv` of Trader's shared notifications (`Trader.Core/Notifications`, `notifications.json`), which TM already uses; Telegram or another channel later, as a new channel there, without a change to Scout. Alert kinds as Scout_Pine's (§3.4); in Trade mode also "order placed" and "order rejected".

### 4.4 Improvements over Scout_Pine v1.0 (owner, 03-Nov-2026)

| # | Improvement | First idea, to be tuned against the markups (§2.2) |
|---|---|---|
| I1 | **Higher-timeframe trend** | Every setup is tagged with the trend of the next timeframe up (1H ← 4H, 4H ← 1D, 1D ← 1W), from the same detector run on that timeframe's closed candles: *with*, *against* or *unknown*. **Marked only, never skipped** (q9, 03-Nov-2026): the owner takes every pause (§2.1 rule 2), and the first entry after a turn is against the higher trend by nature. The trial's logs decide whether *against* setups are worth skipping |
| I2 | Level: Smart rule | Confirmed (§2.1 rule 4, §7 q4); stays the default |
| I3 | No moving stops | §4.2: Scout's order is never moved; TM manages it |
| I4 | **Reversal stops are orders too** (q10, 03-Nov-2026) | In Trade mode the reversal stop (§2.1 rule 5) is placed like the main one, with its stop-loss at the main level. The two are a pair: when one fills, Scout cancels the other ("one cancels the other") |

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

### 4.6 Trial run (owner, 03-Nov-2026)

| Item | Value |
|---|---|
| Start | 03-Nov-2026, as the systemd service `trader-scout`; TM (`trader-tm`) running with `"Scout-"` in `takeOver` |
| Mode | **Trade** on every chart below |
| Timeframe | **1H** (4H for the I1 tag only) |
| Symbols | From 04-Nov-2026 (owner), top three per market: EURUSD, GBPUSD, USDJPY; GBPJPY, EURJPY, AUDJPY; XAUUSD, XAGUSD, XPTUSD; US500, USTEC, DE40; XTIUSD, XBRUSD, XNGUSD; BTCUSD, ETHUSD, SOLUSD. 03–04 Nov: TM's six (AUDJPY, EURGBP, EURUSD, GBPJPY, BTCUSD, ETHUSD) |
| Accounts | From 07-Nov-2026 17:27Z (owner): Pepperstone (brokerB) only, for fresh results (Trader scout.md v1.15). 04–07 Nov: IC Markets (brokerA) only. 03–04 Nov: both demos, IC Markets and Pepperstone (brokerB), each with its own detector on its own candles |
| Size | **0.1 lot** per Scout order; TM's mirror adds the same, so 0.2 lot per trade (q2). From 04-Nov-2026 (owner): a fixed size per symbol, small, so a typical 1H move is worth about the same money on every symbol (≈ $15 per order; forex still 0.1 lot) — values in Trader `config/scout.json` |
| Logs | Scout: every setup event and every order, fill and close (Trader `docs/bots/scout.md` §3); TM: its own `actions.csv` |
| Review | After one week (≈ 10-Nov-2026): from both bots' logs, score the setups — fill rate, win rate and R per trade, *with* vs *against* the 4H trend, main vs reversal stops, per symbol, market and broker — and suggest changes to the rules (§3.2) |

### 4.7 Daily first: timeframes top-down (owner, 07-Nov-2026)

From the owner's USTEC markups of Oct–Nov 2026 (daily, 4H, 1H; charts and explanation: [research/setup-examples/USTEC-2026-10](../research/setup-examples/USTEC-2026-10/README.md)): the **daily chart sets the direction and the first entry** — a stop just beyond a daily level, e.g. a Sell Stop under a daily range low after a top; a daily support zone that held twice becomes resistance once broken ("Sell Stop #2"). **4H and 1H pauses are re-entries that add to the position**, only in the daily direction.

| # | Decision (owner, 07-Nov-2026) | Rule today | Change |
|---|---|---|---|
| D1 | **Trade with the daily trend.** 4H/1H pauses against the daily direction are not traded, even in Trade mode; they are reported as alerts, with the reason in the logs and on the dashboard | Higher timeframe only tagged (q9; 1H ← 4H) | Daily direction as a filter; 4H tag kept |
| D2 | **Higher timeframes give the direction and the key support/resistance levels; entries come from the pauses on the daily chart and every chart between it and the one Scout is set on** (table below). Placed automatically during the test; an "Automatic orders" on/off switch on the dashboard, to turn off before a live account | Pauses on the set chart only (1H) | The detector runs on every chart of the ladder; direction and levels from the daily and monthly pictures (Trader scout-lens.md §1.2) |
| D3 | **Add-ons: same size**, as many as the rules allow (the margin budget still applies); the AI layer may later skip some | One order per pause, same size | None — every aligned pause is an add-on |
| D4 | **Retracement of the move:** up to Fib 0.382 = full size (ideal); 0.382–0.5 = **half size**; deeper than 0.5 = skip (0.618 is too much) | Pause cancelled beyond 0.6 of the move (§3.2) | 0.5 limit, half size above 0.382 |
| D5 | **A one-candle pull-back is a pause** — a strong trend where few traders close ("Sell Stop beautifully at only 1 candle retrace") | A pause needs 2 candles before a stop is placed (§2.1 rule 3, §3.1 step 4) | Stop from the 1st pause candle |

**Entry ladder (D2, owner, 07-Nov-2026).** Daily and monthly charts set the direction and the key support/resistance levels in every case; the first entry and the add-ons come from the pauses on these charts, in that direction only:

| Scout set on | Entries from |
|---|---|
| Daily | Daily |
| 4H | Daily, 4H |
| 1H | Daily, 4H, 1H |
| 30M | Daily, 4H, 1H, 30M |

The higher charts give the first entry (e.g. the daily Sell Stop under a range low); the lower ones scale the position up. **30M is the lowest chart Scout trades on** (owner, 07-Nov-2026; an earlier 15M row is withdrawn). Lower charts (15M, 5M) are only consulted for checks (§4.8), **5M at the lowest**. 30M is a new timeframe for Scout (today: 1H, 4H, daily).

**Order of work:** these change the rules, so each is first measured on years of history (Trader scout-lens.md §8 step 1: the replay with outcomes, tagging each setup with the daily direction, its retracement depth and one-candle pauses), checked against the markups (CLAUDE.md rule 3), then built into Trader's C# detector (Scout_Pine is closed, §3).

### 4.8 Lower-timeframe confirmation (owner, 07-Nov-2026)

From the same markups (USTEC 1H, 14 Oct 2026 14:00, and its twelve 5-minute candles; [research/setup-examples/USTEC-2026-10 §3–4](../research/setup-examples/USTEC-2026-10/README.md)). The lower timeframe shows how strong the trend is and how weak the counter-trend side was inside a pause.

| # | Rule (owner, 07-Nov-2026) | How it is measured | Used for |
|---|---|---|---|
| L1 | **Strong trend: few pauses up high, pauses down low.** A higher-timeframe move with no pause yet, while a lower chart of the ladder shows pauses, is a strong trend; lower timeframes give more chances to join it | For each pause on a chart of the ladder: the number of pauses the next higher chart has had in the same leg (0 = strong) | Tag on every setup; entries on the lower chart in that leg are taken at full size |
| L2 | **Pause confirmed on a lower timeframe.** Decompose the pause candle(s) into a lower timeframe (1H → 5M: twelve candles). The pause is strong when (a) the correction's **bodies stay within 38.2 %** of the lower-timeframe impulse into the pause, and (b) **every counter-trend candle is answered within 1–2 candles** by a candle in the trend's direction | (a) deepest body close of the correction, as a fraction of the impulse leg on the lower chart; (b) for each counter-trend candle, the number of candles until the next with-trend candle; strong = all within 2. Lower chart: D1 → 1H, 4H → 15M, 1H → 5M, 30M → 5M — **5M is the lowest chart consulted; no 1M** (owner, 07-Nov-2026) | Tag on every setup (strong · normal · weak); later: size and the AI layer |

Like §4.7, these are first measured on years of history (the replay tags every setup with L1 and L2), checked against the markups (CLAUDE.md rule 3), then built into Trader's C# detector (Scout_Pine is closed, §3). The replay needs the lower-timeframe candles (5-minute history for a 1H Scout).

## 5. Separation

- Scout_Pine never trades and needs nothing from Trader.
- The Scout bot places orders, so its code lives in the Trader repository (`src/Trader.Scout`) under Trader's rules, with its own bot document `docs/bots/scout.md` there for running details (config, labels, service) that points back here for the setup rules. This repository keeps Scout_Pine, this spec (setup, modes, improvements), the markups and the prototype.
- Nothing in this repository connects to a broker, and nothing of Trader's (`~/code/Trader`, `~/tradebot/`, `~/.config/trader/`) is read or changed from here. Trader changes are made in the Trader repository on the owner's go.

## 6. Phases

| Phase | Name | Status |
|---|---|---|
| 0 | Repo and spec | Done 29-Oct-2026 |
| 1 | Scout_Pine: marks and alerts on TradingView | Built 29-Oct-2026; compiles (§3.6) |
| 2 | Owner review on more charts; tune §3.2 | Closed 07-Nov-2026 with Scout_Pine (§3); tuning continues in the C# bot from the replay |
| 3 | Scout detector in C# (`src/Trader.Scout`, no broker), same results as Scout_Pine / the prototype on the markups; then I1 higher-timeframe trend (§4.4) | Built 03-Nov-2026 |
| 4 | **Watch** mode: live cTrader demo candles, alerts (§4.1, §4.3); `trader-scout` service | Built with Phase 5, 03-Nov-2026 |
| 5 | **Trade** mode: Scout places the entry stop; `"Scout-"` added to TM's `takeOver` (Trader change) | Trial run from 03-Nov-2026 (§4.6) |
| 6 | Optional: web page (watchlist, setups, Start/Stop) | — |

## 7. Open questions

| # | Question | Notes |
|---|---|---|
| 1 | ~~Where does the Scout bot's code live?~~ — **answered 03-Nov-2026: (a)** an Open API service, `src/Trader.Scout` in Trader, reusing Trader.Core; this repo for Scout_Pine, spec and research (§4.5, §5) | — |
| 2 | ~~Lot size~~ — **0.1 lot** for the trial (owner, 03-Nov-2026); TM's mirror doubles it to 0.2 (§4.6) | — |
| 3 | ~~Stop-loss on Scout's orders~~ — **decided 03-Nov-2026: at the far side of the pause**, trailing switch on; TM uses it as the hedge level H (§4.2) | Review after the trial |
| 4 | ~~Level: wicks or bodies?~~ — **answered 03-Nov-2026: Smart** (owner) | — |
| 5 | ~~Unfilled stop when the next pause forms: move or cancel?~~ — **answered 03-Nov-2026**: Scout never moves stops; it only places the first order or alerts; TM manages after that (§4.2) | Leaves q7 |
| 6 | Number of setups | ~2–3 per chart per day on 1H; stricter settings if too many |
| 7 | ~~Who removes a Scout stop that never filled once its setup is gone?~~ — **decided 03-Nov-2026**: Scout cancels its own unfilled order when the setup ends, plus a server expiry 16 candles after placing as a safety net (§4.2) | — |
| 8 | Alert channel | Desktop pop-ups via Trader's notifications for orders placed and refused; everything in the logs. Telegram or other later (§4.3) |
| 9 | ~~Higher-timeframe trend: skip or mark?~~ — **decided 03-Nov-2026: mark only**, 1H ← 4H, 4H ← 1D, 1D ← 1W (§4.4 I1); skipping reconsidered from the trial's logs | — |
| 10 | ~~Reversal stops as orders?~~ — **decided 03-Nov-2026: yes**, paired with the main stop, one cancels the other (§4.4 I4) | — |
| 11 | Daily first (§4.7): D1–D5 and the entry ladder decided by the owner 07-Nov-2026 (0.382–0.5 = half size; entries from the daily chart down to the set chart, direction and levels from daily and monthly); 30M is the lowest trading chart (owner, 07-Nov-2026; 15M and 5M only for checks). Lower-timeframe confirmation L1–L2 (§4.8) decided the same day | Measured on history first |

## 8. History

| Version | Date | Change |
|---|---|---|
| v1.0 | 29-Oct-2026 | Repo created. Setup rules from the owner's markups (§2), Scout_Pine Phase 1 (§3), bot proposal (§4), open questions (§7) |
| v1.1 | 03-Nov-2026 | **Scout bot agreed** (owner, §4): Open API service in Trader (`src/Trader.Scout`, q1 answered); **Watch** and **Trade** modes; Scout only alerts or places the first order, TM manages the rest (q5 answered); Smart level confirmed (q4); improvement I1 higher-timeframe trend; alert channel open. Phases 3–6 reshaped (§6). New open questions q7–q10 |
| v1.2 | 03-Nov-2026 | **Decisions for the trial run** (owner asked Claude to choose, §4.6): q7 Scout cancels its own unfilled order when the setup ends + server expiry after 16 candles; q9 higher-timeframe trend marked only; q10 reversal stops placed as orders, one cancels the other; q3 stop-loss at the far side of the pause with trailing on; q2 0.1 lot. Trial from 03-Nov-2026 in Trade mode on 1H, six symbols, both demos; review after a week |
| v1.3 | 04-Nov-2026 | **Trial widened** (owner, §4.6): IC Markets only, 18 symbols — top three per market (forex majors, forex crosses, metals, indices, energies, crypto); Pepperstone dropped. Same rules, mode, timeframe and lot size. Trader: scout.md v1.4 |
| v1.4 | 04-Nov-2026 | **Size per symbol** (owner, §4.6): fixed lots per symbol so a 1H ATR is worth ≈ $15 per order everywhere (forex 0.1 lot); risk per trade shown in a later Scout screen. Trader: scout.md v1.5 |
| v1.5 | 07-Nov-2026 | **Daily first** (owner, §4.7): the daily chart sets direction and the first entry; 4H/1H pauses add on in its direction only (against it: alerts with a reason); add-ons same size; retracement ≤ 0.382 full, 0.382–0.5 smaller, > 0.5 skip; a one-candle pull-back counts as a pause; an "Automatic orders" switch. To be measured on history before the rules change (q11). Trial moved to Pepperstone 07-Nov (Trader scout.md v1.15) |
| v1.6 | 07-Nov-2026 | **Daily first, completed** (owner, §4.7): 0.382–0.5 retracement = half size (D4); **entry ladder** (D2): direction and key levels from the daily and monthly charts, entries from the daily chart down to the chart Scout is set on (1H: daily, 4H, 1H); 30M and 15M planned as new timeframes. Open: 15M itself in a 15M ladder (q11) |
| v1.7 | 07-Nov-2026 | **Lower-timeframe confirmation** (owner, §4.8): L1 strong trend = no pause yet on the higher chart while a lower chart pauses; L2 a pause confirmed on a lower timeframe (bodies within 38.2 %, counter-trend candles answered within 1–2 candles). Entry ladder: a 15M Scout also enters on 15M (§4.7). The owner's USTEC charts and their explanation added: `research/setup-examples/USTEC-2026-10` |
| v1.8 | 07-Nov-2026 | **Scout_Pine closed for development** (owner, §3): new rules go only into the C# bot in Trader; the Python prototype frozen with it; phase 2 closed. Lower-timeframe check (§4.8 L2): **5M is the lowest chart consulted**, no 1M (15M → 5M) |
| v1.9 | 07-Nov-2026 | **30M is the lowest trading chart** (owner, §4.7): the 15M ladder row withdrawn; 15M and 5M only for checks (§4.8), 5M the lowest |
| v1.10 | 08-Nov-2026 | §4.2 (owner: implement the independent review, Trader scout.md v1.25): expiry counts from the candle that gave the level; a level the price has already passed gets no order |
