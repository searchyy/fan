---
name: onchain-forensics
description: 链上取证与资金流还原技能。对任何可疑代币/合约进行完整的链上作案时间线还原，追踪资金流向，识别 rug pull、蜜罐、洗钱等恶意行为。当用户要求：(1) 追踪某个合约/地址的资金流向 (2) 还原项目跑路时间线 (3) 分析可疑交易和地址关联 (4) 检测 rug pull/蜜罐/闪电跑路 (5) 识别跨链洗钱路径 (6) 生成链上取证报告时使用。支持 EVM 链（ETH/Base/BSC/Arb 等）。
---

# 链上取证与资金流还原

## 核心理念

像刑侦一样还原链上犯罪现场：谁部署的、钱从哪来、怎么收割、怎么跑路、钱去了哪。

## 输入要求

至少提供以下之一：
- 合约地址（代币/挖矿/质押等）
- 部署者地址
- 项目名称 + 链（用于搜索）

## 分析流程

### Phase 1: 角色识别

从合约地址出发，反向追踪，识别所有关键角色：

| 角色 | 识别方法 |
|------|----------|
| 部署者 | 合约创建交易的 from 地址 |
| 资金来源 | 部署者的首笔入金（CEX 出金？Tornado？跨链？） |
| 合约本体 | V1/V2/多版本合约，各自功能 |
| 收割钱包 | 从合约提取资金或大额 swap 的地址 |
| 跨链中继 | 调用 bridge 合约的地址 |
| 分发工具 | Disperse.app / 批量转账合约 |
| 关联地址 | 与部署者有资金往来的地址 |

识别方法：
1. 查合约创建 tx → 拿到部署者
2. 查部署者历史 tx → 找资金来源（第一笔入金）
3. 查合约所有 internal tx → 找资金流出方向
4. 查部署者所有 tx → 找关联合约和地址
5. 对每个关联地址重复 2-4

### Phase 2: 时间线还原

按时间顺序记录所有关键事件，格式：

```
[YYYY-MM-DD HH:MM] 事件描述
  TX: 0x...
  From: 0x... → To: 0x...
  金额: X ETH ($Y)
  意义: [入金/部署/收割/转移/跨链/洗钱]
```

关键节点类型：
1. **入金** — 部署者获得初始资金
2. **部署** — 合约创建
3. **运营** — 用户交互期（mint/swap/stake）
4. **收割** — 从合约/池子提取资金
5. **烟雾** — 社交媒体掩护动作（发推/改名/声明）
6. **转移** — 资金在地址间转移
7. **跨链** — 通过 bridge 转移到其他链
8. **套现** — 最终变现（CEX 入金/OTC）

### Phase 3: 资金流图

绘制完整资金流向，格式：

```
[来源] ──金额──→ [目标]
  ├── [子流向1]
  └── [子流向2]
```

必须追踪到终点（CEX 入金 / bridge 出链 / 余额归零）。

### Phase 3.5: 跨链追踪

当发现资金通过 bridge 转移时，必须跨链继续追踪，不能在源链停下。

#### 识别跨链操作
在源链上查找以下特征：
- 调用已知 bridge 合约（Mayan/Wormhole/Stargate/LayerZero）
- 大额 ETH/token 转入 bridge 合约
- 交易 method 包含 forward/bridge/swap/relay 等关键词

#### Bridge API 查询

Mayan Protocol:
```
https://explorer-api.mayan.finance/v3/swaps?trader={address}
```
返回字段：sourceChain, destChain, fromAmount, toAmount, destAddress, status, fulfillTxHash

Wormhole:
```
https://api.wormholescan.io/api/v1/transactions?address={address}
```

#### 目标链追踪
1. 从 bridge API 获取目标链地址和 fulfillTxHash
2. 在目标链上查该地址余额和交易历史
3. 追踪每一跳直到资金停止移动或进入 CEX/混币器

#### Solana 追踪方法
```bash
# 余额
POST https://solana-rpc.publicnode.com
{"jsonrpc":"2.0","id":1,"method":"getBalance","params":["ADDRESS"]}

# 交易签名列表
{"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress","params":["ADDRESS",{"limit":20}]}

# 交易详情（jsonParsed 格式可直接看 transfer 指令）
{"jsonrpc":"2.0","id":1,"method":"getTransaction","params":["SIGNATURE",{"encoding":"jsonParsed","maxSupportedTransactionVersion":0}]}
```

备用 RPC: solana-rpc.publicnode.com（免费，有限流）

#### 跨链洗钱模式识别
- 落地后立即转移（<5分钟）→ 预编排脚本
- 多跳快速转移 → 烧地址模式（用完即弃）
- 汇集额外资金 → 混淆追踪（金额不匹配说明有其他来源）
- 最终进入 CEX → 可追溯（需执法配合）
- 最终进入混币器 → 追踪中断

### Phase 4: 合约机制分析

检查合约中的恶意机制：

| 检查项 | 方法 | 红旗信号 |
|--------|------|----------|
| 隐藏 mint | 查 mint/transfer 函数 | 无上限 mint、owner 可任意铸造 |
| 蜜罐机制 | 查 transfer 限制 | 买入正常卖出失败 |
| 可升级代理 | 查 proxy pattern | 可随时换逻辑合约 |
| 后门函数 | 查 owner-only 函数 | emergencyWithdraw、setFee(100%) |
| 假锁池 | 查 LP lock 合约 | 锁定时间极短、可提前解锁 |
| 假 renounce | 查 owner 变更历史 | renounce 后仍有控制权 |
| 税率操控 | 查 fee 相关变量 | 可动态调整到 100% |
| 白名单/黑名单 | 查 mapping + modifier | 选择性限制交易 |

