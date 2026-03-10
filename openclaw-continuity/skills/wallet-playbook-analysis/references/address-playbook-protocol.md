# Address Playbook Protocol

## Goal
Infer a wallet's repeatable trading method instead of summarizing its raw history.

## Mandatory questions
1. Which trades are noise and should be excluded?
2. Which positions likely contributed realized profit?
3. Which positions are survivors / runners?
4. Is the wallet primarily 首板 / 二波 / 接飞刀?
5. What topic cluster does it specialize in?
6. How does it size entries?
7. How does it stop out?
8. How does it take profit?
9. Which parts are worth learning?

## Analysis order
1. Wallet size / capital base
2. Recent cadence
3. Preferred launchpad / router
4. Token transfer timeline
5. Remove seconds-level flips first
6. Match remaining buys against current holdings snapshot
7. Label realized-profit candidates, survivors, and failed probes
8. Infer style label
9. Infer stop-loss logic
10. Infer take-profit logic

## Realized-profit candidate heuristics
Prefer these clues:
- non-trivial IN -> OUT windows longer than scalp noise
- same ticker revisited or scaled, not just touched once
- partial exits while some size remains alive
- ticker later appears in higher-value current holdings
- wallet revisits the same concept family after early success

## Three-layer model
Always separate behavior into:
- scalp noise layer
- rolling realized-PnL layer
- survivor / runner layer

Only the last two explain durable performance.

## Noise filter threshold
Exclude transactions where buy-to-sell gap < **120 seconds** (consistent with batch protocol).
Also exclude: `possible_spam=true`, dust-only IN with no OUT, approval-only noise.

## Delivery rule
Default delivery for address analysis is a `.txt` report.

- Write the report to `skills/wallet-playbook-analysis/reports/`
- Use a deterministic filename: `wallet-<addr8>.txt` or `wallet-<addr8>-profit.txt`
- Send the txt file to the user, not just store it locally
- Inline chat text can stay as a short summary or status note

## Compression rule
Answer with the fixed template in `address-analysis-template.md` unless the user wants a custom format.
