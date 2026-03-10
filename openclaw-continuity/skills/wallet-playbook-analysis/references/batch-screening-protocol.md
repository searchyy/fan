# Batch Wallet Screening Protocol
# 批量地址筛选与早期高胜率评级协议

## 适用场景
- 用户给出一批地址（10-100个）需要快速筛选
- 目标是找出"以小博大、早期入场、高胜率"的可跟踪地址
- 输出：分级跟踪名单（S/A/排除）

## 数据源
- **优先使用 Moralis API**（BSC ERC20转账记录）
  - Endpoint: `https://deep-index.moralis.io/api/v2.2/{address}/erc20/transfers`
  - Chain: `bsc`，每地址最多拉5页×100条=500条记录
  - Header: `X-API-Key: {MORALIS_KEY}`
- Key存储：环境变量 `MORALIS_KEY`，或用户会话中提供

## 噪音过滤规则（与单地址分析一致）
1. `possible_spam=true` 直接丢弃
2. 买卖间隔 < 120秒 → 秒狙噪音，排除
3. 只有IN、无OUT、总量 < 0.001 → airdrop dust，排除
4. 有效token数 < 3 → 样本不足，标记 ⬜ 数据不足

## 早期高胜率评分维度（满分5分）

> **前置要求**：所有维度的统计必须在噪音过滤（120s阈值 + spam + dust）之后进行。

| 维度 | 条件 | 分值 |
|------|------|------|
| 早期入场 | 平均持仓时间 < 3小时 | +2 |
| 高出局率 | 已实现出局率 ≥ 25% | +2 |
| 反复加仓 | 噪音过滤后，≥2个品种被反复买入3次+ | +1 |

## 分级标准

| 等级 | 得分 | 含义 | 跟踪策略 |
|------|------|------|---------|
| S级 | 5分 | 三维全中，核心跟踪 | 监控首次买入动作，买入即跟 |
| A级 | 3-4分 | 部分优势，观察跟踪 | 与S级交叉验证时作为二次确认 |
| 排除 | ≤2分 或出局率=0% | 囤token型/数据不足 | 不跟踪 |

## 特殊排除规则
- 出局率 = 0% 且活口数量 > 50 → 囤token模式，排除（即使资金量大）
- 平均持仓 > 200h → 长期套牢风险高，降为参考
- 噪音条数 / 总条数 > 80% → 地址主要是噪音操作，降级

## 批量脚本位置
`/home/fan/.openclaw/workspace/scripts/batch_wallet_analysis_moralis.py`

## 输出文件规范
- 完整报告: `reports/wallet_batch_{YYYYMMDD_HHMMSS}.txt`
- 精筛跟踪名单（文字）: `reports/high_winrate_tracking.txt`
- 精筛跟踪名单（JSON）: `reports/high_winrate_watchlist.json`
- 发送给用户的文件：两份都发（txt给人看，json给后续自动化用）

## 跟踪名单字段规范（JSON）
```json
{
  "tier": "S|A",
  "address": "0x...",
  "name": "备注名",
  "exit_rate": 0.67,
  "avg_hold_h": 1.68,
  "multi_buy": 11,
  "style": "首板型|二波型|接飞刀型",
  "score": 5,
  "note": "关键特征一句话"
}
```

## 跟踪动作建议
- **S级**：监控新增买入 → 同票首次买入即关注 → 3次以上买入视为强信号
- **A级**：与S级交叉操作同票时权重加分，不单独跟进
- **更新周期**：建议每周重新拉一次数据，更新出局率和活口状态
