#!/usr/bin/env python3
"""
Meme Contract Forensics - 主分析脚本
给定 BSC meme 合约地址，识别：庄家 / 获利最多 / 真正高手
依赖: Moralis API (MORALIS_KEY in .env)
用法: python3 contract_forensics.py <合约地址> [--top 50]
"""

import sys, os, json, time, requests, argparse
from collections import defaultdict
from datetime import datetime

# 自动加载 .env
_ENV = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(_ENV):
    for _l in open(_ENV):
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            k, v = _l.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

MORALIS_KEY = os.environ.get("MORALIS_KEY", "")
BSCSCAN_KEY = os.environ.get("BSCSCAN_KEY", "")  # 从 .env 读取，不再用占位符
BASE = "https://deep-index.moralis.io/api/v2.2"
HEADS = {"X-API-Key": MORALIS_KEY}
CHAIN = "bsc"
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

# 已知 DEX/基础设施地址，排除买卖分类和利润计算
# 凡是 from 或 to 属于此集合 → 该笔转账判定为 DEX 交互（买入/卖出），而非内部分发
EXCLUDE_ADDRS = {
    "0x10ed43c718714eb63d5aa57b78b54704e256024e",  # PancakeSwap Router v2
    "0x13f4ea83d0bd40e75c8222255bc855a974568dd4",  # PancakeSwap Router v3
    "0x05ff2b0db69458a0750badebc4f9e13add608c7f",  # PancakeSwap Router v1
    "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506",  # SushiSwap Router BSC
    "0xd99d1c33f9fc3444f8101754abc46c52416550d1",  # PancakeSwap Testnet
    "0x10ed43c718714eb63d5aa57b78b54704e256024e",  # PancakeSwap v2 (dup guard)
    "0x9ac64cc6e4415144c455bd8e4837fea55603e5c3",  # PancakeSwap Testnet v2
    "0xdef1c0ded9bec7f1a1670819833240f027b25eff",  # 0x Exchange Proxy
    "0x1111111254fb6c44bac0bed2854e76f90643097d",  # 1inch v4
    "0x1111111254eeb25477b68fb85ed929f73a960582",  # 1inch v5
    "0x72d220ce168c4f361dd4dee5d826a01ad8598f6c",  # Four.meme launchpad
    "0x5c952063c7fc8610ffdb798152d69f0b9550762b",  # PinkSale
    "0x35113a300ca0d7621374890abfeac30e88f87b6c",  # DODO BSC
    "0x8f8dd7db1bda5ed3da8c9daf3bfa471c12d58486",  # DODO Proxy
    "0x3a6d8ca21d1cf76f653a67577fa0d27453350dd8",  # Biswap Router
    "0x0000000000000000000000000000000000000000",  # zero
    "0x000000000000000000000000000000000000dead",  # burn
}

# DEX 地址集合（from/to 在此集合内代表真实 swap，而非内部分发）
DEX_ADDRS = EXCLUDE_ADDRS - {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
}

# ─── API helpers ──────────────────────────────────────────────────────────────

def moralis_get(path, params=None, retries=3):
    url = f"{BASE}{path}"
    for i in range(retries):
        try:
            r = requests.get(url, headers=HEADS, params=params or {}, timeout=15)
            if r.status_code == 429:
                print("  [429] rate limit, sleep 2s...")
                time.sleep(2)
                continue
            return r.json()
        except Exception as e:
            if i == retries - 1:
                return {}
            time.sleep(1)
    return {}

def get_token_metadata(ca):
    """获取 token 基础信息"""
    d = moralis_get(f"/erc20/metadata", {"chain": CHAIN, "addresses[0]": ca})
    if isinstance(d, list) and d:
        return d[0]
    return {}

