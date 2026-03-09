# Address Playbook Protocol

Use this when the user asks to analyze a wallet's trading style, especially for BSC meme / dirt-dog behavior.

## Goal

Infer the wallet's playbook, not just list transactions.

## Output questions

Always answer these:
1. Which trades are noise / seconds-level flips and should be excluded?
2. Which positions look like real held winners / survivors?
3. Which trades likely contributed realized profit?
4. Does the wallet prefer first-board, second-wave, or falling-knife entries?
5. What topic cluster does it specialize in?
6. What is the wallet's position-sizing logic?
7. What is its stop-loss logic?
8. What is its take-profit logic?
9. What part is worth learning vs what part is just luck / noise?

## Analysis order

1. Wallet size / capital base
2. Recent transaction cadence
3. Launchpad / router dependency
4. Token transfer timeline
5. Remove seconds/minutes-level flips first
6. Compare remaining buys with current holdings snapshot
7. Label survivors, failed probes, tactical exits, and realized-profit candidates
8. Infer style: first-board / second-wave / knife-catching
9. Infer stop-loss logic (position stop / time stop / relative-strength stop)
10. Infer take-profit logic (quick first take / rolling reduce / leave runner)

## Key heuristics

### Exclude these from conviction analysis
- round trips within seconds
- exits within a few minutes with no residual position
- dust airdrops
- obvious approval-only noise

### Treat these as higher-conviction clues
- repeated buys into the same ticker
- partial de-risk + residual position still held
- current holdings with non-trivial USD weight
- concentration among similar concept clusters

### Infer realized-profit candidates like this
- same ticker appears with non-trivial IN -> OUT windows that are longer than scalp noise
- position is revisited or scaled, not just one-touch flipped
- part of the position is sold while some residual stays alive
- ticker later appears among current higher-value holdings
- wallet cycles back into the same concept family after first successful test

### Separate three layers of edge
- scalp noise layer
- rolling realized-PnL layer
- survivor/runner layer

A good dirt-dog address usually uses all three, but only the last two explain real performance.

## Style labels

- **首板型**: enters early, many small probes, launchpad-heavy, narrative-first
- **二波型**: waits for proof, adds after initial narrative acceptance, fewer names, larger sizing
- **接飞刀型**: buys after visible damage, likes prior hot names in retrace, less launchpad dependence

## Stop-loss / take-profit inference

Do not assume fixed percentage rules unless evidence is strong.
Prefer these categories:

### Stop-loss
- **仓位止损**: tiny initial size caps downside before price-based stop matters
- **时间止损**: exits if the coin fails to strengthen within a short window
- **相对强弱止损**: rotates out when stronger names emerge in the same batch

### Take-profit
- **首波先吃**: first impulse gets partially or fully realized quickly
- **滚动止盈**: repeated in/out on the same theme to recycle capital
- **留活口**: strong names keep a runner after initial profit-taking

## Compression rule

Do not drown the user in raw tx spam.
Compress into:
- noise trades to ignore
- realized-profit candidates
- survivor positions
- style label
- stop-loss logic
- take-profit logic
- actionable lessons
