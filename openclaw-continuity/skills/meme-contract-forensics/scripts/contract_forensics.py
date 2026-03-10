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
BASE = "https://deep-index.moralis.io/api/v2.2"
HEADS = {"X-API-Key": MORALIS_KEY}
CHAIN = "bsc"
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

# 已知 DEX/基础设施地址，排除利润计算
EXCLUDE_ADDRS = {
    "0x10ed43c718714eb63d5aa57b78b54704e256024e",  # PancakeSwap Router v2
    "0x13f4ea83d0bd40e75c8222255bc855a974568dd4",  # PancakeSwap Router v3
    "0x0000000000000000000000000000000000000000",  # zero
    "0x000000000000000000000000000000000000dead",  # burn
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
    """按地址整理买卖行为"""
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

        if fr in EXCLUDE_ADDRS or to in EXCLUDE_ADDRS:
            continue

        # 卖出：from=持有者, to=DEX or 0x
        # 买入：from=DEX or 0x, to=持有者
        # 转移：from=持有者, to=另一持有者
        if amt < 0.001:
            continue

        entry = {"ts": ts, "amt": amt, "from": fr, "to": to, "hash": tx_hash}

        # 简单规则：transfer in = 买入方收到 token
        activity[to]["buys"].append(entry)
        activity[fr]["sells"].append(entry)

    return activity

def identify_deployer(ca):
    """通过 Moralis 获取合约创建者"""
    # 尝试通过 token metadata 找 deployer
    meta = get_token_metadata(ca)
    # Moralis 不直接给 deployer，用 BSCScan 公开接口试试
    try:
        r = requests.get(
            f"https://api.bscscan.com/api?module=contract&action=getcontractcreation"
            f"&contractaddresses={ca}&apikey=YourApiKeyToken",
            timeout=10
        )
        d = r.json()
        if d.get("status") == "1" and d.get("result"):
            return d["result"][0].get("contractCreator", "").lower()
    except:
        pass
    return None

def score_address(addr, data, total_supply, deployer, first_buyers_set, all_activity):
    """
    对单个地址打分，返回分类标签
    返回: (庄家分, 高手分, 分类)
    """
    buys = data["buys"]
    sells = data["sells"]
    if not buys and not sells:
        return 0, 0, "无效"

    total_buy_amt = sum(b["amt"] for b in buys)
    total_sell_amt = sum(s["amt"] for s in sells)
    exit_rate = total_sell_amt / total_buy_amt if total_buy_amt > 0 else 0

    # 时间排序
    buy_ts = sorted([b["ts"] for b in buys])
    sell_ts = sorted([s["ts"] for s in sells])
    first_buy_ts = buy_ts[0] if buy_ts else 0
    last_sell_ts = sell_ts[-1] if sell_ts else 0
    hold_hours = (last_sell_ts - first_buy_ts) / 3600 if first_buy_ts and last_sell_ts else 0

    # ── 庄家评分 ──
    zhuang_score = 0
    zhuang_reasons = []

    # 1. deployer 关联
    if addr == deployer:
        zhuang_score += 10
        zhuang_reasons.append("合约部署者")

    # 2. 早于公开交易收到大量 token（分发信号）
    if addr in first_buyers_set and total_buy_amt / max(total_supply, 1) > 0.01:
        zhuang_score += 5
        zhuang_reasons.append(f"早期大量收入占比{total_buy_amt/total_supply*100:.1f}%")

    # 3. 向多个新钱包转出（分发操作）
    sent_to = set(s["to"] for s in sells)
    if len(sent_to) >= 5 and exit_rate > 0.3:
        zhuang_score += 3
        zhuang_reasons.append(f"分发到{len(sent_to)}个地址")

    # 4. 大量买卖循环（反复拉砸）
    if len(buys) >= 5 and len(sells) >= 5:
        zhuang_score += 2
        zhuang_reasons.append("高频买卖循环")

    # ── 高手评分 ──
    smart_score = 0
    smart_reasons = []

    # 1. 早期买入
    if addr in first_buyers_set:
        smart_score += 3
        smart_reasons.append("早期买入（前20%）")

    # 2. 高出局率（真实落袋）
    if exit_rate >= 0.5:
        smart_score += 3
        smart_reasons.append(f"出局率{exit_rate:.0%}")
    elif exit_rate >= 0.25:
        smart_score += 1
        smart_reasons.append(f"部分出局{exit_rate:.0%}")

    # 3. 持仓时间合理（1-24h 视为纪律性强）
    if 0.5 <= hold_hours <= 24:
        smart_score += 2
        smart_reasons.append(f"持仓{hold_hours:.1f}h")

    # 4. 非庄家（排除庄家知情者）
    if zhuang_score >= 5:
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

def generate_report(ca, meta, results, deployer, output_path):
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
    lines += [
        "【合约基础信息】",
        f"  名称: {meta.get('name','')} / {meta.get('symbol','')}",
        f"  总量: {meta.get('total_supply_formatted', meta.get('total_supply','?'))}",
        f"  部署者: {deployer or '未识别'}",
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

    # 获利排行
    profit_sorted = sorted(results, key=lambda x: -x["stats"]["total_sell_amt"])
    lines.append("【💰 获利最多 Top15（按卖出量估算）】")
    for i, r in enumerate(profit_sorted[:15], 1):
        s = r["stats"]
        lines.append(
            f"  {i:2d}. {r['label']} {r['address'][:20]}..."
            f" | 卖出:{s['total_sell_amt']:.1f} | 出局:{s['exit_rate']:.0%}"
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

    # 解析活动
    activity = parse_transfers(txs, ca, decimals)

    # 识别早期买入者（前20%时间段）
    all_first_buys = []
    for addr, d in activity.items():
        if d["buys"]:
            all_first_buys.append((addr, min(b["ts"] for b in d["buys"])))
    all_first_buys.sort(key=lambda x: x[1])
    top20_pct = max(1, int(len(all_first_buys) * 0.2))
    first_buyers_set = {a for a, _ in all_first_buys[:top20_pct]}

    # Step 5: 评分
    print(f"[5/5] 分析 {len(activity)} 个地址...")
    results = []
    for addr, d in activity.items():
        if addr in EXCLUDE_ADDRS:
            continue
        ret = score_address(addr, d, total_supply, deployer, first_buyers_set, activity)
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
    generate_report(ca, meta, results, deployer, report_path)

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
