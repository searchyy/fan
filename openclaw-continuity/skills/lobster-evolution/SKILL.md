---
name: lobster-evolution
description: Continuously learn from local skills, workspace docs, scripts, git changes, and user conversations; distill reusable patterns into memory, workflow updates, helper scripts, and skill patches. Use when the user asks the agent to evolve, keep learning, build personal workflows, or turn repeated lessons from real tasks into long-term operating procedures.
---

# Lobster Evolution

Treat evolution as a standing objective, not a one-off task.

## Run the loop

1. Review recent signals from:
   - user instructions in the current chat
   - `MEMORY.md` and `memory/YYYY-MM-DD.md`
   - local skills under `/home/fan/.openclaw/workspace/skills`
   - local docs/scripts/projects in the workspace
   - recent git diffs and recurring fixes
2. Identify only **reusable** learnings:
   - repeated user preferences
   - procedures worth standardizing
   - scripts worth saving
   - pitfalls worth preventing
   - local environment facts that improve future execution
3. Convert the learning into the smallest durable artifact:
   - update `MEMORY.md` for long-term standing rules/preferences
   - update `memory/YYYY-MM-DD.md` for daily context and recent changes
   - patch an existing skill when the lesson belongs to that domain
   - create or improve a local helper script when determinism matters
   - document a workflow in the most specific local file instead of duplicating it everywhere
4. Keep the delta compact. Prefer small, high-signal updates over verbose notes.
5. Commit workspace changes after meaningful edits.

## Heartbeat mode

When the user wants continuous evolution, use heartbeat as the default low-noise scheduler for lightweight learning scans.

- Target cadence: about once every 6 hours when there is no higher-priority alert.
- Use heartbeat for batched, context-aware learning.
- Keep exact-time jobs on cron; do not overload heartbeat with precision scheduling.
- If a scan produces no durable learning, stay quiet.

Track the last evolution scan in `memory/heartbeat-state.json` under `lastChecks.evolution`.

## Default scan order

When there is free time or the user explicitly asks for continuous learning, scan in this order:

1. `skills/*/SKILL.md` for available operating patterns
2. workspace `scripts/` for reusable automation opportunities
3. project docs and local repos that were touched recently
4. `MEMORY.md` plus the last 1-3 daily memory files
5. recent git history for repeated fixes or operational drift

## Promotion rules

Promote a learning to `MEMORY.md` only if it is likely to matter again.

Good candidates:
- stable user preferences
- standing tasks
- hard-won operational lessons
- local setup facts that prevent breakage

Keep transient noise in daily memory instead.

## Project-analysis extraction mode

When a project investigation produces a useful pattern, compress it into a reusable protocol instead of leaving it as one-off commentary.

Use the four-layer structure from `references/project-analysis-protocol.md`:
- project essence
- best participation plan
- abuse surface / risk review
- decision impact

Default abuse-surface categories to check:
- fake data injection
- replay / duplicate submission
- weak auth binding
- client-trust assumptions
- normalization / weight mapping abuse
- ranking / points / invite manipulation

Use a safe testing ladder:
- static audit
- public read-only endpoint checks
- non-invasive auth/error-path validation
- local reproduction
- explicit authorized testing only after that

## Meme-analysis extraction mode

For meme tokens, do not overfit to generic project-analysis order. Use `references/meme-analysis-protocol.md`.

Bias the analysis toward:
- KOL framing weight
- next-bagholder profile
- narrative break conditions
- spread quality of heat
- market-maker / operator intent
- media relay vs real community heat
- same-lane substitutes
- final go-grade: 只适合观察 / 可看 / 可小仓 / 可追

Keep contract security as the risk floor, not the lead story, unless contract control can directly destroy the meme narrative.

## Evolution outputs

Prefer one of these outputs each time a real learning appears:
- one memory update
- one skill patch
- one new helper script
- one workflow note
- one cleanup/refactor that removes future friction

## Guardrails

- Do not modify core OpenClaw config unless the user explicitly asks.
- Do not invent busywork or infinite loops.
- Do not duplicate the same rule in multiple files unless there is a clear retrieval reason.
- Prefer learning from actual work over abstract self-reflection.

## Bundled helper

Use `scripts/record_evolution.py` to append a compact learning note into today’s daily memory file when a lesson should survive the session.

## Meme reply output

When answering meme-token investigations, use the fixed spine in `references/meme-analysis-template.md` unless the user explicitly wants a shorter or custom format.

## Contract forensics extraction mode

When a meme contract forensics session produces new classification heuristics, distill them:

1. Check if庄家/高手识别规则在 `skills/meme-contract-forensics/SKILL.md` 是否覆盖了新发现的模式。
2. If a new operator pattern was identified (new distribution method, new wash-trade signature), patch the skill's 庄家判定标准 table.
3. If a new smart-money signal was found, add it to the 高手判定标准 table.
4. Update `scripts/contract_forensics.py` scoring logic when the user corrects a mis-classification.
5. Promote to `MEMORY.md` only if a data-source change occurred (new API, new endpoint, new key).

Typical evolution triggers from contract forensics:
- user says "this address is obviously a market maker" → tighten庄家 scoring rules
- user says "this is a real trader, not a smart money" → adjust smart-money scoring weights
- new DEX router address discovered → add to EXCLUDE_ADDRS in the script

## Wallet batch screening extraction mode

When a batch address screening session produces a watchlist, distill the reusable pattern:

1. Check if `references/batch-screening-protocol.md` inside `wallet-playbook-analysis` exists and is current.
2. If new scoring rules or filter heuristics were applied, patch the protocol file.
3. Update `scripts/batch_wallet_analysis_moralis.py` if logic improvements were made during the session.
4. Promote to `MEMORY.md` only if a standing user preference changed (e.g. new API key, new filter threshold).

Typical evolution triggers from address analysis:
- user rejects a tier and explains why → update scoring weights in the protocol
- new noise pattern discovered → add to filter rules
- new API endpoint or data source introduced → update script and document in skill

## Wallet playbook extraction mode

When the user asks how an address trades dirt dogs / meme tokens, use `references/address-playbook-protocol.md`.

Focus on:
- excluding seconds-level flips first
- identifying survivor positions
- inferring first-board vs second-wave vs falling-knife preference
- extracting sizing logic and topic preference
- separating learnable method from pure noise
