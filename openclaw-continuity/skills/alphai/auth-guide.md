# Alph.ai 认证与 WebSocket 连接指南

本文档是所有 API 调用的基础，请在使用任何模块前先阅读。

---

## 1. 获取 dex_cookie

`dex_cookie` 是 Alph.ai 所有 API 和 WebSocket 连接的认证凭证，有效期 **14 天**。

### 获取步骤

1. 用浏览器登录 [alph.ai](https://alph.ai)
2. 打开浏览器开发者工具（快捷键 `F12` 或 `Cmd+Option+I`）
3. 依次进入：**Application** → **Cookies** → **alph.ai**
4. 找到 `dex_cookie` 字段，复制其 Value

### 在请求中使用

所有 HTTP 请求都需要在 `Cookie` header 中携带 `dex_cookie`：

```
Cookie: dex_cookie=<your_dex_cookie_value>
```

### 代码示例

**Python:**
```python
import requests

DEX_COOKIE = "你的dex_cookie值"

headers = {
    "Cookie": f"dex_cookie={DEX_COOKIE}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://b.alph.ai/smart-web-gateway/xxx",
    headers=headers,
    json={}
)
```

**JavaScript:**
```javascript
const DEX_COOKIE = "你的dex_cookie值";

const response = await fetch("https://b.alph.ai/smart-web-gateway/xxx", {
    method: "POST",
    headers: {
        "Cookie": `dex_cookie=${DEX_COOKIE}`,
        "Content-Type": "application/json"
    },
    body: JSON.stringify({})
});
```

### 注意事项

- dex_cookie 有效期 **14 天**，过期后需要重新从浏览器获取
- 请妥善保管 dex_cookie，不要提交到代码仓库或公开分享
- 建议使用环境变量或配置文件管理 dex_cookie

---

## 2. 获取 listenKey（WebSocket 必需）

如果需要接收 WebSocket 实时推送（行情、推特监控等），必须先获取 `listenKey`。

### 请求

```
POST https://b.alph.ai/smart-web-gateway/ws/listenkey
```

**Headers:**
```
Cookie: dex_cookie=<your_dex_cookie_value>
Content-Type: application/json
```

**Body:**
```json
{}
```

### 响应

```json
{
  "code": "200",
  "data": {
    "listenKey": "xxxxxxxxxxxxxxxxxx",
    "expiresTtl": 3600
  }
}
```

**字段说明：**
- `data.listenKey` - WebSocket 连接凭证
- `data.expiresTtl` - 过期时间（秒），默认按 **3600 秒（1小时）** 处理

**成功判定（需兼容两种格式）：**
- `data.code == "200"` 或
- 顶层 `code == "200"`

### 代码示例

**Python:**
```python
import requests

DEX_COOKIE = "你的dex_cookie值"

def get_listen_key():
    response = requests.post(
        "https://b.alph.ai/smart-web-gateway/ws/listenkey",
        headers={
            "Cookie": f"dex_cookie={DEX_COOKIE}",
            "Content-Type": "application/json"
        },
        json={}
    )
    result = response.json()

    # 兼容两种响应格式
    code = result.get("data", {}).get("code") or result.get("code")
    if code == "200":
        data = result["data"]
        return data["listenKey"], data.get("expiresTtl", 3600)
    else:
        raise Exception(f"获取 listenKey 失败: {result}")

listen_key, expires_ttl = get_listen_key()
print(f"listenKey: {listen_key}")
print(f"过期时间: {expires_ttl}秒")
```

---

## 3. 建立 WebSocket 连接

### 连接地址

```
wss://ws.alph.ai/stream/ws?listenKey=<listen_key>
```

### 代码示例

**Python (websockets):**
```python
import asyncio
import websockets
import json

async def connect_ws(listen_key):
    uri = f"wss://ws.alph.ai/stream/ws?listenKey={listen_key}"

    async with websockets.connect(uri) as ws:
        print("WebSocket 连接成功")

        async for message in ws:
            data = json.loads(message)
            print(f"收到消息: {data}")

asyncio.run(connect_ws(listen_key))
```

**JavaScript:**
```javascript
function connectWS(listenKey) {
    const ws = new WebSocket(`wss://ws.alph.ai/stream/ws?listenKey=${listenKey}`);

    ws.onopen = () => {
        console.log("WebSocket 连接成功");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("收到消息:", data);
    };

    ws.onerror = (error) => {
        console.error("WebSocket 错误:", error);
    };

    ws.onclose = () => {
        console.log("WebSocket 连接关闭");
    };

    return ws;
}
```

---

## 4. listenKey 自动续期

listenKey 默认 **3600 秒（1小时）** 过期，需要定时续期。建议在过期前提前续期（如每 50 分钟续一次），避免连接中断。

### 续期策略

1. 在 listenKey 过期时间的 **80%** 时发起续期（即默认 3600s × 0.8 = 2880s ≈ 48分钟）
2. 续期方式：重新调用 `POST /ws/listenkey` 获取新的 listenKey
3. 用新 listenKey 重新建立 WebSocket 连接，或根据服务端支持情况更新现有连接

### 代码示例

**Python 完整方案（含自动续期）：**
```python
import asyncio
import websockets
import requests
import json
import time

DEX_COOKIE = "你的dex_cookie值"

