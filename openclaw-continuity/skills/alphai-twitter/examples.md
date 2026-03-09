# 推特模块代码示例

## Python 完整示例

### 基础：关注 KOL + 拉取推文

```python
import requests
import json

DEX_COOKIE = "你的dex_cookie值"
BASE_URL = "https://b.alph.ai/smart-web-gateway"

headers = {
    "Cookie": f"dex_cookie={DEX_COOKIE}",
    "Content-Type": "application/json"
}

# 1. 关注 KOL
def follow_kol(username):
    resp = requests.post(f"{BASE_URL}/tracker/x/follow", headers=headers, json={
        "username": username,
        "operationType": 1  # 1=关注, 0=取消
    })
    print(f"关注 {username}: {resp.json()}")

# 2. 配置监控项
def config_monitor():
    resp = requests.post(f"{BASE_URL}/tracker/x/config", headers=headers, json={
        "send": True,        # 直接发推
        "retweeted": True,   # 转发
        "replied_to": True,  # 回复
        "quoted": True,      # 引用
        "follow": False,     # 关注事件
        "profile": False,    # 个人资料变更
        "icon": False,       # 头像变更
        "nick": False,       # 昵称变更
        "banner": False,     # 横幅变更
        "account": False     # 账号变更
    })
    print(f"配置监控: {resp.json()}")

# 3. 拉取某 KOL 的推文列表
def get_kol_tweets(username, page_size=20):
    resp = requests.post(f"{BASE_URL}/tracker/x/myList", headers=headers, json={
        "username": username,
        "pageNum": 1,
        "pageSize": page_size,
        "sort": "desc"
    })
    data = resp.json()
    tweets = data.get("data", {}).get("list", [])

    for tweet in tweets:
        tweet_type = tweet.get("type", "unknown")
        text = tweet.get("text", "")
        created_at = tweet.get("created_at", "")

        print(f"[{tweet_type}] {created_at}")
        print(f"  正文: {text[:100]}")

        # 如果有引用/回复的原始推文
        referenced = tweet.get("referenced")
        if referenced:
            print(f"  引用: {referenced.get('text', '')[:100]}")
        print()

    return tweets

# 4. 翻译推文
def translate_tweet(text, to_lang="cn"):
    resp = requests.post(f"{BASE_URL}/tracker/x/transTexts", headers=headers, json={
        "from": "en",
        "to": to_lang,
        "text": text
    })
    return resp.json().get("data", {}).get("result", "")

# 使用示例
follow_kol("cz_binance")
config_monitor()
tweets = get_kol_tweets("cz_binance", page_size=20)

# 翻译英文推文
for tweet in tweets:
    if tweet.get("text"):
        translated = translate_tweet(tweet["text"])
        print(f"原文: {tweet['text'][:80]}")
        print(f"翻译: {translated[:80]}")
        print()
```

---

### 进阶：WebSocket 实时监控 + 推文分析