def get_token_holders(ca, limit=200):
    """获取当前持有者列表（按余额降序）"""
    holders = []
    cursor = None
    while len(holders) < limit:
        params = {"chain": CHAIN, "limit": min(100, limit - len(holders))}
        if cursor:
            params["cursor"] = cursor
        d = moralis_get(f"/erc20/{ca}/owners", params)
        result = d.get("result", [])
        holders.extend(result)
        cursor = d.get("cursor")
        if not cursor or len(result) < 100:
            break
        time.sleep(0.3)
    return holders

def get_token_transfers(ca, limit_pages=10):
    """获取合约的所有 token 转账记录（按时间升序）"""
    txs = []
    cursor = None
    for _ in range(limit_pages):
        params = {"chain": CHAIN, "limit": 100, "order": "ASC"}
        if cursor:
            params["cursor"] = cursor
        d = moralis_get(f"/erc20/{ca}/transfers", params)
        result = d.get("result", [])
        txs.extend(result)
        cursor = d.get("cursor")
        if not cursor or len(result) < 100:
            break
        time.sleep(0.35)
    return txs

def get_wallet_first_tx(addr):
    """获取地址第一笔链上交易时间（粗略判断账户新旧）"""
    d = moralis_get(f"/{addr}/erc20/transfers", {"chain": CHAIN, "limit": 1, "order": "ASC"})
    results = d.get("result", [])
    if results:
        return results[0].get("block_timestamp", "")
    return ""

# ─── 核心分析 ─────────────────────────────────────────────────────────────────

def parse_transfers(txs, ca, decimals):
    """
    按地址整理买卖行为，区分三种转账类型：
    - DEX 买入：from 是 DEX/LP，to 是普通用户  → to 的 buy
    - DEX 卖出：from 是普通用户，to 是 DEX/LP  → from 的 sell
    - 内部分发：from/to 均不是 DEX → internal_transfer（庄家分发信号，不算买卖）
    """
    ca_lower = ca.lower()
    activity = defaultdict(lambda: {"buys": [], "sells": [], "internal_transfers": []})

    for tx in txs:
        if tx.get("address", "").lower() != ca_lower:
            continue
        fr = tx.get("from_address", "").lower()
        to = tx.get("to_address", "").lower()
        try:
            ts = int(datetime.fromisoformat(
                tx.get("block_timestamp", "").replace("Z", "+00:00")).timestamp())
        except:
            ts = 0
        try:
            amt = int(tx.get("value", 0)) / (10 ** decimals)
        except:
            amt = 0
        tx_hash = tx.get("transaction_hash", "")

        # 过滤：dust / zero / burn 地址
        if fr in {"0x0000000000000000000000000000000000000000",
                  "0x000000000000000000000000000000000000dead"}:
            continue
        if to in {"0x000000000000000000000000000000000000dead"}:
            continue
        if amt < 0.001:
            continue

        entry = {"ts": ts, "amt": amt, "from": fr, "to": to, "hash": tx_hash}

        fr_is_dex = fr in DEX_ADDRS
        to_is_dex = to in DEX_ADDRS

        if fr_is_dex and not to_is_dex:
            # DEX → 用户：真实买入
            activity[to]["buys"].append(entry)
        elif not fr_is_dex and to_is_dex:
            # 用户 → DEX：真实卖出
            activity[fr]["sells"].append(entry)
        elif not fr_is_dex and not to_is_dex:
            # 用户 → 用户：内部分发/转移（庄家分发信号）
            activity[fr]["internal_transfers"].append(entry)
            activity[to]["internal_transfers"].append({**entry, "_direction": "in"})
        # DEX → DEX: 路由内部跳转，忽略

    return activity

def identify_deployer(ca):
    """通过 BSCScan API 获取合约创建者（需要 BSCSCAN_KEY 环境变量）"""
    if not BSCSCAN_KEY:
        print("  [!] BSCSCAN_KEY 未配置，deployer 识别跳过（在 .env 中添加 BSCSCAN_KEY=...）")
        return None
    try:
        r = requests.get(
            f"https://api.bscscan.com/api?module=contract&action=getcontractcreation"
            f"&contractaddresses={ca}&apikey={BSCSCAN_KEY}",
            timeout=10
        )
        d = r.json()
        if d.get("status") == "1" and d.get("result"):
            return d["result"][0].get("contractCreator", "").lower()
        if d.get("message") == "NOTOK":
            print(f"  [!] BSCScan 返回错误: {d.get('result','')}")
    except Exception as e:
        print(f"  [!] BSCScan 请求失败: {e}")
    return None

