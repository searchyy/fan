---
name: trading-signal
description: |
  Subscribe and retrieve on-chain Smart Money signals. Monitor trading activities of smart money addresses,
  including buy/sell signals, trigger price, current price, max gain, and exit rate.
  Use this skill when users are looking for investment opportunities — smart money signals can serve as valuable references for potential trades.
metadata:
  author: binance-web3-team
  version: "1.0"
---

# Trading Signal Skill

## Overview

This skill retrieves on-chain Smart Money trading signals to help users track professional investors:

- Get smart money buy/sell signals
- Compare signal trigger price with current price
- Analyze max gain and exit rate of signals
- Get token tags (e.g., Pumpfun, DEX Paid)

## API Endpoint

### Get Smart Money Signals

**Method**: POST

**URL**: 
```
https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money
```

**Request Headers**:
```
Content-Type: application/json
Accept-Encoding: identity
```

**Request Body**:
```json
{
    "smartSignalType": "",
    "page": 1,
    "pageSize": 100,
    "chainId": "CT_501"
}
```

**Request Parameters**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| smartSignalType | string | No | Signal type filter, empty string for all |
| page | number | Yes | Page number, starting from 1 |
| pageSize | number | Yes | Items per page, max 100 |
| chainId | string | Yes | Chain ID: `56` for bsc, `CT_501` for solana |

**Example Request**:
```bash
curl --location 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money' \
--header 'Content-Type: application/json' \
--header 'Accept-Encoding: identity' \
--data '{"smartSignalType":"","page":1,"pageSize":100,"chainId":"CT_501"}'
```

**Response Example**:
```json
{
    "code": "000000",
    "message": null,
    "messageDetail": null,
    "data": [
        {
            "signalId": 22179,
            "ticker": "symbol of the token",
            "chainId": "CT_501",
            "contractAddress": "NV...pump",
            "logoUrl": "/images/web3-data/public/token/logos/825C62EC6BE6.png",
            "chainLogoUrl": "https://bin.bnbstatic.com/image/admin_mgs_image_upload/20250303/42065e0a-3808-400e-b589-61c2dbfc0eac.png",
            "tokenDecimals": 6,
            "isAlpha": false,
            "launchPlatform": "Pumpfun",
            "mark": null,
            "isExclusiveLaunchpad": false,
            "alphaPoint": null,
            "tokenTag": {
                "Social Events": [
                    {"tagName": "DEX Paid", "languageKey": "wmp-label-update-dexscreener-social"}
                ],
                "Launch Platform": [
                    {"tagName": "Pumpfun", "languageKey": "wmp-label-title-pumpfun"}
                ],
                "Sensitive Events": [
                    {"tagName": "Smart Money Add Holdings", "languageKey": "wmp-label-title-smart-money-add-position"}
                ]
            },
            "smartSignalType": "SMART_MONEY",
            "smartMoneyCount": 5,
            "direction": "buy",
            "timeFrame": 883000,
            "signalTriggerTime": 1771903462000,
            "totalTokenValue": "3436.694044670495772073",
            "alertPrice": "0.024505932131088482",
            "alertMarketCap": "24505118.720436560690909782",
            "currentPrice": "0.025196",
            "currentMarketCap": "25135683.751234890220129783671668745",
            "highestPrice": "0.027244000000000000",
            "highestPriceTime": 1771927760000,
            "exitRate": 78,
            "status": "timeout",
            "maxGain": "5.4034",
            "signalCount": 23
        }
    ],
    "success": true
}
```

**Response Fields**:

### Basic Information
| Field | Type | Description |
|-------|------|-------------|
| signalId | number | Unique signal ID |
| ticker | string | Token symbol/name |
| chainId | string | Chain ID |
| contractAddress | string | Token contract address |
| logoUrl | string | Token icon URL path |
| chainLogoUrl | string | Chain icon URL |
| tokenDecimals | number | Token decimals |

### Tag Information
| Field | Type | Description |
|-------|------|-------------|
| isAlpha | boolean | Whether it's an Alpha token |
| launchPlatform | string | Launch platform (e.g., Pumpfun) |
| isExclusiveLaunchpad | boolean | Whether it's exclusive launchpad |
| alphaPoint | number | Alpha points (can be null) |
| tokenTag | object | Token tag categories |

### Signal Data
| Field | Type | Description |
|-------|------|-------------|
| smartSignalType | string | Signal type, e.g., `SMART_MONEY` |
| smartMoneyCount | number | Number of smart money addresses involved |
| direction | string | Trade direction: `buy` / `sell` |
| timeFrame | number | Time frame (milliseconds) |
| signalTriggerTime | number | Signal trigger timestamp (ms) |
| signalCount | number | Total signal count |

### Price Data
| Field | Type | Description |
|-------|------|-------------|
| totalTokenValue | string | Total trade value (USD) |
| alertPrice | string | Price at signal trigger |
| alertMarketCap | string | Market cap at signal trigger |
| currentPrice | string | Current price |
| currentMarketCap | string | Current market cap |
| highestPrice | string | Highest price after signal |
| highestPriceTime | number | Highest price timestamp (ms) |