```python
import asyncio
import websockets
import requests
import json
import time
import re

DEX_COOKIE = "你的dex_cookie值"
BASE_URL = "https://b.alph.ai/smart-web-gateway"

headers = {
    "Cookie": f"dex_cookie={DEX_COOKIE}",
    "Content-Type": "application/json"
}

def get_listen_key():
    """获取 listenKey"""
    resp = requests.post(f"{BASE_URL}/ws/listenkey", headers=headers, json={})
    result = resp.json()
    code = result.get("data", {}).get("code") or result.get("code")
    if code == "200":
        return result["data"]["listenKey"], result["data"].get("expiresTtl", 3600)
    raise Exception(f"获取 listenKey 失败: {result}")

def extract_contract_addresses(text):
    """从推文中提取可能的合约地址（CA）"""
    # 匹配以太坊/BSC 合约地址
    eth_pattern = r'0x[a-fA-F0-9]{40}'
    # 匹配 Solana 合约地址
    sol_pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'

    eth_addresses = re.findall(eth_pattern, text)
    sol_addresses = [addr for addr in re.findall(sol_pattern, text) if len(addr) >= 32]

    return {"eth": eth_addresses, "sol": sol_addresses}

def process_tweet(tweet_data):
    """处理收到的推文"""
    tweet_type = tweet_data.get("type", "unknown")
    text = tweet_data.get("text", "")
    created_at = tweet_data.get("created_at", "")

    print(f"\n{'='*60}")
    print(f"[{tweet_type}] {created_at}")
    print(f"正文: {text}")

    # 检查引用的推文
    referenced = tweet_data.get("referenced")
    if referenced:
        print(f"引用: {referenced.get('text', '')}")

    # 提取 CA
    all_text = text
    if referenced:
        all_text += " " + referenced.get("text", "")

    cas = extract_contract_addresses(all_text)
    if cas["eth"] or cas["sol"]:
        print(f"⚠️ 发现合约地址:")
        for addr in cas["eth"]:
            print(f"  ETH/BSC: {addr}")
        for addr in cas["sol"]:
            print(f"  SOL: {addr}")

    return tweet_data

async def subscribe_and_monitor(listen_key):
    """连接 WebSocket 并监控推特"""
    uri = f"wss://ws.alph.ai/stream/ws?listenKey={listen_key}"

    async with websockets.connect(uri) as ws:
        print(f"[{time.strftime('%H:%M:%S')}] WebSocket 连接成功")

        # 订阅推特数据
        await ws.send(json.dumps({
            "id": "0c1bfd5cb47fb8051e62d333b99916e72c695203fa9d94b171eed267486efb0c",
            "event": "SUBSCRIBE",
            "params": [{"type": "user_tracker_x"}]
        }))
        print("已订阅推特(X)实时推送")

        async for message in ws:
            data = json.loads(message)
            process_tweet(data)

async def run_with_auto_renew():
    """自动续期 + 持续监听"""
    while True:
        try:
            listen_key, expires_ttl = get_listen_key()
            print(f"[{time.strftime('%H:%M:%S')}] listenKey 获取成功，{expires_ttl}秒后过期")

            renew_after = int(expires_ttl * 0.8)

            listen_task = asyncio.create_task(subscribe_and_monitor(listen_key))
            renew_task = asyncio.create_task(asyncio.sleep(renew_after))

            done, pending = await asyncio.wait(
                [listen_task, renew_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()

            print(f"\n[{time.strftime('%H:%M:%S')}] 续期 listenKey...")

        except Exception as e:
            print(f"连接异常: {e}，5秒后重试...")
            await asyncio.sleep(5)

# 启动
asyncio.run(run_with_auto_renew())
```

---

### 批量操作：关注多个 KOL + 拉取推文分析

```python
import requests
import json
import time

DEX_COOKIE = "你的dex_cookie值"
BASE_URL = "https://b.alph.ai/smart-web-gateway"

headers = {
    "Cookie": f"dex_cookie={DEX_COOKIE}",
    "Content-Type": "application/json"
}

def batch_follow_kols(kol_list):
    """批量关注 KOL"""
    results = []
    for username in kol_list:
        resp = requests.post(f"{BASE_URL}/tracker/x/follow", headers=headers, json={
            "username": username,
            "operationType": 1
        })
        results.append({"username": username, "result": resp.json()})
        time.sleep(0.5)  # 避免请求过快
        print(f"✅ 已关注: {username}")
    return results

def batch_get_tweets(kol_list, page_size=20):
    """批量拉取 KOL 推文"""
    all_tweets = {}
    for username in kol_list:
        resp = requests.post(f"{BASE_URL}/tracker/x/myList", headers=headers, json={
            "username": username,
            "pageNum": 1,
            "pageSize": page_size,
            "sort": "desc"
        })
        data = resp.json()
        tweets = data.get("data", {}).get("list", [])
        all_tweets[username] = tweets
        time.sleep(0.5)
        print(f"✅ {username}: 获取到 {len(tweets)} 条推文")
    return all_tweets

# 使用示例
kols = ["cz_binance", "VitalikButerin", "elonmusk"]

# 批量关注
batch_follow_kols(kols)

# 批量拉取推文
all_tweets = batch_get_tweets(kols, page_size=20)

# 输出统计
for username, tweets in all_tweets.items():
    type_counts = {}
    for t in tweets:
        tt = t.get("type", "unknown")
        type_counts[tt] = type_counts.get(tt, 0) + 1

    print(f"\n{username}: {len(tweets)} 条推文")
    for tt, count in type_counts.items():
        print(f"  {tt}: {count} 条")
```