def detect_wash_trading(addr, data, all_activity):
    """
    检测洗盘行为：addr 的 internal_transfers 中是否存在 A→B→A 的资金循环。
    返回 (is_wash, wash_pairs) 其中 wash_pairs 是发现的循环对数量。
    """
    sent_to = {}   # addr 发出的地址 → 金额列表
    recv_from = {} # addr 收到的地址 → 金额列表

    for t in data.get("internal_transfers", []):
        if t.get("_direction") == "in":
            fr = t["from"]
            recv_from.setdefault(fr, []).append(t["amt"])
        else:
            to = t["to"]
            sent_to.setdefault(to, []).append(t["amt"])

    # 找 A→addr→A 的循环
    cycle_addrs = set(sent_to.keys()) & set(recv_from.keys())
    # 验证循环金额是否接近（容差 20%）
    confirmed_cycles = 0
    for cycle_addr in cycle_addrs:
        out_total = sum(sent_to[cycle_addr])
        in_total  = sum(recv_from[cycle_addr])
        if in_total > 0 and abs(out_total - in_total) / in_total < 0.2:
            confirmed_cycles += 1

    return confirmed_cycles > 0, confirmed_cycles


def score_address(addr, data, total_supply, deployer, first_buyers_set,
                  distributing_receivers, all_activity):
    """
    对单个地址打分，返回分类标签。
    distributing_receivers: 由 deployer 直接分发（internal transfer）收到 token 的地址集合，
                            用于从 first_buyers_set 中剔除被污染的地址。
    返回: (zhuang_score, smart_score, label, zhuang_reasons, smart_reasons, stats)
    """
    buys = data["buys"]
    sells = data["sells"]
    if not buys and not sells:
        return 0, 0, "⬜ 普通散户", [], [], {
            "total_buy_amt": 0, "total_sell_amt": 0, "exit_rate": 0,
            "hold_hours": 0, "first_buy_ts": 0, "last_sell_ts": 0,
            "buy_count": 0, "sell_count": 0,
        }

    total_buy_amt = sum(b["amt"] for b in buys)
    total_sell_amt = sum(s["amt"] for s in sells)
    exit_rate = total_sell_amt / total_buy_amt if total_buy_amt > 0 else 0

    buy_ts = sorted([b["ts"] for b in buys])
    sell_ts = sorted([s["ts"] for s in sells])
    first_buy_ts = buy_ts[0] if buy_ts else 0
    last_sell_ts = sell_ts[-1] if sell_ts else 0
    hold_hours = (last_sell_ts - first_buy_ts) / 3600 if first_buy_ts and last_sell_ts else 0

    # ── 庄家评分 ──
    zhuang_score = 0
    zhuang_reasons = []

    # 1. deployer 直接关联
    if addr == deployer:
        zhuang_score += 10
        zhuang_reasons.append("合约部署者")

    # 2. 内部分发：向 5+ 个不同地址转出（分发型庄家）
    sent_out = data.get("internal_transfers", [])
    sent_to_addrs = {t["to"] for t in sent_out if t.get("_direction") != "in"}
    if len(sent_to_addrs) >= 5:
        zhuang_score += 4
        zhuang_reasons.append(f"内部分发到{len(sent_to_addrs)}个地址")

    # 3. deployer 的分发接收者（内盘知情）
    if addr in distributing_receivers and addr != deployer:
        zhuang_score += 4
        zhuang_reasons.append("deployer直接分发接收者（内盘知情）")

    # 4. 早期大仓买入（前20%且占比>1%总供应量）
    is_early = (addr in first_buyers_set) and (addr not in distributing_receivers)
    if is_early and total_buy_amt / max(total_supply, 1) > 0.01:
        zhuang_score += 3
        zhuang_reasons.append(f"早期大仓占比{total_buy_amt/total_supply*100:.1f}%")

    # 5. 洗盘检测（A→B→A 资金循环）
    is_wash, wash_pairs = detect_wash_trading(addr, data, all_activity)
    if is_wash:
        zhuang_score += 3
        zhuang_reasons.append(f"洗盘循环{wash_pairs}对（资金回流）")

    # 6. 高频拉砸（DEX买卖各≥5次）
    if len(buys) >= 5 and len(sells) >= 5:
        zhuang_score += 2
        zhuang_reasons.append(f"高频拉砸（买{len(buys)}卖{len(sells)}）")

    # ── 高手评分 ──
    smart_score = 0
    smart_reasons = []

    # 1. 早期买入（排除分发接收者污染）
    if is_early:
        smart_score += 3
        smart_reasons.append("早期买入（前20%，非内盘分发）")

    # 2. 高出局率
    if exit_rate >= 0.5:
        smart_score += 3
        smart_reasons.append(f"出局率{exit_rate:.0%}")
    elif exit_rate >= 0.25:
        smart_score += 1
        smart_reasons.append(f"部分出局{exit_rate:.0%}")

    # 3. 持仓时间合理（0.5-24h）
    if 0.5 <= hold_hours <= 24:
        smart_score += 2
        smart_reasons.append(f"持仓{hold_hours:.1f}h（纪律性）")

    # 4. 庄家降权
    if zhuang_score >= 4:
        smart_score = max(0, smart_score - 5)
        smart_reasons.append("⚠️ 疑似庄关联，降权")

    # 分类
    if zhuang_score >= 8:
        label = "🔴 庄家核心"
    elif zhuang_score >= 5:
        label = "🟠 庄家关联"
    elif zhuang_score >= 2:
        label = "🟡 疑似内盘"
    elif smart_score >= 5:
        label = "🟢 真实高手"
    elif smart_score >= 3:
        label = "🔵 潜在高手"
    else:
        label = "⬜ 普通散户"

    return zhuang_score, smart_score, label, zhuang_reasons, smart_reasons, {
        "total_buy_amt": total_buy_amt,
        "total_sell_amt": total_sell_amt,
        "exit_rate": exit_rate,
        "hold_hours": hold_hours,
        "first_buy_ts": first_buy_ts,
        "last_sell_ts": last_sell_ts,
        "buy_count": len(buys),
        "sell_count": len(sells),
    }

