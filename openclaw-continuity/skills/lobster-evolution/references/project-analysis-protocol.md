# Project Analysis Protocol

Use this protocol when a real project investigation yields reusable method, not just one-off conclusions.

## Goal

Compress each project analysis into four reusable layers:

1. **Project essence**
2. **Best participation plan**
3. **Abuse surface / risk review**
4. **Decision impact**

This turns ad-hoc research into a durable operating pattern.

## Layer 1 — Project essence

Determine what the project actually is before discussing participation.

Questions:
- Is it an asset play, product play, identity system, points system, protocol, or thin wrapper?
- What is the real participation path?
- What are the official moving parts: website, docs, repo, plugin, contracts, API, socials?
- What is the current maturity: live, placeholder, partial launch, or vapor?

Preferred evidence order:
- official frontend behavior
- official repo / README / code
- public API behavior
- on-chain evidence if applicable
- community signals last

If the target is a meme token, switch to `meme-analysis-protocol.md` for ordering and emphasis.

## Layer 2 — Best participation plan

Produce the highest signal, lowest regret participation strategy.

Default structure:
- define whether the project deserves heavy / medium / light participation
- choose the cheapest path to first meaningful milestone
- define stage goals (e.g. Lv.2 → Lv.3 → top 3)
- prefer real useful work over synthetic farming when the system rewards usage/activity
- explicitly state what is *not* worth doing yet

## Layer 3 — Abuse surface / risk review

Always review where the system could be gamed, but keep this in authorized security-audit language.

Look for these categories first:
- fake data injection
- replay / duplicate submission
- auth token leakage or weak binding
- client-side trust assumptions
- model / weight / tier normalization abuse
- invite / points / ranking / claim manipulation
- public API overexposure
- early-user / whitelist / leaderboard edge-case pollution

## Layer 4 — Decision impact

Translate technical findings into participation guidance.

Examples:
- If public credibility is weak, avoid high-cost participation.
- If ranking can be gamed, only take low-cost identity positions.
- If maturity is low but entry cost is tiny, treat it as optional early exposure.
- If abuse surfaces look well controlled, larger participation may be justified.

## Safe testing ladder

Escalate testing in this order:

1. static audit of official code
2. public read-only endpoint checks
3. non-invasive auth/error-path validation
4. controlled local reproduction
5. explicit authorized testing environment

Do not jump to live exploit-style validation on third-party systems without authorization.

## Compression rule

After each project review, try to save only the durable method:
- one protocol patch
- one risk heuristic
- one reusable checklist item
- one memory update if it changes future behavior

Avoid storing long case-specific narration unless it will matter again.
