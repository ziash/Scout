# Scout

**Finds the owner's "pause, then stop order" setup on many charts and says where to put the order.**

In a running trend, every pause for profit taking gets a stop order just beyond it in the trend's direction: a Buy Stop above the pause in an up-trend, a Sell Stop below it in a down-trend. Scout watches for these pauses and alerts you.

| Item | Value |
|---|---|
| Status | **Phase 1 built** (29-Oct-2026): Scout_Pine compiles and runs on TradingView. **Scout bot agreed** (03-Nov-2026): C#, Watch and Trade modes; not built yet |
| Specification | [docs/spec.md](docs/spec.md) — the single source of truth (setup rules, settings, phases, open questions, history) |
| Scout_Pine | [pine/Scout_Pine.pine](pine/Scout_Pine.pine) — TradingView indicator, Pine Script v6. **Closed for development** (07-Nov-2026): new rules go only into the C# bot ([spec §3](docs/spec.md#3-scout_pine-phase-1)) |
| Scout (bot) | Watches cTrader prices; **Watch** mode alerts, **Trade** mode places the first stop order and TM manages the rest. Code in Trader as `src/Trader.Scout` ([spec §4](docs/spec.md#4-scout-bot-agreed-03-nov-2026)) |
| Research | [research/setup-examples](research/setup-examples) — the marked-up charts; [research/prototype](research/prototype) — the Python check of the rules |
| Related | [Trader](https://github.com/ziash/Trader) (TM manages the orders you place), [Rewind](https://github.com/ziash/Rewind), [Levels](https://github.com/ziash/Levels) |

## Phases

| Phase | Name | Status |
|---|---|---|
| 0 | Repo and spec | Done |
| 1 | Scout_Pine: marks and alerts | Built 29-Oct-2026 |
| 2 | Owner review, tuning | Due |
| 3 | Scout detector in C# + tests; higher-timeframe trend | — |
| 4 | Watch mode: live alerts | — |
| 5 | Trade mode: first order, TM manages | — |
| 6 | Web page (optional) | — |

## Add Scout_Pine to TradingView

1. Open a chart of your broker's symbol, e.g. `ICMARKETS:EURUSD`, 1H.
2. Pine Editor → **Open → New indicator** → replace the template with the whole of [`pine/Scout_Pine.pine`](pine/Scout_Pine.pine) → **Save** as "Scout_Pine" → **Add to chart**.
3. **Alert** → Condition: **Scout_Pine** → **Any alert() function call** → Create. One alert per chart and timeframe covers new levels, moves, reversal stops, hits and cancels.
4. Place the order by hand in cTrader; TM takes it over.

## Run the prototype

```bash
python3 -m venv research/prototype/venv
research/prototype/venv/bin/pip install pandas
research/prototype/venv/bin/python research/prototype/fetch.py research/prototype/data
cd research/prototype && venv/bin/python proto.py data EURUSD 2026-10-06T00:00 2026-10-07T20:00
```