# ─── 报告生成 ─────────────────────────────────────────────────────────────────

def generate_report(ca, meta, results, deployer, output_path,
                    top10_pct=0.0, distributing_receivers=None):
    ca_short = ca[:8]
    lines = [
        "=" * 55,
        f"  BSC Meme 合约取证报告",
        f"  合约: {ca}",
        f"  Token: {meta.get('name','')} ({meta.get('symbol','')})",
        f"  生成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 55, "",
    ]

    # 合约基础
    dist_recv_count = len(distributing_receivers) if distributing_receivers else 0
    lines += [
        "【合约基础信息】",
        f"  名称: {meta.get('name','')} / {meta.get('symbol','')}",
        f"  总量: {meta.get('total_supply_formatted', meta.get('total_supply','?'))}",
        f"  部署者: {deployer or '未识别（需配置 BSCSCAN_KEY）'}",
        f"  前10持仓占比: {top10_pct:.1f}%{'（高度集中，注意风险）' if top10_pct > 50 else ''}",
        f"  内盘分发接收者: {dist_recv_count} 个地址",
        "",
    ]

    # 分类汇总
    zhuang_core = [r for r in results if "庄家核心" in r["label"]]
    zhuang_rel  = [r for r in results if "庄家关联" in r["label"]]
    neipan       = [r for r in results if "内盘" in r["label"]]
    smart        = [r for r in results if "真实高手" in r["label"]]
    potential    = [r for r in results if "潜在高手" in r["label"]]

    lines += [
        "【识别汇总】",
        f"  🔴 庄家核心:  {len(zhuang_core)} 个",
        f"  🟠 庄家关联:  {len(zhuang_rel)} 个",
        f"  🟡 疑似内盘:  {len(neipan)} 个",
        f"  🟢 真实高手:  {len(smart)} 个",
        f"  🔵 潜在高手:  {len(potential)} 个",
        "",
    ]

    # 庄家地址
    if zhuang_core or zhuang_rel:
        lines.append("【🔴🟠 庄家地址详情】")
        for r in (zhuang_core + zhuang_rel)[:15]:
            lines += [
                f"  {r['label']} {r['address']}",
                f"    庄家得分: {r['zhuang_score']} | 证据: {' / '.join(r['zhuang_reasons'])}",
                f"    买入量: {r['stats']['total_buy_amt']:.1f} | 卖出量: {r['stats']['total_sell_amt']:.1f} | 出局率: {r['stats']['exit_rate']:.0%}",
                "",
            ]

    # 获利排行（注意：按 token 卖出量排序，不含精确价格，非真实利润）
    profit_sorted = sorted(results, key=lambda x: -x["stats"]["total_sell_amt"])
    lines.append("【💰 卖出量 Top15（token数量，非价格利润——价格数据需另行获取）】")
    for i, r in enumerate(profit_sorted[:15], 1):
        s = r["stats"]
        lines.append(
            f"  {i:2d}. {r['label']} {r['address'][:20]}..."
            f" | 卖出量:{s['total_sell_amt']:.1f} token | 出局:{s['exit_rate']:.0%}"
            f" | 持仓:{s['hold_hours']:.1f}h"
        )
    lines.append("")

    # 高手名单
    if smart or potential:
        lines.append("【🟢🔵 真正高手名单】")
        for r in (smart + potential):
            s = r["stats"]
            lines += [
                f"  {r['label']} {r['address']}",
                f"    高手得分: {r['smart_score']} | 亮点: {' / '.join(r['smart_reasons'])}",
                f"    出局率: {s['exit_rate']:.0%} | 持仓: {s['hold_hours']:.1f}h | 买{s['buy_count']}次卖{s['sell_count']}次",
                "",
            ]

    # 跟踪建议
    lines += [
        "【跟踪建议】",
        "  1. 庄家地址 → 监控其下一个合约部署动作（可能复制成功案例）",
        "  2. 真实高手地址 → 送入 wallet-playbook-analysis 深挖打法",
        "  3. 获利 Top 非庄家地址 → 送入批量分析评级跟踪",
        "",
        "注：利润为 token 数量估算，不含精确价格，仅供参考。",
    ]

    content = "\n".join(lines)
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return content