---

## JavaScript 完整示例

### WebSocket 实时监控

```javascript
const DEX_COOKIE = "你的dex_cookie值";
const BASE_URL = "https://b.alph.ai/smart-web-gateway";

const headers = {
    "Cookie": `dex_cookie=${DEX_COOKIE}`,
    "Content-Type": "application/json"
};

async function getListenKey() {
    const resp = await fetch(`${BASE_URL}/ws/listenkey`, {
        method: "POST", headers, body: JSON.stringify({})
    });
    const result = await resp.json();
    const code = result.data?.code || result.code;
    if (code === "200") {
        return { listenKey: result.data.listenKey, expiresTtl: result.data.expiresTtl || 3600 };
    }
    throw new Error(`获取 listenKey 失败: ${JSON.stringify(result)}`);
}

function extractCA(text) {
    const ethAddresses = text.match(/0x[a-fA-F0-9]{40}/g) || [];
    return ethAddresses;
}

function processTweet(data) {
    const { type, text, created_at, referenced } = data;

    console.log(`\n[${type}] ${created_at}`);
    console.log(`正文: ${text}`);
    if (referenced) {
        console.log(`引用: ${referenced.text}`);
    }

    // 提取 CA
    const allText = text + (referenced?.text || "");
    const cas = extractCA(allText);
    if (cas.length > 0) {
        console.log(`⚠️ 发现合约地址: ${cas.join(", ")}`);
    }
}

async function startMonitor() {
    while (true) {
        try {
            const { listenKey, expiresTtl } = await getListenKey();
            console.log(`listenKey 获取成功，${expiresTtl}秒后过期`);

            const ws = new WebSocket(`wss://ws.alph.ai/stream/ws?listenKey=${listenKey}`);

            ws.onopen = () => {
                console.log("WebSocket 连接成功");
                ws.send(JSON.stringify({
                    id: "0c1bfd5cb47fb8051e62d333b99916e72c695203fa9d94b171eed267486efb0c",
                    event: "SUBSCRIBE",
                    params: [{ type: "user_tracker_x" }]
                }));
                console.log("已订阅推特(X)实时推送");
            };

            ws.onmessage = (event) => processTweet(JSON.parse(event.data));

            // 等待续期
            await new Promise(resolve => setTimeout(resolve, expiresTtl * 0.8 * 1000));
            ws.close();
            console.log("续期 listenKey...");

        } catch (e) {
            console.error(`异常: ${e.message}，5秒后重试...`);
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
    }
}

startMonitor();
```

---

## 场景示例

### 场景：监控 CZ，发现 CA 后查流动性

```python
# 伪代码流程
async def on_tweet(tweet_data):
    """收到推文时的处理逻辑"""

    # 1. 提取推文中的所有文本
    text = tweet_data.get("text", "")
    ref_text = tweet_data.get("referenced", {}).get("text", "")
    all_text = f"{text} {ref_text}"

    # 2. 提取合约地址
    cas = extract_contract_addresses(all_text)

    if not cas["eth"] and not cas["sol"]:
        return  # 没有 CA，跳过

    # 3. 查询每个 CA 的行情
    for ca in cas["eth"]:
        ticker = requests.get(
            f"{BASE_URL}/ticker/{ca}/eth",
            headers=headers
        ).json()
        # 比较流动性，找到最大的

    for ca in cas["sol"]:
        ticker = requests.get(
            f"{BASE_URL}/ticker/{ca}/sol",
            headers=headers
        ).json()

    # 4. 推送到 Telegram（由同事的 agent 处理）
    # send_to_telegram(best_ca_info)
```
