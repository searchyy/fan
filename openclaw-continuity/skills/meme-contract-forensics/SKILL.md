---
name: meme-contract-forensics
description: 给定一个 BSC meme 合约地址，从链上数据反向识别三类关键地址：庄家地址（砸盘/拉升/分发）、获利最多的地址、真正的 meme 高手。输出结构化分析报告和地址分级跟踪名单。当用户给出一个 meme 合约地址并询问谁是庄家、谁赚钱最多、哪些是聪明钱时使用。
---

# Meme Contract Forensics

## 核心目标
从合约维度反向识别三类地址：
1. **庄家地址**：控盘者，负责拉升/砸盘/分发/洗盘
2. **获利最多地址**：实现最大盈利的前出局者
3. **真正 meme 高手**：以小博大、早进早出、多次复现的聪明钱

## 数据源
- **Moralis API**（主力）：ERC20 transfers、token holders、wallet history
- **BSCScan V2 API**（辅助）：合约创建者（deployer）识别
- Key 存储：`.env` 文件中 `MORALIS_KEY`（必须）、`BSCSCAN_KEY`（deployer识别必须，否则跳过）

## 分析流程（五步法）

### Step 1：合约基础画像
- 获取 token 基本信息：name / symbol / decimals / totalSupply / deployer
- 获取 deployer 地址及其关联地址
- 获取 LP 创建者（通常是庄家主账户）
- 获取初始流动性注入时间和金额
- 识别是否有预挖、内盘分发、团队保留

### Step 2：持仓分布扫描
- 拉取当前持有者列表（top 100-200）
- 计算集中度：前10持仓占比
- 标记异常大户：持仓 > 2% 且不是 LP 合约

### Step 3：庄家识别（三类特征）

> **重要前提**：token transfer ≠ 真实买卖。必须区分以下两类：
> - **DEX swap**：from 或 to 为已知 DEX 路由/LP地址 → 真实买入/卖出
> - **内部分发**：from/to 均为普通地址 → 庄家分发信号（不算买卖，不计入利润排行）
> 脚本的 `parse_transfers()` 已实现此区分，分析结论基于区分后的数据。

#### A. 分发型庄家
- 特征：通过内部 token transfer（非 DEX）从 deployer 向 5+ 个地址分发
- 识别信号：deployer 的 `internal_transfers` 中发出到 ≥5 个不同地址
- 接收者标记为 `distributing_receivers`（内盘知情），从高手候选中剔除

#### B. 拉升型庄家
- 特征：通过 DEX 反复大额买入 → 价格拉升 → 高点砸出
- 识别信号：DEX buys ≥5 次且 DEX sells ≥5 次，且出局率 >80%
- 关键信号：买卖时序（价格数据需另行获取，脚本只做次数和出局率判断）

#### C. 洗盘型庄家
- 特征：在自己控制的地址之间反复 internal transfer，制造交易量假象
- 识别：`detect_wash_trading()` 检测 A→addr→A 的资金循环（金额容差20%）
- 关键信号：循环对数量 ≥1 且金额近似相等

### Step 4：获利排行榜
对每个地址计算：
- 总 DEX 买入量（token数量）
- 总 DEX 卖出量（token数量）
- **注意**：当前版本按 token 卖出量排序，不含精确价格。真实利润 = 卖出量 × 卖出均价 - 买入量 × 买入均价，需通过 DEX 价格 API 另行获取（TODO）
- 出局率：DEX 卖出量 / DEX 买入量
- 持仓时间：首次 DEX 买入到最后一次 DEX 卖出

排行榜前15，标注：
- 是否庄家关联地址（标🔴🟠）
- 是否 deployer 分发接收者（内盘知情）
- 出局率 / 持仓时长