### Phase 5: 社交取证（辅助）

如有项目社交账号，交叉验证：
- Twitter 创建时间 vs 合约部署时间
- 关键推文时间 vs 链上操作时间（是否同步放烟雾）
- 推文内容 vs 实际行为（说锁池实际没锁）
- 关联账号（转发/互动的可疑账号）

### Phase 6: 收支汇总

输出资金收支表：

| 指标 | 数值 | 说明 |
|------|------|------|
| 初始资金 | | 部署者入金 |
| 用户投入总额 | | mint/swap/stake 总计 |
| 受害地址数 | | 独立交互地址 |
| 套现金额 | | DEX swap + CEX 入金 |
| 跨链转移 | | bridge 金额 |
| 剩余余额 | | 各地址残留 |
| **净利润** | | 套现 + 跨链 - 初始资金 |

### Phase 7: 可追溯性评估

评估追回可能性：

| 线索 | 状态 | 说明 |
|------|------|------|
| CEX 出金 | ✅/❌ | 有 KYC 可追溯 |
| CEX 入金 | ✅/❌ | 套现路径可追溯 |
| ENS/域名 | ✅/❌ | 注册信息 |
| 社交账号 | ✅/❌ | 真实身份线索 |
| 跨链路径 | ✅/❌ | 目标链地址 |
| Tornado/混币 | ✅/❌ | 是否使用混币器 |

## 数据源与工具

按优先级：
1. **Blockscout API** — 免费无需 key，支持 EVM 链（Base/ETH/BSC/Arb/OP）
2. **Mayan Finance API** — 跨链记录查询（免费）
3. **Solana RPC** — solana-rpc.publicnode.com（免费，交易详情用 jsonParsed）
4. **DEX Screener** — 交易对、价格、流动性历史
5. **Arkham/Nansen**（如可用）— 地址标签、实体识别
6. **Wormhole Scan API** — Wormhole 跨链记录
7. **Disperse.app** — 批量转账记录
8. **Twitter/X** — 社交时间线

### Blockscout API 用法（推荐，免费无 key）

```bash
# 地址信息（含 creator、余额、是否合约）
https://{chain}.blockscout.com/api/v2/addresses/{addr}

# 交易列表（⚠️ 不支持 limit 参数，默认50条，用 next_page_params 分页）
https://{chain}.blockscout.com/api/v2/addresses/{addr}/transactions
# 分页：响应里有 next_page_params，带入下次请求；null 表示最后一页
# 示例：?block_number=xxx&index=yyy&items_count=50

# Internal 交易（同样用 next_page_params 分页）
https://{chain}.blockscout.com/api/v2/addresses/{addr}/internal-transactions

# Token 转账（同样用 next_page_params 分页）
https://{chain}.blockscout.com/api/v2/addresses/{addr}/token-transfers
```

Chain 域名: base.blockscout.com / eth.blockscout.com / bsc.blockscout.com / arbitrum.blockscout.com / optimism.blockscout.com

**分页策略：** 取证时拉最近 3-5 页（150-250条）覆盖关键事件即可。完整历史追踪循环到 `next_page_params = null`。

### Solana RPC 限流降级

publicnode.com 免费节点 QPS 约 10 req/s。遇限时：
1. 每次请求 sleep 200ms
2. 备用：`https://api.mainnet-beta.solana.com`（官方，同限）
3. 签名列表太长 → 只取最近 20 条精细分析，不必追全量历史

### Etherscan V1 API（已废弃）

注意：Basescan 等已迁移到 V2 付费 API，V1 返回 deprecated 错误。优先用 Blockscout。

### 跨链 Bridge API

```bash
# Mayan Protocol
https://explorer-api.mayan.finance/v3/swaps?trader={address}

# Wormhole
https://api.wormholescan.io/api/v1/transactions?address={address}
```

## 输出格式

最终报告结构：

```
# [项目名] 链上取证报告

## 概要
[一段话总结：谁干的、怎么干的、卷了多少钱、钱去了哪]

## 关键角色
[角色表格]

## 作案时间线
[按时间排列的事件]

## 资金流图
[资金流向图]

## 合约机制分析
[恶意机制检查结果]

## 收支汇总
[资金收支表]

## 可疑操作摘要
[编号列表，每条一个可疑操作 + 解释]

## 可追溯性评估
[追回可能性分析]

## 结论
评级：[CONFIRMED_SCAM / HIGHLY_SUSPICIOUS / SUSPICIOUS / INCONCLUSIVE]
[最终判断和建议]
```

## 评级标准

- **CONFIRMED_SCAM**: 资金流完整闭环，明确跑路证据
- **HIGHLY_SUSPICIOUS**: 多个强烈红旗，资金流异常但未完全确认
- **SUSPICIOUS**: 部分可疑行为，需进一步监控
- **INCONCLUSIVE**: 数据不足，无法下结论

## 常见跑路模式速查

| 模式 | 特征 | 时间窗口 |
|------|------|----------|
| 闪电 Rug | 部署→收割→跑路 <24h | 极短 |
| 慢性 Rug | 逐步抽流动性，持续数周 | 中等 |
| 蜜罐 | 买入正常卖出失败 | 持续 |
| 假迁移 | V1→V2 名义迁移实际跑路 | 短 |
| 税率操控 | 逐步提高税率到 100% | 中等 |
| Oracle 操控 | 操纵价格预言机套利 | 极短 |
| 跨链洗钱 | 多链多跳转移资金 | 短-中 |