# ─── 主流程 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", help="BSC meme 合约地址")
    parser.add_argument("--top", type=int, default=200, help="分析持有者数量")
    parser.add_argument("--pages", type=int, default=10, help="拉取转账记录页数")
    args = parser.parse_args()

    ca = args.contract.lower()
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    ca_short = ca[2:10]
    report_path = os.path.join(REPORT_DIR, f"contract-forensics-{ca_short}-{date_str}.txt")
    alpha_path  = os.path.join(REPORT_DIR, f"contract-alpha-{ca_short}-{date_str}.json")

    print(f"[*] 合约取证分析: {ca}")
    print(f"[*] 报告路径: {report_path}\n")

    # Step 1: 基础信息
    print("[1/5] 获取 token 基础信息...")
    meta = get_token_metadata(ca)
    decimals = int(meta.get("decimals", 18))
    total_supply = float(meta.get("total_supply", 0)) / (10 ** decimals)
    print(f"    → {meta.get('name','')} ({meta.get('symbol','')}) 总量:{total_supply:.0f}")
    time.sleep(0.3)

    # Step 2: 获取部署者
    print("[2/5] 识别部署者...")
    deployer = identify_deployer(ca)
    print(f"    → deployer: {deployer or '未识别'}")
    time.sleep(0.3)

    # Step 3: 获取持有者
    print(f"[3/5] 获取持有者 top {args.top}...")
    holders = get_token_holders(ca, limit=args.top)
    print(f"    → 获取到 {len(holders)} 个持有者")
    time.sleep(0.3)

    # Step 4: 获取转账记录
    print(f"[4/5] 拉取转账记录（最多 {args.pages} 页）...")
    txs = get_token_transfers(ca, limit_pages=args.pages)
    print(f"    → 获取到 {len(txs)} 条转账")

    # 解析活动（区分 DEX买卖 vs 内部分发）
    activity = parse_transfers(txs, ca, decimals)

    # 识别早期 DEX 买入者（前20%时间段，只统计真实 DEX 买入）
    all_first_buys = []
    for addr, d in activity.items():
        if d["buys"]:  # 此时 buys 已只含 DEX swap 买入
            all_first_buys.append((addr, min(b["ts"] for b in d["buys"])))
    all_first_buys.sort(key=lambda x: x[1])
    top20_pct = max(1, int(len(all_first_buys) * 0.2))
    first_buyers_set = {a for a, _ in all_first_buys[:top20_pct]}

    # 识别 deployer 的直接分发接收者（内部 transfer，排除高手集合污染）
    distributing_receivers = set()
    if deployer and deployer in activity:
        for t in activity[deployer].get("internal_transfers", []):
            if t.get("_direction") != "in":
                distributing_receivers.add(t["to"])

    # 持仓集中度计算
    print("[4.5] 计算持仓集中度...")
    top10_holders = holders[:10]
    top10_pct = 0.0
    if holders:
        total_pct = sum(
            float(h.get("percentage_relative_to_total_supply", 0))
            for h in top10_holders
        )
        top10_pct = total_pct
    print(f"    → 前10持仓占比: {top10_pct:.1f}%")

    # Step 5: 评分
    print(f"[5/5] 分析 {len(activity)} 个地址...")
    results = []
    for addr, d in activity.items():
        if addr in EXCLUDE_ADDRS:
            continue
        ret = score_address(addr, d, total_supply, deployer, first_buyers_set,
                            distributing_receivers, activity)
        zhuang_score, smart_score, label, zr, sr, stats = ret
        results.append({
            "address": addr,
            "label": label,
            "zhuang_score": zhuang_score,
            "smart_score": smart_score,
            "zhuang_reasons": zr,
            "smart_reasons": sr,
            "stats": stats,
        })

    # 生成报告
    generate_report(ca, meta, results, deployer, report_path,
                    top10_pct=top10_pct, distributing_receivers=distributing_receivers)

    # 导出高手名单 JSON
    alpha_list = [
        {
            "address": r["address"],
            "label": r["label"].split(" ", 1)[-1],
            "entry_rank": "前20%" if r["address"] in first_buyers_set else "后80%",
            "exit_rate": round(r["stats"]["exit_rate"], 3),
            "hold_hours": round(r["stats"]["hold_hours"], 1),
            "buy_count": r["stats"]["buy_count"],
            "sell_count": r["stats"]["sell_count"],
            "smart_score": r["smart_score"],
            "note": " / ".join(r["smart_reasons"]) if r["smart_reasons"] else "—",
        }
        for r in results
        if "高手" in r["label"]
    ]
    with open(alpha_path, "w", encoding="utf-8") as f:
        json.dump(alpha_list, f, ensure_ascii=False, indent=2)

    # 控制台汇总
    zhuang_n = sum(1 for r in results if "庄家" in r["label"])
    smart_n  = sum(1 for r in results if "高手" in r["label"])
    print(f"\n[✓] 分析完成")
    print(f"    庄家相关: {zhuang_n} | 高手: {smart_n} | 总分析地址: {len(results)}")
    print(f"    报告: {report_path}")
    print(f"    高手名单: {alpha_path}")

    return report_path, alpha_path

if __name__ == "__main__":
    main()
