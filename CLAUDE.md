# CLAUDE.md — Scout project

Standing instructions for Claude Code in this repository. Read this first, then `README.md` and `docs/spec.md`.

## What this project is

**Scout**: finds the owner's "pause, then stop order" setup (spec §2) on many symbols and timeframes. **Scout_Pine** (Phase 1) is a TradingView indicator that marks the setups and sends alerts; the owner places the orders by hand in cTrader and TM manages them. **Scout** (later) is a bot that watches cTrader prices and places the orders on the owner's click. Spec: `docs/spec.md` (single source of truth).

## Working rules

1. **Code only when the owner says so.** Spec and planning discussions do not authorise coding. Build the phase asked for (spec §6), not the next ones.
2. **Spec-driven.** Any change in decisions, scope or design goes into `docs/spec.md`: bump its version in the header table, add a row to its history (§8), update the open questions (§7) and the phase table (§6). Commit messages like `scout v1.1: <what changed>`. Code comments point at spec sections, e.g. `(spec §3.1)`.
3. **The setup is the owner's, learned from examples.** The owner reads charts by eye and says the market is not mathematical. Rules come from their markups (`research/setup-examples/`); a rule change is checked against those markups with the prototype before it goes into Scout_Pine.
4. **Define difficult terms.** The owner is a telecom core-network engineer, not a developer: explain technical terms (Pine, C#, trading) briefly in plain words.
5. **Explain before large changes**, in a few lines.
6. **Short, direct answers.**

## Separation and safety

- Nothing in this repository connects to a broker or places orders until spec §7 q1 is decided and recorded. Scout_Pine never trades.
- Never read, write or print `~/.config/trader/secrets.env`; never change `~/code/Trader` or `~/tradebot/`, and never stop, restart or redeploy Trader's services from here. A Trader change (e.g. adding `"Scout-"` to TM's `takeOver`) is made in the Trader repository under its own rules, on the owner's go.
- Demo accounts only, ever, until a go-live is decided (Trader shared.md §4).

## Tech stack and conventions

- **Scout_Pine:** Pine Script v6, one file `pine/Scout_Pine.pine`. The second comment line carries the spec version it implements. Only closed candles change the state (no repainting); the "level hit" alert is the one intrabar part.
- **Prototype:** `research/prototype/proto.py` (Python, pandas) runs the same rules in the same order as Scout_Pine. Keep the two in step. Downloaded candles (`research/prototype/data/`) and the venv are never committed.
- **Scout bot (later):** C#, .NET 10 LTS, nullable on, warnings as errors; layout and conventions as in Trader.

## Before finishing a task

- Pine cannot be compiled here. Re-read the script against the spec and Pine v6 rules; if a TradingView session is available, paste it into the Pine Editor and check "Compiled. Added to chart."; otherwise say plainly that the owner's TradingView check is still due.
- Prototype changes: rerun it on the markup windows (spec §2.3) and update that table.
- Commit. Push only once the GitHub repository exists and the owner works from it.
