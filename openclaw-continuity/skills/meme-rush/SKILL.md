---
name: meme-rush
description: |
  Meme token fast-trading assistant with two core capabilities:
  1. Meme Rush - Real-time meme token lists from launchpads (Pump.fun, Four.meme, etc.) across new, finalizing, and migrated stages
  2. Topic Rush - AI-powered market hot topics with associated tokens ranked by net inflow
  Use this skill when users ask about new meme tokens, meme launches, bonding curve, migration status,
  pump.fun tokens, four.meme tokens, fast meme trading, market hot topics, or trending narratives.
metadata:
  author: binance-web3-team
  version: "1.0"
---

# Meme Rush Skill

## Overview

### Meme Rush — Launchpad token lifecycle tracking

| rankType | Stage | Description |
|----------|-------|-------------|
| 10 | New | Freshly created meme tokens still on bonding curve |
| 20 | Finalizing | Tokens about to migrate (bonding curve nearly complete) |
| 30 | Migrated | Tokens that just migrated to DEX |

### Topic Rush — AI-powered market hot topic discovery

| rankType | Stage | Description |
|----------|-------|-------------|
| 10 | Latest | Newest hot topics |
| 20 | Rising | Rising topics with all-time high inflow between $1k–$20k |
| 30 | Viral | Viral topics with all-time high inflow above $20k |

## Use Cases

1. **Snipe New Launches**: Find freshly created meme tokens on Pump.fun, Four.meme, etc.
2. **Migration Watch**: Monitor tokens about to migrate — catch early DEX liquidity
3. **Post-Migration Trading**: Find just-migrated tokens for early DEX entry
4. **Filter by Dev Behavior**: Exclude dev wash trading, check dev sell %, burned tokens
5. **Holder Analysis**: Filter by top10 %, dev %, sniper %, insider %, bundler % holdings
6. **Smart Filtering**: Combine bonding curve progress, liquidity, volume, market cap filters
7. **Topic Discovery**: Find AI-generated market hot topics and their associated tokens
8. **Narrative Trading**: Trade tokens grouped by trending narratives, sorted by net inflow

## Supported Chains

| Chain | chainId |
|-------|---------|
| BSC | 56 |
| Solana | CT_501 |

## Protocol Reference

| Protocol Code | Platform | Chain |
|---------------|----------|-------|
| 1001 | Pump.fun | Solana |
| 1002 | Moonit | Solana |
| 1003 | Pump AMM | Solana |
| 1004 | Launch Lab | Solana |
| 1005 | Raydium V4 | Solana |
| 1006 | Raydium CPMM | Solana |
| 1007 | Raydium CLMM | Solana |
| 1008 | BONK | Solana |
| 1009 | Dynamic BC | Solana |
| 1010 | Moonshot | Solana |
| 1011 | Jup Studio | Solana |
| 1012 | Bags | Solana |
| 1013 | Believer | Solana |
| 1014 | Meteora DAMM V2 | Solana |
| 1015 | Meteora Pools | Solana |
| 1016 | Orca | Solana |
| 2001 | Four.meme | BSC |
| 2002 | Flap | BSC |

---

## API 1: Meme Rush Rank List

### Method: POST

**URL**:
```
https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/rank/list
```

**Headers**: `Content-Type: application/json`, `Accept-Encoding: identity`

### Request Body

**Required Parameters**:

| Field | Type | Description |
|-------|------|-------------|
| chainId | string | Chain ID: `56` for bsc, `CT_501` for solana |
| rankType | integer | `10`=New, `20`=Finalizing, `30`=Migrated |

**Pagination & Keyword**:

| Field | Type | Description |
|-------|------|-------------|
| limit | integer | Max results per request (default 40, max 200) |
| keywords | string[] | Include symbols matching keywords (max 5) |
| excludes | string[] | Exclude symbols (max 5) |

**Token Filters (Min/Max pairs)**:

| Filter | Type | Description |
|--------|------|-------------|
| progressMin/Max | string | Bonding curve progress (0-100%) |
| tokenAgeMin/Max | long | Token age |
| holdersMin/Max | long | Holder count |
| liquidityMin/Max | string | Liquidity (USD) |
| volumeMin/Max | string | 24h volume (USD) |
| marketCapMin/Max | string | Market cap (USD) |
| countMin/Max | long | Total trade count |
| countBuyMin/Max | long | Buy trade count |
| countSellMin/Max | long | Sell trade count |

**Holder Distribution Filters (Min/Max pairs)**:

| Filter | Type | Description |
|--------|------|-------------|
| holdersTop10PercentMin/Max | string | Top10 holder % |
| holdersDevPercentMin/Max | string | Dev holder % |
| holdersSniperPercentMin/Max | string | Sniper holder % |
| holdersInsiderPercentMin/Max | string | Insider holder % |
| bundlerHoldingPercentMin/Max | string | Bundler holder % |
| newWalletHoldingPercentMin/Max | string | New wallet holder % |
| bnHoldingPercentMin/Max | string | Binance wallet holder % |
| bnHoldersMin/Max | long | Binance wallet holder count |
| kolHoldersMin/Max | long | KOL holder count |
| proHoldersMin/Max | long | Pro holder count |

**Dev & Launch Filters**:

| Field | Type | Description |
|-------|------|-------------|
| devMigrateCountMin/Max | long | Dev historical migration count |
| devPosition | integer | Dev position: `2`=dev sold all (pass when checked) |
| devBurnedToken | integer | Dev burned tokens: `1`=yes |
| excludeDevWashTrading | integer | Exclude dev wash trading: `1`=yes |
| excludeInsiderWashTrading | integer | Exclude insider wash trading: `1`=yes |

**Other Filters**:

| Field | Type | Description |
|-------|------|-------------|
| protocol | integer[] | Launchpad protocol codes (see Protocol Reference) |
| exclusive | integer | Binance exclusive token: `0`=no, `1`=yes |
| paidOnDexScreener | integer | Paid on DexScreener |
| pumpfunLiving | integer | Pump.fun live stream: `1`=yes |
| cmcBoost | integer | CMC paid boost: `1`=yes |
| globalFeeMin/Max | string | Trading fee (Solana only) |
| pairAnchorAddress | string[] | Quote token addresses |
| tokenSocials.atLeastOne | integer | Has at least one social: `1`=yes |
| tokenSocials.socials | string[] | Specific socials: `website`, `twitter`, `telegram` |

### Example Request

```bash
curl -X POST 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/rank/list' \
-H 'Content-Type: application/json' \
-H 'Accept-Encoding: identity' \
-d '{"chainId":"CT_501","rankType":10,"limit":20}'
```

### Response (`data.tokens[]`)

**Core Fields**:

| Field | Type | Description |
|-------|------|-------------|
| chainId | string | Chain ID |
| contractAddress | string | Contract address |
| symbol | string | Token symbol |
| name | string | Token name |
| decimals | integer | Token decimals |
| icon | string | Logo URL (prefix `https://bin.bnbstatic.com`) |
| price | string | Current price (USD) |
| priceChange | string | 24h price change (%) |
| marketCap | string | Market cap (USD) |
| liquidity | string | Liquidity (USD) |
| volume | string | 24h volume (USD) |
| holders | long | Holder count |
| progress | string | Bonding curve progress (%, append `%` directly) |
| protocol | integer | Launchpad protocol code |
| exclusive | integer | Binance exclusive: 0/1 |

**Trade Counts**:

| Field | Type | Description |
|-------|------|-------------|
| count | long | 24h total trades |
| countBuy | long | 24h buy trades |
| countSell | long | 24h sell trades |

**Holder Distribution** (all string, already in %, append `%` directly):

| Field | Description |
|-------|-------------|
| holdersTop10Percent | Top10 holders % |
| holdersDevPercent | Dev holders % |
| holdersSniperPercent | Sniper holders % |
| holdersInsiderPercent | Insider holders % |
| bnHoldingPercent | Binance wallet holders % |
| kolHoldingPercent | KOL holders % |
| proHoldingPercent | Pro holders % |
| newWalletHoldingPercent | New wallet holders % |
| bundlerHoldingPercent | Bundler holders % |

**Dev & Migration Info**:

| Field | Type | Description |
|-------|------|-------------|
| devAddress | string | Dev wallet address |
| devSellPercent | string | Dev sell % |
| devMigrateCount | long | Dev historical migration count |
| devPosition | integer | `2`=dev sold all position |
| migrateStatus | integer | `0`=not migrated, `1`=migrated |
| migrateTime | long | Migration timestamp (ms) |
| createTime | long | Token creation timestamp (ms) |

**Tags & Flags**:

| Field | Type | Description |
|-------|------|-------------|
| tagDevWashTrading | integer | Dev wash trading: 1=yes |
| tagInsiderWashTrading | integer | Insider wash trading: 1=yes |
| tagDevBurnedToken | integer | Dev burned tokens: 1=yes |
| tagPumpfunLiving | integer | Pump.fun live: 1=yes |
| tagCmcBoost | integer | CMC paid: 1=yes |
| paidOnDexScreener | integer | DexScreener paid: 1=yes |
| launchTaxEnable | integer | Has launch tax: 1=yes |
| taxRate | string | Trading tax rate (%) |
| globalFee | string | Trading fee (Solana only) |

**Social Links**:

| Field | Type | Description |
|-------|------|-------------|
| socials.website | string | Website URL |
| socials.twitter | string | Twitter URL |
| socials.telegram | string | Telegram URL |

**AI Narrative**:

| Field | Type | Description |
|-------|------|-------------|
| narrativeText.en | string | AI narrative (English) |
| narrativeText.cn | string | AI narrative (Chinese) |

---

## API 2: Topic Rush Rank List

### Method: GET

**URL**:
```
https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/social-rush/rank/list
```

**Headers**: `Accept-Encoding: identity`

### Request Parameters

**Required Parameters**:

| Field | Type | Description |
|-------|------|-------------|
| chainId | string | Chain ID: `56`, `CT_501` |
| rankType | integer | `10`=Latest, `20`=Rising, `30`=Viral |
| sort | integer | Sort by: `10`=create time, `20`=net inflow, `30`=viral time |

> **Sort convention**: When the user does not specify a sort preference, use `sort=10` (create time) for Latest/Rising, and `sort=30` (viral time) for Viral.

**Optional Parameters**:

| Field | Type | Description |
|-------|------|-------------|
| asc | boolean | `true`=ascending, `false`=descending |
| keywords | string | Keyword filter (case-insensitive, contains match) |
| topicType | string | Topic type filter, comma-separated for multiple |
| tokenSizeMin/Max | integer | Associated token count range |
| netInflowMin/Max | string | Topic net inflow range (USD) |

### Example Request

```bash
curl 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/social-rush/rank/list?chainId=CT_501&rankType=30&sort=30&asc=false' \
-H 'Accept-Encoding: identity'
```

### Response (`data[]`)

**Topic Fields**:

| Field | Type | Description |
|-------|------|-------------|
| topicId | string | Topic unique ID |
| chainId | string | Chain ID |
| name | object | Multi-language topic name (`topicNameEn`, `topicNameCn`, etc.) |
| type | string | Topic type/category |
| close | integer | Topic closed: `0`=no, `1`=yes |
| topicLink | string | Related tweet/post URL |
| createTime | long | Topic creation timestamp (ms) |
| progress | string | Topic progress (pre-formatted %, append `%` directly) |
| aiSummary | object | AI-generated topic narrative |
| topicNetInflow | string | Total net inflow (USD) |
| topicNetInflow1h | string | 1h net inflow (USD) |
| topicNetInflowAth | string | All-time high net inflow (USD) |
| tokenSize | integer | Number of associated tokens |
| deepAnalysisFlag | integer | Deep analysis available: `1`=yes |

**Token List** (`tokenList[]` within each topic):