def get_listen_key():
    """获取 listenKey"""
    response = requests.post(
        "https://b.alph.ai/smart-web-gateway/ws/listenkey",
        headers={
            "Cookie": f"dex_cookie={DEX_COOKIE}",
            "Content-Type": "application/json"
        },
        json={}
    )
    result = response.json()
    code = result.get("data", {}).get("code") or result.get("code")
    if code == "200":
        data = result["data"]
        return data["listenKey"], data.get("expiresTtl", 3600)
    raise Exception(f"获取 listenKey 失败: {result}")

async def ws_listener(listen_key, on_message):
    """WebSocket 监听"""
    uri = f"wss://ws.alph.ai/stream/ws?listenKey={listen_key}"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            await on_message(data)

async def auto_renew_and_listen(on_message):
    """自动续期 + 持续监听"""
    while True:
        try:
            listen_key, expires_ttl = get_listen_key()
            print(f"[{time.strftime('%H:%M:%S')}] listenKey 获取成功，{expires_ttl}秒后过期")

            # 在过期前 80% 的时间点续期
            renew_after = int(expires_ttl * 0.8)

            # 创建监听和续期两个任务
            listen_task = asyncio.create_task(ws_listener(listen_key, on_message))
            renew_task = asyncio.create_task(asyncio.sleep(renew_after))

            # 等待续期时间到达
            done, pending = await asyncio.wait(
                [listen_task, renew_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # 取消未完成的任务
            for task in pending:
                task.cancel()

            print(f"[{time.strftime('%H:%M:%S')}] 开始续期 listenKey...")

        except Exception as e:
            print(f"连接异常: {e}，5秒后重试...")
            await asyncio.sleep(5)

# 使用示例
async def handle_message(data):
    print(f"收到: {data}")

asyncio.run(auto_renew_and_listen(handle_message))
```

**JavaScript 完整方案（含自动续期）：**
```javascript
const DEX_COOKIE = "你的dex_cookie值";

async function getListenKey() {
    const response = await fetch("https://b.alph.ai/smart-web-gateway/ws/listenkey", {
        method: "POST",
        headers: {
            "Cookie": `dex_cookie=${DEX_COOKIE}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({})
    });

    const result = await response.json();
    const code = result.data?.code || result.code;

    if (code === "200") {
        return {
            listenKey: result.data.listenKey,
            expiresTtl: result.data.expiresTtl || 3600
        };
    }
    throw new Error(`获取 listenKey 失败: ${JSON.stringify(result)}`);
}

class AlphAIWebSocket {
    constructor(onMessage) {
        this.onMessage = onMessage;
        this.ws = null;
        this.renewTimer = null;
        this.running = false;
    }

    async start() {
        this.running = true;
        await this._connectWithRenew();
    }

    stop() {
        this.running = false;
        if (this.renewTimer) clearTimeout(this.renewTimer);
        if (this.ws) this.ws.close();
    }

    async _connectWithRenew() {
        if (!this.running) return;

        try {
            const { listenKey, expiresTtl } = await getListenKey();
            console.log(`[${new Date().toLocaleTimeString()}] listenKey 获取成功，${expiresTtl}秒后过期`);

            // 建立 WebSocket 连接
            this.ws = new WebSocket(`wss://ws.alph.ai/stream/ws?listenKey=${listenKey}`);

            this.ws.onopen = () => console.log("WebSocket 连接成功");
            this.ws.onmessage = (event) => this.onMessage(JSON.parse(event.data));
            this.ws.onerror = (error) => console.error("WebSocket 错误:", error);
            this.ws.onclose = () => {
                console.log("WebSocket 连接关闭");
                if (this.running) {
                    setTimeout(() => this._connectWithRenew(), 5000);
                }
            };

            // 设置自动续期（过期时间的 80%）
            const renewAfter = expiresTtl * 0.8 * 1000;
            this.renewTimer = setTimeout(() => {
                console.log(`[${new Date().toLocaleTimeString()}] 开始续期 listenKey...`);
                if (this.ws) this.ws.close();
            }, renewAfter);

        } catch (error) {
            console.error(`连接异常: ${error.message}，5秒后重试...`);
            setTimeout(() => this._connectWithRenew(), 5000);
        }
    }
}

// 使用示例
const client = new AlphAIWebSocket((data) => {
    console.log("收到:", data);
});

client.start();

// 停止: client.stop();
```

---

## 5. 完整流程总结

```
浏览器登录 alph.ai
       │
       ▼
DevTools → Application → Cookies → dex_cookie
       │
       ▼
POST /ws/listenkey （携带 dex_cookie）
       │
       ▼
获取 listenKey + expiresTtl
       │
       ▼
wss://ws.alph.ai/stream/ws?listenKey=xxx
       │
       ▼
发送订阅消息（如推特监控：{"event":"SUBSCRIBE","params":[{"type":"user_tracker_x"}]}）
       │
       ▼
接收实时推送数据
       │
       ▼ (每 ~48 分钟)
重新获取 listenKey → 重新连接
```

---

## 6. 常见问题

### Q: dex_cookie 过期了怎么办？
A: 重新登录 alph.ai，从 DevTools 获取新的 dex_cookie。有效期 14 天。

### Q: listenKey 过期了怎么办？
A: 重新调用 `POST /ws/listenkey` 获取新的。建议用自动续期方案。

### Q: WebSocket 断开了怎么办？
A: 代码中已包含自动重连逻辑，断开后 5 秒自动重试。

### Q: 可以同时订阅多个频道吗？
A: 可以，在同一个 WebSocket 连接上发送多个 SUBSCRIBE 消息即可。
