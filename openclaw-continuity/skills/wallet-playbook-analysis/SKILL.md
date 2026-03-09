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
- round trips within seconds
- exits within a few minutes with no residual position
- tiny batch-transfer / airdrop dust
- approval-only routing noise

### Higher-conviction clues
- repeated buys into the same ticker
- partial de-risk + residual position still held
- ticker still visible in current higher-value holdings
- multiple tickets from the same concept cluster
- quick test entry followed by a larger re-entry

## Style labels

- **首板型**: enters early, many small probes, launchpad-heavy, narrative-first
- **二波型**: waits for proof, adds after initial narrative acceptance, fewer names, larger sizing
- **接飞刀型**: buys after visible damage, likes retrace entries into prior hot names

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
