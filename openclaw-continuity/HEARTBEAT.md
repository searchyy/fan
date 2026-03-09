# HEARTBEAT.md

## 每日加密情报简报

仅在以下情况执行：
- 用户明确要求“现在跑一次晨报/情报简报”；或
- 本地时间在 08:55-09:30 之间，且今天还没有发过这份简报。

执行流程：
1. 用 opennews 检索过去 24 小时 AI 评分最高的加密新闻，挑 3 条最重要的。
2. 单独提炼“今天有什么新闻或大事发生了”，优先抓宏观、市场熔断、地缘冲突、监管、ETF、解锁、链上大事件，输出 2-4 条最关键的大事。
3. 单独观察 BTC 生态（BTC / ETF / BTCFi / Ordinals / Runes / 比特币生态项目），提炼 2-4 条有执行价值的信息。
   - 重点观察这些 BTC 生态博主：`@Dongmoom55`、`@dapangdun`、`@CG_BRC20`、`@runes_leo`。
4. 运行 `python3 scripts/steamdt_homepage_sample.py`，提炼 SteamDT 首页大盘样本，输出 2-4 条 CS 饰品市场关键信号。
5. 用 crypto-market-rank 给出趋势币 top 5（优先 24h 维度，必要时附链和主要信号）。
6. 用 meme-rush 找链上新发/临近迁移/已迁移的热点 meme，挑 3 个。
7. 用 opentwitter 观察主流 crypto KOL 在聊什么，总结 2-4 条社区情绪。
8. 额外追踪这 7 个人今天在聊什么：`@flai6666`、`@0xmmu`、`@rocky_eths`、`@libapi_`、`@akakay04`、`@0xzheng888`、`@0x_xifeng`，提炼 3-5 条高价值信息。
9. 从上面选 1 个最值得盯或最有争议的新项目，用 project-onboarding 或 crypto-project-analyzer 做一个简短风控拆解。

BSC 过滤规则（强制执行）：
- 参考 `https://alpha123.uk/zh/stability/` 的“稳定度看板”。
- 对 BSC 方向，默认剔除明显的币安 Alpha 刷量代币和“不稳”代币。
- 如果某个 BSC 标的在稳定度看板里显示为“不稳”，或成交/价差特征明显异常，不进入【热度榜单】和【冲狗前线】的推荐位。
- 如果过滤后 BSC 方向没有足够可靠的候选，相关位置直接写“数据不足”，不要为了凑数把可疑标的塞进去。
- 如果必须提到这类标的，只能放在风险提示里，并明确标注“疑似刷量/不稳”。
- KOGE 可作为稳定参考基线，但不能因为在榜就自动视为推荐。

输出格式固定：
【头条速递】
- ...

【今日大事】
- ...

【BTC生态观察】
- ...

【SteamDT观察】
- ...

【热度榜单】
- ...

【冲狗前线】
- ...

【社交脉搏】
- ...

【7人动态】
- ...

【小龙虾避坑建议】
- 项目：...
- 为什么值得看：...
- 主要风险：...
- 建议动作：观察 / 小仓试错 / 暂避

如果没有足够可靠的数据，就明确写“数据不足”，不要编。

## 小龙虾进化巡检

仅在以下情况执行：
- 用户明确要求“开始学习 / 进化巡检”；或
- 距离上次进化巡检已超过 6 小时，且当前没有更高优先级告警要发。

巡检节奏：
- 用 heartbeat 承接轻量、上下文相关、可批量的学习巡检。
- 精确时间任务（如每日 09:00 晨报）继续交给 cron，不和进化巡检混为一谈。

状态文件：`memory/heartbeat-state.json`
- 记录 `lastChecks.evolution` 的 Unix 时间戳。

执行流程：
1. 扫描 1-2 个本地 skill（优先最近没复习过的）与 1 个本地 docs/scripts/project 目标。
2. 提炼最多 3 条“可复用”收获：流程、脚本机会、踩坑规避、环境事实、用户偏好固化。
3. 只把真正会影响未来执行的东西落地到最小工件：`MEMORY.md` / `memory/YYYY-MM-DD.md` / 某个 skill / 某个脚本。
4. 如需记一笔学习结果，优先调用：`python3 skills/lobster-evolution/scripts/record_evolution.py "..." --kind learning`
5. 更新 `memory/heartbeat-state.json` 里的 `lastChecks.evolution`。

输出原则：
- 有真实升级或新沉淀时，再给老板发简短进化报告。
- 如果这轮没有新东西，直接 `HEARTBEAT_OK`，不要硬编学习成果。