### Performance Data
| Field | Type | Description |
|-------|------|-------------|
| exitRate | number | Exit rate (%) |
| status | string | Signal status: `active`/`timeout`/`completed` |
| maxGain | string | Maximum gain (%) |

## Token Tag Types

### Social Events
| Tag | Description |
|-----|-------------|
| DEX Paid | DEX paid promotion |

### Launch Platform
| Tag | Description |
|-----|-------------|
| Pumpfun | Pump.fun platform |
| Moonshot | Moonshot platform |

### Sensitive Events
| Tag | Description |
|-----|-------------|
| Smart Money Add Holdings | Smart money accumulating |
| Smart Money Reduce Holdings | Smart money reducing |
| Whale Buy | Whale buying |
| Whale Sell | Whale selling |

## Supported Chains

| Chain Name | chainId |
|------------|---------|
| BSC | 56 |
| Solana | CT_501 |

## Signal Status

| Status | Description |
|--------|-------------|
| active | Active, signal still valid |
| timeout | Timed out, exceeded observation period |
| completed | Completed, reached target or stop loss |

## Use Cases

1. **Track Smart Money**: Monitor professional investor trading behavior
2. **Discover Opportunities**: Get early signals when smart money buys
3. **Risk Alert**: Receive alerts when smart money starts selling
4. **Performance Analysis**: Analyze historical signal performance and max gains
5. **Strategy Validation**: Evaluate signal quality via exitRate and maxGain

## Example Requests

### Get Smart Money Signals on Solana
```bash
curl --location 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money' \
--header 'Content-Type: application/json' \
--header 'Accept-Encoding: identity' \
--data '{"smartSignalType":"","page":1,"pageSize":50,"chainId":"CT_501"}'
```

### Get Signals on BSC
```bash
curl --location 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/web/signal/smart-money' \
--header 'Content-Type: application/json' \
--header 'Accept-Encoding: identity' \
--data '{"smartSignalType":"","page":1,"pageSize":50,"chainId":"56"}'
```

## Notes

1. Token icon URL requires full domain prefix: `https://bin.bnbstatic.com` + logoUrl path
2. Chain icon URL (chainLogoUrl) is already a full URL
3. All timestamps are in milliseconds
4. maxGain is a percentage string
5. Signals may timeout (status=timeout), focus on active signals
6. Higher smartMoneyCount may indicate higher signal reliability
7. exitRate shows smart money exit status, high exitRate may indicate expired signal

---

## 信号质量评估框架（必须执行，不能跳过）

### 第一步：状态过滤

| status | 处理方式 |
|--------|---------|
| `active` | 继续评估 |
| `timeout` | 标注"⏰ 已超时"，降为仅参考历史表现 |
| `completed` | 标注"✅ 已完结"，用于复盘，不用于决策 |

**只有 active 信号才进入后续评分，timeout/completed 不做交易参考。**

### 第二步：信号可信度评分（满分5分）

| 维度 | 条件 | 得分 |
|------|------|------|
| 聪明钱数量 | smartMoneyCount ≥ 5 | +2 |
| 聪明钱数量 | smartMoneyCount = 3-4 | +1 |
| 出局率 | exitRate < 30%（聪明钱还在） | +2 |
| 出局率 | exitRate 30-60% | +1 |
| 出局率 | exitRate > 60% | 0（聪明钱已出，信号过期） |
| 触发后价格 | currentPrice > alertPrice（信号触发后还在涨） | +1 |

**评级标准：**
- 5分 → 🟢 高可信，可作为参考入场信号
- 3-4分 → 🟡 中可信，需结合其他维度验证
- 1-2分 → 🔴 低可信，仅作历史参考
- 0分 → ⬛ 无效，忽略

### 第三步：与当前市场状态交叉验证

收到信号后必须做：
1. 用 `query-token-info` 查该 token 当前实时价格 / 24h量 / 持有人
2. 对比 alertPrice vs currentPrice：价格差 > 30% 说明信号严重滞后
3. 用 `meme-rush` 检查该 token 是否仍在活跃榜单
4. 如果可行，用 `meme-contract-forensics` 验证 smartMoney 地址是否是真实高手还是庄家

### 输出格式规范

```
{序号}. {ticker} | {chainId} | {direction}方向
   触发价: ${alertPrice} → 当前价: ${currentPrice} | 最高价: ${highestPrice}
   聪明钱数: {smartMoneyCount} | 出局率: {exitRate}% | 最大涨幅: {maxGain}%
   信号时间: {signal_trigger_time} | 状态: {status}
   可信度评分: {score}/5 → {等级}
   ⚠️ 注意: [列出任何风险点]
   下一步: [建议的验证动作]
```

### 与其他 Skill 的联动

```
trading-signal 发现高可信信号
  → query-token-info 验证当前市场状态
  → meme-contract-forensics 验证 smartMoney 地址
  → wallet-playbook-analysis 深挖聪明钱打法
  → 决策：跟 / 观察 / 忽略
```