### Step 5：真正高手识别
筛选条件（同时满足）：
- 不是 deployer 关联地址，且不在 `distributing_receivers`（排除内盘知情者）
- 出局率 ≥ 50%（实际 DEX 卖出落袋）
- 买入时机：属于 DEX 首次买入前20%的早期参与者（基于 DEX swap，非分发 transfer）
- 资金体量：中小仓（非大资金）
- **复现性（TODO）**：理想情况应查询该地址在其他 token 上的早期操作记录，当前版本未实现，需调用 `wallet-playbook-analysis` 进一步核实

## 庄家判定标准

| 特征 | 权重 | 说明 |
|------|------|------|
| deployer 直接转账 | 极高 | 100%庄家关联 |
| 持仓 > 5% 且早于公开交易 | 高 | 内盘分发 |
| 买卖循环 ≥ 3次，均在高点卖 | 高 | 拉升型 |
| 与 deployer 有资金往来 | 中 | 关联账户 |
| 转账给多个新钱包 | 中 | 分发操作 |
| 初始 LP 注入者 | 中 | 可能是庄也可能是散 |

## 高手判定标准

| 特征 | 权重 | 说明 |
|------|------|------|
| 早期买入（前10%时间段） | 高 | 嗅觉敏锐 |
| 出局率 ≥ 50% | 高 | 真实落袋 |
| 买入后未出现分发行为 | 高 | 非庄家关联 |
| 持仓 1-5h 内出局 | 中 | 纪律性强 |
| 多票复现同类操作 | 中 | 可学习性强 |
| 仓位合理（非全仓押注） | 低 | 风控意识 |

## 输出规范

### 报告文件
- 主报告：`reports/contract-forensics-{ca_short}-{date}.txt`
- 高手名单：`reports/contract-alpha-{ca_short}-{date}.json`

### 报告结构
```
【合约基础信息】
【庄家地址列表】
  - 类型（分发/拉升/洗盘）
  - 地址
  - 关键证据
【获利排行榜 Top10】
  - 地址 / 估算利润 / 出局率 / 入场时机
【真正高手名单】
  - 地址 / 买入时机 / 出局率 / 可跟踪性评级
【一句话结论】
【跟踪建议】
```

### 高手名单 JSON 字段
```json
{
  "address": "0x...",
  "label": "外部高手/内盘知情/疑似庄关联",
  "entry_rank": "前5%/前20%/前50%",
  "exit_rate": 0.85,
  "est_profit_bnb": 12.3,
  "hold_hours": 2.5,
  "style": "首板型/二波型",
  "replicable": true,
  "note": "一句话特征"
}
```

## 执行脚本
`scripts/contract_forensics.py` — 主分析脚本（已实现五步法 + 洗盘检测 + 集中度）
`scripts/contract_profit_rank.py` — 利润排行专项脚本（TODO：接入价格 API 实现真实利润计算）

## 已知局限（TODO）
1. **价格数据缺失**：利润排行仅凭 token 数量，不含价格。如需真实盈亏需接入 DexScreener/GeckoTerminal 价格历史 API
2. **复现性未实现**：高手识别中的"多票复现"维度需调用 wallet-playbook-analysis 批量分析确认
3. **LP 动态地址**：Uniswap/PancakeSwap LP 合约地址是每个 token pair 独有的，当前 DEX_ADDRS 无法覆盖，未识别的 LP 地址的转账会被误判为内部分发

## 与 wallet-playbook-analysis 的关系
- 本 skill 从合约维度切入，批量识别地址分类
- `wallet-playbook-analysis` 从地址维度深挖单个地址的打法
- 典型流程：先用本 skill 筛出"高手名单"，再用 `wallet-playbook-analysis` 深挖每个高手的具体打法

## 注意事项
- 庄家地址不等于坏人，内盘知情也可能是真实参与者
- 获利排行榜需要排除 LP 合约、DEX 路由合约等基础设施地址
- 利润估算是基于转账量的近似值，不含精确价格，标注为"估算"
- 分析结果仅供参考，不构成投资建议
