#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个股研报指标监听脚本
- 数据源：腾讯行情快照（qt.gtimg.cn），字段：现价(3)、PE-TTM(39)、总市值(45, 亿元)
- 输出：/var/www/research/alerts.json（网页预警中心读取）
- 状态：/home/ubuntu/monitor/state.json（记录每条规则的首次触发日期，避免重复刷屏）
"""
import json, os, re, urllib.request, datetime

RULES = {
    "smic": dict(
        qcode="sh688981", name="中芯国际", link="reports/smic.html",
        stance="观察 Watchlist（A股）",
        rules=[
            dict(id="smic_pe_digested", kind="prove",  metric="pe", op="<=", thr=100.0,
                 msg="PE-TTM 回落至 100 倍下方：A 股估值消化至可讨论区间，「优先 H 股」逻辑边际弱化，可重估 A 股立场"),
            dict(id="smic_price_bear", kind="disprove", metric="price", op="<=", thr=85.0,
                 msg="股价跌入悲观情景区域（≤85 元）：证伪信号，需复核成熟制程扩产回报假设"),
            dict(id="smic_price_target", kind="prove", metric="price", op=">=", thr=170.99,
                 msg="股价触及一致目标价 170.99 元：乐观情景兑现，注意一致性预期是否继续上修"),
        ]),
    "eve": dict(
        qcode="sz300014", name="亿纬锂能", link="reports/eve.html",
        stance="逢低增持 Add",
        rules=[
            dict(id="eve_price_bear", kind="disprove", metric="price", op="<=", thr=40.0,
                 msg="股价跌入悲观情景区域（≤40 元）：大概率对应毛利率/现金流证伪，复核「量增补价稳」假设"),
            dict(id="eve_price_target", kind="prove", metric="price", op=">=", thr=83.31,
                 msg="股价触及一致目标价 83.31 元：基准情景兑现，检查是否仍有 2027E 上修空间"),
            dict(id="eve_pe_repair", kind="prove", metric="pe", op=">=", thr=30.0,
                 msg="PE-TTM 回到 30 倍上方：五年最低分位的估值修复已基本兑现，剩余收益依赖业绩兑现"),
        ]),
    "fii": dict(
        qcode="sh601138", name="工业富联", link="reports/fii.html",
        stance="持有 Hold（回调增持）",
        rules=[
            dict(id="fii_price_addzone", kind="prove", metric="price", op="<=", thr=44.0,
                 msg="股价进一步跌至 44 元下方（2026E 约 14 倍）：增持区下沿，赔率显著改善"),
            dict(id="fii_price_bear", kind="disprove", metric="price", op="<=", thr=39.0,
                 msg="股价跌入悲观情景区域（≤39 元）：证伪信号，大概率对应 CSP 资本开支下修"),
            dict(id="fii_price_up", kind="prove", metric="price", op=">=", thr=76.0,
                 msg="股价触及基准情景中枢（≈76 元）：基准情景兑现，剩余空间依赖 CSP capex 再上修"),
        ]),
    "cmoc": dict(
        qcode="sh603993", name="洛阳钼业", link="reports/cmoc.html",
        stance="增持 Add（顺周期分批）",
        rules=[
            dict(id="cmoc_price_up", kind="prove", metric="price", op=">=", thr=26.0,
                 msg="股价回到 26 元附近（一年高点/乐观情景区）：铜价逻辑强化，检查 2027E 是否上修"),
            dict(id="cmoc_price_bear", kind="disprove", metric="price", op="<=", thr=12.6,
                 msg="股价跌入悲观情景区域（≤12.6 元）：证伪信号，大概率对应铜价跌破成本支撑"),
            dict(id="cmoc_pe_extreme", kind="prove", metric="pe", op="<=", thr=10.0,
                 msg="PE-TTM 逼近五年最低 9.77 倍：极端低分位，若基本面未恶化则赔率进一步改善"),
        ]),

    "yonyou": dict(
        qcode="sh600588", name="用友网络", link="reports/yonyou.html",
        stance="观察 Watchlist（待扭亏信号）",
        rules=[
            dict(id="yonyou_price_up", kind="prove", metric="price", op=">=", thr=14.8,
                 msg="股价触及乐观情景区（≈14.8 元）：扭亏预期被强烈定价，复核 PS 是否已到 5 倍"),
            dict(id="yonyou_price_bear", kind="disprove", metric="price", op="<=", thr=5.9,
                 msg="股价跌入悲观情景区域（≤5.9 元）：大概率对应减亏失速/收入转负，反转假设证伪"),
            dict(id="yonyou_price_low", kind="prove", metric="price", op="<=", thr=8.0,
                 msg="股价跌破 8 元创一年新低：若基本面未恶化，困境反转赔率进一步改善"),
        ]),
    "xiaomi": dict(
        qcode="hk01810", name="小米集团-W", link="reports/xiaomi.html", market="hk",
        stance="持有 Hold（待 H2 拐点）",
        rules=[
            dict(id="xiaomi_price_up", kind="prove", metric="price", op=">=", thr=39.1,
                 msg="股价触及乐观情景区（≈39.1 港元）：汽车/手机逻辑被重新定价，检查盈利是否同步上修"),
            dict(id="xiaomi_price_bear", kind="disprove", metric="price", op="<=", thr=17.8,
                 msg="股价跌入悲观情景区域（≤17.8 港元）：证伪信号，大概率对应盈利下行未见底"),
            dict(id="xiaomi_pe_low", kind="prove", metric="pe", op="<=", thr=14.0,
                 msg="PE-TTM 跌破 14 倍（2026-05 以来区间底部）：若盈利未继续恶化则估值极具吸引力"),
        ]),
    "hh": dict(
        qcode="sh688347", name="华虹宏力", link="reports/hh.html",
        stance="回避 / 不追 Pass（估值极端透支）",
        rules=[
            dict(id="hh_pe_cool", kind="prove", metric="pe", op="<=", thr=300.0,
                 msg="PE-TTM 回落至 300 倍以下：估值消化进行中，若盈利仍在加速则转观察名单"),
            dict(id="hh_price_up", kind="disprove", metric="price", op=">=", thr=290.0,
                 msg="股价触及乐观情景区（≈290 元）：透支进一步加剧，复核是否伴随盈利预期大幅上修"),
            dict(id="hh_price_bear", kind="prove", metric="price", op="<=", thr=140.0,
                 msg="股价跌至 140 元下方：悲观情景（108 元）上方最后一道缓冲，估值消化过半"),
        ]),
    "mu": dict(
        qcode="usMU", name="美光科技", link="reports/mu.html",
        stance="持有 Hold（周期顶部区域）",
        rules=[
            dict(id="mu_price_up", kind="prove", metric="price", op=">=", thr=1285.0,
                 msg="股价触及基准情景中枢（≈1,285 美元）：FY27E 兑现预期充分，复核周期位置"),
            dict(id="mu_price_bear", kind="disprove", metric="price", op="<=", thr=735.0,
                 msg="股价跌至 735 美元下方：市场在定价 FY27E 盈利幻觉证伪（周期逆转）"),
            dict(id="mu_price_low", kind="prove", metric="price", op="<=", thr=800.0,
                 msg="股价跌破 800 美元：FY26 年报后 PE-TTM 约 10.7 倍，错杀概率上升，评估窗口加深"),
        ]),
    "sndk": dict(
        qcode="usSNDK", name="闪迪", link="reports/sndk.html",
        stance="持有 Hold（预期打满，对称）",
        rules=[
            dict(id="sndk_price_up", kind="prove", metric="price", op=">=", thr=2900.0,
                 msg="股价触及乐观情景区（≈2,900 美元）：NAND 超级周期延续被充分定价"),
            dict(id="sndk_price_bear", kind="disprove", metric="price", op="<=", thr=1000.0,
                 msg="股价跌破 1,000 美元整数关口：趋势确认破坏，NAND 价格拐点大概率已出现"),
        ]),
    "nvda": dict(
        qcode="usNVDA", name="英伟达", link="reports/nvda.html",
        stance="增持 Add（回调加仓）",
        rules=[
            dict(id="nvda_price_up", kind="prove", metric="price", op=">=", thr=280.0,
                 msg="股价触及基准情景中枢（≈280 美元）：FY28E 兑现预期充分，复核云厂资本开支"),
            dict(id="nvda_price_bear", kind="disprove", metric="price", op="<=", thr=172.0,
                 msg="股价跌入悲观情景区域（≤172 美元）：大概率对应 AI 资本开支指引下修，增持假设证伪"),
            dict(id="nvda_pe_high", kind="disprove", metric="pe", op=">=", thr=45.0,
                 msg="PE-TTM 升至 45 倍以上：估值再度脱离盈利增速可解释区间"),
        ]),
    "axti": dict(
        qcode="usAXTI", name="AXT Inc", link="reports/axti.html",
        stance="观察 Watchlist（等两个触发器）",
        rules=[
            dict(id="axti_price_low", kind="prove", metric="price", op="<=", thr=45.0,
                 msg="股价跌破 45 美元（2027E 20 倍）：估值消化充分，升级评估的赔率显著改善"),
            dict(id="axti_price_up", kind="disprove", metric="price", op=">=", thr=126.0,
                 msg="股价触及乐观情景区（≈126 美元）：盈利兑现未同步则透支加剧"),
            dict(id="axti_price_bear", kind="disprove", metric="price", op="<=", thr=36.0,
                 msg="股价跌入悲观情景区域（≤36 美元）：动量瓦解+盈利不及预期，观察假设证伪"),
        ]),
}

FIELDS = dict(price=3, pe=39, mktcap=45, name=1, chg=32)      # A股字段索引
FIELDS_HK = dict(price=3, pe=57, mktcap=45, name=1, chg=32)  # 港股字段索引

def fetch(codes):
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", "ignore")
    out = {}
    for m in re.finditer(r'v_(\w+)="([^"]*)"', raw):
        parts = m.group(2).split("~")
        fields = FIELDS_HK if m.group(1).startswith("hk") else FIELDS
        d = {}
        for k, i in fields.items():
            try:
                d[k] = float(parts[i]) if k != "name" else parts[i]
            except (ValueError, IndexError):
                d[k] = None
        out[m.group(1)] = d
    return out

OPS = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b}

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    state_path = "/home/ubuntu/monitor/state.json"
    state = json.load(open(state_path)) if os.path.exists(state_path) else {}
    snap = fetch([v["qcode"] for v in RULES.values()])
    alerts, snapshot = [], []
    for key, cfg in RULES.items():
        q = snap.get(cfg["qcode"], {})
        price, pe = q.get("price"), q.get("pe")
        snapshot.append(dict(code=cfg["qcode"], name=cfg["name"], stance=cfg["stance"],
                             link=cfg["link"], price=price, pe=pe,
                             chg=q.get("chg"), mktcap=q.get("mktcap")))
        for r in cfg["rules"]:
            val = pe if r["metric"] == "pe" else price
            hit = val is not None and OPS[r["op"]](val, r["thr"])
            rec = state.get(r["id"], {})
            if hit and not rec.get("active"):
                rec = dict(active=True, first_fired=now)
                alerts.append(dict(stock=cfg["name"], link=cfg["link"], kind=r["kind"],
                                   rule=r["id"], msg=r["msg"], value=val, thr=r["thr"],
                                   first_fired=now, new=True))
            elif hit and rec.get("active"):
                alerts.append(dict(stock=cfg["name"], link=cfg["link"], kind=r["kind"],
                                   rule=r["id"], msg=r["msg"], value=val, thr=r["thr"],
                                   first_fired=rec.get("first_fired", now), new=False))
            elif not hit and rec.get("active"):
                rec = dict(active=False, first_fired=None)  # 条件解除
            state[r["id"]] = rec
    payload = dict(last_check=now, alerts=alerts, snapshot=snapshot,
                   note="数据源：腾讯行情快照（收盘后自动更新）；证伪/证实规则来自各深度报告的立场与证伪条件。")
    tmp = "/tmp/alerts.json"
    json.dump(payload, open(tmp, "w"), ensure_ascii=False, indent=1)
    os.replace(tmp, "/var/www/research/alerts.json")
    json.dump(state, open(state_path, "w"), ensure_ascii=False, indent=1)
    print(now, "checked", len(snapshot), "stocks,", len(alerts), "alerts active")

if __name__ == "__main__":
    main()