| Field | Type | Description |
|-------|------|-------------|
| chainId | string | Chain ID |
| contractAddress | string | Contract address |
| symbol | string | Token symbol |
| icon | string | Logo URL (prefix `https://bin.bnbstatic.com`) |
| decimals | integer | Token decimals |
| createTime | long | Token creation timestamp (ms) |
| marketCap | string | Market cap (USD) |
| liquidity | string | Liquidity (USD) |
| priceChange24h | string | 24h price change (pre-formatted %, append `%`) |
| netInflow | string | Token net inflow since topic creation (USD) |
| netInflow1h | string | Token 1h net inflow (USD) |
| volumeBuy / volumeSell | string | Buy / Sell volume since topic creation (USD) |
| volume1hBuy / volume1hSell | string | 1h buy / sell volume (USD) |
| uniqueTrader{5m,1h,4h,24h} | long | Unique traders by period |
| count{5m,1h,4h,24h} | long | Trade count by period |
| holders | long | Holder count |
| kolHolders | long | KOL holder count |
| smartMoneyHolders | long | Smart money holder count |
| protocol | integer | Launchpad protocol code (`0`/null = DEX token) |
| internal | integer | On bonding curve: `0`=no, `1`=yes |
| migrateStatus | integer | Migrated: `0`=no, `1`=yes |

---

## Notes

1. Only `chainId` and `rankType` are required; all other parameters are optional filters
2. Percentage fields (progress, holder %, dev sell %, tax rate) are pre-formatted — append `%` directly
3. `taxRate` for protocol=2001 (Four.meme) only shows on Migrated list; for protocol=2002 (Flap) shows on all lists
4. Icon URLs require prefix: `https://bin.bnbstatic.com` + path

---

## 过滤规则（必须执行）

### 强制排除（直接丢弃，不展示）
- `tagDevWashTrading = 1` — dev 洗盘，直接排除
- `exclusive = 1` — 币安 Alpha 独家代币（可能刷量），排除或单独标注"Alpha专区，稳定性未知"
- `tagInsiderWashTrading = 1` — 内部人洗盘，排除
- holders < 20 — 持有人太少，非正常盘

### 风险高亮（展示但必须标红/⚠️）
- `launchTaxEnable = 1` → ⚠️ 有launch税（显示税率）
- `tagCmcBoost = 1` → ⚠️ CMC付费推广（可能是营销盘）
- `paidOnDexScreener = 1` → ⚠️ DexScreener付费（注意区分真实热度）
- `holdersTop10Percent > 80` → ⚠️ 筹码高度集中
- `holdersSniperPercent > 20` → ⚠️ 狙击手占比偏高
- `bundlerHoldingPercent > 15` → ⚠️ bundler占比偏高

### 参考过滤预设（两档）

**稳健扫描**（BSC，迁移后，适合老板日常扫）：
```json
{
  "chainId": "56", "rankType": 30, "limit": 30,
  "holdersMin": 100,
  "liquidityMin": "5000",
  "volumeMin": "10000",
  "excludeDevWashTrading": 1,
  "excludeInsiderWashTrading": 1,
  "holdersTop10PercentMax": "80",
  "devPosition": 2
}
```

**激进扫描**（BSC，新盘，捕捉早期机会）：
```json
{
  "chainId": "56", "rankType": 10, "limit": 50,
  "holdersMin": 30,
  "progressMin": "60",
  "excludeDevWashTrading": 1
}
```

---

## 输出格式规范

不要 dump 原始 JSON。每个代币按以下格式输出：

```
{序号}. {symbol} | {name}
   MC: ${marketCap} | 流动性: ${liquidity} | 24h量: ${volume}
   持有者: {holders} | 进度: {progress}% | 创建: {age}
   Top10: {holdersTop10Percent}% | Dev卖出: {devSellPercent}%
   ⚠️ 风险: [列出所有风险标记]
   链接: CA={contractAddress}
```

最后附一句话总结该轮扫描质量（如："本轮BSC新盘12个，3个有洗盘标记已排除，推荐关注 XXX / YYY"）。

如果过滤后没有可靠标的，直接说："本轮过滤后无推荐标的"，不要强行推荐垃圾盘。

---

## 与其他 Skill 的联动

发现值得关注的标的后：
1. → `query-token-info` 拿实时价格 / K线 / 持有人分布
2. → `meme-contract-forensics` 做合约取证（谁是庄家）
3. → `alphai-twitter` 查该 token 的社媒讨论热度
4. → `lobster-evolution` 提炼本轮扫描规律
