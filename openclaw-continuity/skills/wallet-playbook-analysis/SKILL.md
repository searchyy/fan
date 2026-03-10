---
name: wallet-playbook-analysis
description: Analyze an on-chain wallet's trading playbook, especially for BSC meme / dirt-dog wallets. Identify seconds-level noise trades, realized-profit candidates, survivor positions, first-board vs second-wave vs falling-knife style, topic preference, position sizing, stop-loss logic, and take-profit logic. Use when the user asks how an address trades, makes money, manages exits, rotates between meme tokens, or whether a wallet is worth copying.
---

# Wallet Playbook Analysis

Treat the goal as **playbook extraction**, not transaction listing.

## Core workflow

1. Measure wallet size and capital base.
2. Read recent tx cadence and preferred routing / launchpad paths.
3. Pull token transfer history.
4. Remove seconds-level flips, dust, airdrops, and approval noise first.
5. Split the remaining behavior into three layers:
   - scalp noise layer
   - rolling realized-PnL layer
   - survivor / runner layer
6. Identify:
   - likely realized-profit contributors
   - current survivor positions
   - style label: 首板 / 二波 / 接飞刀
   - topic cluster preference
   - position-sizing logic
   - stop-loss logic
   - take-profit logic
7. Compress the result with the fixed skeleton in `references/address-analysis-template.md`.
8. For any non-trivial address analysis, write a `.txt` report under `/home/fan/.openclaw/workspace/reports/` and send that file to the user instead of only leaving it local or only replying inline.

## Heuristics

### Exclude from conviction analysis
- round trips within **120 seconds** (seconds-level scalp noise threshold — consistent with batch protocol)
- exits within a few minutes with no residual position
- `possible_spam=true` from Moralis — discard directly
- tiny batch-transfer / airdrop dust (only IN, no OUT, total < 0.001)
- approval-only routing noise

### Higher-conviction clues
- repeated buys into the same ticker
- partial de-risk + residual position still held
- ticker still visible in current higher-value holdings
- multiple tickets from the same concept cluster
- quick test entry followed by a larger re-entry

## Style labels

- **首板型**: enters early, many small probes, launchpad-heavy, narrative-first
  - Signals: first DEX buy within top-20% of token's trade history; multiple launchpad-origin tokens
- **二波型**: waits for proof, adds after initial narrative acceptance, fewer names, larger sizing
  - Signals: first buy timestamp is 30min–6h after token's first trade; fewer tokens but larger per-position size
- **接飞刀型**: buys after visible damage, likes retrace entries into prior hot names
  - Signals (no price data available via Moralis): infer from **time gap** — first buy is >6h after token's first trade, combined with the token already having high holder count; OR the wallet buys tokens that appear in other wallets' loss records
  - **Limitation**: precise "visible damage" detection requires price history (DexScreener API). Without it, use time-gap + holder-count heuristic as proxy.

## Exit inference

### Stop-loss
Infer from these categories first:
- **仓位止损**: tiny initial size caps downside before price stop matters
- **时间止损**: exit if the coin does not strengthen quickly
- **相对强弱止损**: rotate out when stronger names emerge in the same batch

### Take-profit
Infer from these categories first:
- **首波先吃**: quick first take once momentum proves itself
- **滚动止盈**: repeated in/out on the same ticker or theme
- **留活口**: strong names keep a runner after initial de-risk

## Batch analysis mode

When the user provides multiple addresses (10+) for screening:

1. Use `scripts/batch_wallet_analysis_moralis.py` as the execution engine.
   - **Note**: this script lives at `skills/wallet-playbook-analysis/scripts/batch_wallet_analysis_moralis.py`. If the file is missing, write it before running — see `references/batch-screening-protocol.md` for the full spec.
2. Follow the full screening protocol in `references/batch-screening-protocol.md`.
3. Score each address on the three early-entry / high-winrate dimensions.
   - Apply noise filter (120s threshold, possible_spam, dust) **before** counting multi-buy signals.
4. Output two files: a human-readable `.txt` and a machine-readable `.json` watchlist.
5. Send both files to the user. Inline chat should be a brief summary only.

Key API: Moralis BSC ERC20 transfers — env var `MORALIS_KEY` required.
Key script: `skills/wallet-playbook-analysis/scripts/batch_wallet_analysis_moralis.py`
Report dir: `skills/wallet-playbook-analysis/reports/` (create if missing)

## Output rule

Do not dump raw tx spam. Output only what changes future execution:
- noise trades to ignore
- realized-profit candidates
- survivor positions
- style label
- stop-loss logic
- take-profit logic
- what is worth learning
- what is just noise / luck
