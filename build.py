# -*- coding: utf-8 -*-
"""
个股深度验证研报库 — 静态站点生成器
用法：python3 build.py
结构：
  app/index.html          研报库首页（卡片导航，新增股票在此自动出现）
  app/reports/<code>.html 每只股票的独立深度报告页
新增股票：在 STOCKS 中追加一个 dict（key  figures/thesis/sixdim/bull/bear/scenarios/watch 均为结构化数据），
          图表 PNG 放在 CHART_DIR 下命名 <code>_<name>.png，重跑本脚本即可。
"""
import base64, os, html as _html

ROOT = os.path.dirname(os.path.abspath(__file__))
CHART_DIR = "/mnt/agents/output"
REPORTS_DIR = os.path.join(ROOT, "reports")

CSS = """
  :root { --navy:#16324f; --blue:#1f4e79; --lblue:#5b9bd5; --bg:#f4f6f9; --gold:#c9a227; --red:#b03a2e; --green:#4a7c59; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif; background:var(--bg); color:#2b2b2b; line-height:1.65; }
  .wrap { max-width:960px; margin:0 auto; padding:24px 20px 64px; }
  nav.top { position:sticky; top:0; z-index:50; background:var(--navy); box-shadow:0 2px 6px rgba(0,0,0,.15); }
  nav.top .inner { max-width:960px; margin:0 auto; display:flex; align-items:center; gap:6px; padding:0 20px; flex-wrap:wrap; }
  nav.top .brand { color:#fff; font-weight:bold; font-size:15px; padding:12px 14px 12px 0; margin-right:6px; border-right:1px solid rgba(255,255,255,.25); }
  nav.top a { color:#cfe0f0; text-decoration:none; font-size:14px; padding:12px 14px; display:inline-block; }
  nav.top a:hover { color:#fff; background:rgba(255,255,255,.08); }
  nav.top a.active { color:#fff; border-bottom:3px solid var(--gold); font-weight:bold; }
  header.hero { background:linear-gradient(135deg,#16324f 0%,#1f4e79 100%); color:#fff; padding:36px 28px; border-radius:12px; margin:24px 0; }
  header.hero .tag { display:inline-block; background:var(--gold); color:#16324f; font-weight:bold; font-size:13px; padding:3px 12px; border-radius:20px; margin-bottom:12px; }
  header.hero h1 { font-size:25px; margin-bottom:6px; }
  header.hero .sub { opacity:.85; font-size:14px; }
  .verdict { background:#fff; border-left:6px solid var(--gold); border-radius:8px; padding:20px 24px; margin-bottom:24px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
  .verdict h2 { color:var(--navy); font-size:19px; margin-bottom:10px; }
  .verdict p { font-size:15px; margin-top:8px; }
  .stance { display:inline-block; background:var(--navy); color:#fff; font-weight:bold; padding:2px 14px; border-radius:4px; font-size:14px; }
  section { background:#fff; border-radius:12px; padding:26px 28px; margin-bottom:24px; box-shadow:0 1px 4px rgba(0,0,0,.06); }
  h2.sec { color:var(--navy); font-size:20px; border-bottom:2px solid var(--lblue); padding-bottom:8px; margin-bottom:16px; }
  h2.sec span.en { font-size:13px; color:#8a8a8a; font-weight:normal; margin-left:8px; }
  h3 { color:var(--blue); font-size:16px; margin:16px 0 8px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:14px; }
  .card { border:1px solid #e3e8ef; border-radius:8px; padding:14px 16px; background:#fbfcfe; }
  .card .t { font-size:13px; color:#666; }
  .card .v { font-size:20px; font-weight:bold; color:var(--navy); }
  .card .n { font-size:12px; color:#999; margin-top:2px; }
  table { width:100%; border-collapse:collapse; font-size:14px; margin:10px 0; }
  th { background:var(--navy); color:#fff; padding:8px 10px; text-align:left; font-weight:normal; }
  td { padding:7px 10px; border-bottom:1px solid #e8edf3; }
  tr:nth-child(even) td { background:#f7fafc; }
  .chart { text-align:center; margin:14px 0; }
  .chart img { max-width:100%; border:1px solid #e8edf3; border-radius:8px; }
  .duo { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media(max-width:720px) { .duo { grid-template-columns:1fr; } }
  .bull { border-top:4px solid var(--green); } .bear { border-top:4px solid var(--red); }
  .panel { background:#fbfcfe; border-radius:8px; padding:14px 16px; }
  .panel h4 { font-size:15px; margin-bottom:8px; }
  .bull h4 { color:var(--green); } .bear h4 { color:var(--red); }
  .panel ul { padding-left:18px; font-size:14px; }
  .panel li { margin-bottom:6px; }
  .fals { background:#fdf6e3; border-radius:6px; padding:8px 12px; font-size:13px; margin-top:10px; }
  .src { font-size:12px; color:#999; margin-top:14px; }
  .disc { font-size:12px; color:#8a8a8a; background:#f0f2f5; border-radius:8px; padding:14px 18px; }
  .up { color:var(--red); font-weight:bold; } .dn { color:var(--green); font-weight:bold; }
  /* 首页卡片 */
  .lib { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:18px; margin-top:8px; }
  .libcard { background:#fff; border-radius:12px; padding:22px 24px; box-shadow:0 1px 4px rgba(0,0,0,.06); border-top:5px solid var(--navy); }
  .libcard .code { font-size:13px; color:#999; }
  .libcard h3 { font-size:19px; margin:2px 0 10px; }
  .libcard .stance { font-size:13px; }
  .libcard p.th { font-size:14px; margin:10px 0; color:#444; }
  .libcard .mini { font-size:12.5px; color:#666; border-top:1px dashed #dde3ea; margin-top:10px; padding-top:8px; }
  .libcard a.btn { display:inline-block; margin-top:12px; background:var(--blue); color:#fff; text-decoration:none; font-size:14px; padding:7px 18px; border-radius:6px; }
  .libcard a.btn:hover { background:var(--navy); }
  .note { background:#eef4fb; border:1px solid #d4e2f0; border-radius:8px; padding:12px 16px; font-size:13px; color:#4a6076; margin-top:18px; }
  /* 预警中心 */
  .al { border-radius:8px; padding:12px 16px; margin:10px 0; font-size:14px; border-left:6px solid; }
  .al.disprove { background:#fdf0ee; border-color:var(--red); }
  .al.prove { background:#eef7f0; border-color:var(--green); }
  .al .tagk { display:inline-block; font-size:12px; font-weight:bold; color:#fff; border-radius:4px; padding:1px 8px; margin-right:8px; }
  .al.disprove .tagk { background:var(--red); }
  .al.prove .tagk { background:var(--green); }
  .al .meta { font-size:12px; color:#999; margin-top:4px; }
  .okline { background:#eef7f0; border:1px solid #cfe6d4; border-radius:8px; padding:12px 16px; font-size:14px; color:#3d6447; }
  .snaptable td, .snaptable th { font-size:13px; }
  .alertdot { display:inline-block; width:9px; height:9px; border-radius:50%; background:#ccc; margin-right:6px; }
  .alertdot.on { background:var(--red); animation:blink 1.2s infinite; }
  @keyframes blink { 50% { opacity:.35; } }
"""

def esc(s):
    return _html.escape(str(s), quote=False)

def b64img(path):
    if not os.path.exists(path):
        return ""
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()

ALERT_JS = """
<script>
(function(){
  var depth = %d;
  var base = depth ? '../' : '';
  fetch(base + 'alerts.json').then(function(r){return r.json();}).then(function(d){
    var box = document.getElementById('alertzone'); if(!box) return;
    var stockFilter = box.getAttribute('data-stock');
    var alerts = d.alerts || [];
    if (stockFilter) alerts = alerts.filter(function(a){ return a.link.indexOf(stockFilter) >= 0; });
    var html = '';
    if (alerts.length === 0) {
      html = '<div class="okline"><span class="alertdot"></span>当前无触发中的预警 —— 各报告立场与证伪条件均未被行情数据验证或推翻（最后检查：' + d.last_check + '）</div>';
    } else {
      alerts.forEach(function(a){
        var tag = a.kind === 'disprove' ? '证伪预警' : '证实信号';
        html += '<div class="al ' + a.kind + '"><span class="tagk">' + tag + '</span><a href="' + base + a.link + '" style="color:var(--navy);font-weight:bold;text-decoration:none">' + a.stock + '</a>：' + a.msg
              + '<div class="meta">触发值 ' + a.value + '（阈值 ' + a.thr + '）｜ 首次触发 ' + a.first_fired + '</div></div>';
      });
    }
    if (!stockFilter && d.snapshot) {
      html += '<table class="snaptable" style="margin-top:14px"><tr><th>标的</th><th>现价</th><th>涨跌%%</th><th>PE(TTM)</th><th>总市值(亿)</th><th>当前立场</th></tr>';
      d.snapshot.forEach(function(s){
        var cls = s.chg >= 0 ? 'up' : 'dn';
        html += '<tr><td><a href="' + s.link + '" style="color:var(--blue)">' + s.name + '</a></td><td>' + s.price + '</td><td class="' + cls + '">' + s.chg + '%%</td><td>' + s.pe + '</td><td>' + s.mktcap + '</td><td>' + s.stance + '</td></tr>';
      });
      html += '</table><div class="src">' + d.note + ' 每个交易日收盘后（15:35）自动检查。</div>';
    }
    box.innerHTML = html;
  }).catch(function(){
    var box = document.getElementById('alertzone'); if(box) box.innerHTML = '<div class="src">预警数据加载失败（alerts.json 尚未生成）。</div>';
  });
})();
</script>
"""


def nav(active, depth=0):
    """depth=0 表示页面位于站点根（index.html）；depth=1 表示位于 reports/ 子目录"""
    pre = '../' * depth
    links = [(f'{pre}index.html', '研报库首页', active == 'home')]
    for code, st in STOCKS.items():
        links.append((f'{pre}reports/{code}.html', st['nav_name'], active == code))
    items = "".join(
        f'<a href="{href}" class="{"active" if on else ""}">{esc(label)}</a>'
        for href, label, on in links)
    return f'<nav class="top"><div class="inner"><span class="brand">个股深度验证</span>{items}</div></nav>'


def render_report(code, st):
    """把一只股票的内容 dict 渲染成完整报告页"""
    kpis = "".join(
        f'<div class="card"><div class="t">{esc(t)}</div><div class="v">{esc(v)}</div><div class="n">{esc(n)}</div></div>'
        for t, v, n in st['kpis'])
    charts = "".join(
        f'<div class="chart"><img src="{b64img(os.path.join(CHART_DIR, c))}"></div><div class="src">{esc(src)}</div>'
        for c, src in st['charts'])
    thesis = "".join(f'<h3>{esc(h)}</h3><p style="font-size:14.5px">{p}</p>' for h, p in st['thesis'])
    sixdim_rows = "".join(f"<tr><td><b>{esc(d)}</b></td><td>{e}</td><td>{esc(c)}</td></tr>" for d, e, c in st['sixdim'])
    bull_items = "".join(f"<li>{i}</li>" for i in st['bull']['items'])
    bear_items = "".join(f"<li>{i}</li>" for i in st['bear']['items'])
    scen_rows = "".join(
        f'<tr><td><b>{esc(n)}</b></td><td>{p}</td><td>{esc(a)}</td><td>{esc(np_)}</td><td>{esc(px)}</td><td class="{cls}">{esc(r)}</td></tr>'
        for n, p, a, np_, px, r, cls in st['scenarios']['rows'])
    watch_rows = "".join(f"<tr><td>{esc(t)}</td><td>{esc(e)}</td><td>{esc(v)}</td></tr>" for t, e, v in st['watch'])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(st['title'])}</title>
<style>{CSS}</style>
</head>
<body>
{nav(code, depth=1)}
<div class="wrap">
<header class="hero">
  <div class="tag">单票深度验证 · {esc(st['asof'])}</div>
  <h1>{esc(st['h1'])}</h1>
  <div class="sub">{esc(st['sub'])}</div>
</header>

<div class="verdict">
  <h2>结论先行 / Executive Verdict</h2>
  <p><span class="stance">{esc(st['verdict_stance'])}</span></p>
  <p style="margin-top:10px">{st['verdict_body']}</p>
  <p style="margin-top:8px">证伪条件（Falsifier）：{esc(st['falsifier'])}</p>
</div>

<section>
  <h2 class="sec">关键数据一览 / Key Figures <span class="en">{esc(st['kpi_note'])}</span></h2>
  <div class="grid">{kpis}</div>
  {charts}
</section>

<section>
  <h2 class="sec">投资逻辑 / Investment Thesis</h2>
  {thesis}
</section>

<section>
  <h2 class="sec">基本面六维扫描 / Six-Dimension Scan</h2>
  <table>
    <tr><th style="width:130px">维度</th><th>证据（含 as-of）</th><th style="width:210px">评价</th></tr>
    {sixdim_rows}
  </table>
</section>

<section>
  <h2 class="sec">多空辩论 / Bull vs Bear <span class="en">双方均取最强论证</span></h2>
  <div class="duo">
    <div class="panel bull">
      <h4>多头最强论证（Bull）</h4>
      <ul>{bull_items}</ul>
      <div class="fals"><b>多头证伪：</b>{esc(st['bull']['fals'])}</div>
    </div>
    <div class="panel bear">
      <h4>空头最强论证（Bear）</h4>
      <ul>{bear_items}</ul>
      <div class="fals"><b>空头证伪：</b>{esc(st['bear']['fals'])}</div>
    </div>
  </div>
</section>

<section>
  <h2 class="sec">概率加权情景 / Probability-Weighted Scenarios <span class="en">{esc(st['scenarios']['note'])}</span></h2>
  <table>
    <tr><th>情景</th><th>概率</th><th>关键假设</th><th>目标年归母净利</th><th>股价区间</th><th>收益率</th></tr>
    {scen_rows}
  </table>
  <p style="font-size:14.5px; margin-top:8px">{st['scenarios']['summary']}</p>
  <div class="src">{esc(st['scenarios']['src'])}</div>
</section>

<section>
  <h2 class="sec">监测清单 / What to Watch <span class="en">带日期的可验证事件</span></h2>
  <table>
    <tr><th>时间</th><th>事件</th><th>验证什么</th></tr>
    {watch_rows}
  </table>
</section>

<section>
  <h2 class="sec">本票预警 / Alert Status <span class="en">指标证实/证伪自动监听</span></h2>
  <div id="alertzone" data-stock="{code}"></div>
</section>

<div class="disc"><b>数据来源与免责声明 / Sources & Disclaimer</b><br>{st['disclaimer']}</div>
{ALERT_JS % 1}
</div>
</body>
</html>"""


def render_home():
    cards = ""
    for code, st in STOCKS.items():
        m = st['lib_meta']
        cards += f"""
    <div class="libcard">
      <div class="code">{esc(m['code'])}</div>
      <h3>{esc(m['name'])}</h3>
      <span class="stance">{esc(m['stance'])}</span>
      <p class="th">{esc(m['thesis'])}</p>
      <div class="mini">{m['mini']}</div>
      <a class="btn" href="reports/{code}.html">查看深度报告 →</a>
    </div>"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>个股深度验证 · 研报库</title>
<style>{CSS}</style>
</head>
<body>
{nav('home')}
<div class="wrap">
<header class="hero">
  <div class="tag">研报库 · 持续更新</div>
  <h1>个股深度验证报告库</h1>
  <div class="sub">每只股票一份独立深度报告：六维扫描、多空辩论、概率加权情景与可验证的证伪条件 ｜ 数据：iFinD · 聚源 Gildata · 券商研报</div>
</header>
<div class="lib">{cards}
</div>
<section>
  <h2 class="sec">指标预警中心 / Alert Center <span class="en">证实 / 证伪自动监听 · 每交易日收盘后检查</span></h2>
  <div id="alertzone"></div>
</section>
{ALERT_JS % 0}
<div class="note">新增股票：准备该票的图表 PNG（命名 <code>&lt;代码&gt;_&lt;图名&gt;.png</code>）与结构化内容后运行站点生成脚本，即可自动新增独立页面与本页卡片。</div>
</div>
</body>
</html>"""


# ============================================================
# 股票内容数据（新增股票在此追加 dict）
# ============================================================
STOCKS = {}

STOCKS['smic'] = dict(
    nav_name="中芯国际",
    title="中芯国际（688981.SH / 0981.HK）单票深度验证",
    asof="as of 2026-09-21",
    h1="中芯国际（688981.SH / 0981.HK）：基本面进入收获期，A 股定价已不便宜",
    sub="SMIC Equity Deep Dive ｜ 数据源：iFinD（同花顺）、聚源 Gildata、券商研报（兴业/中信里昂/招商/华鑫）｜ 货币单位：人民币（另注明美元口径）",
    verdict_stance="立场：观察名单 Watchlist（A股）；新增敞口优先考虑 H 股",
    verdict_body="""公司与证券要分开看：<b>公司逻辑很强</b>——2Q26 收入、毛利率双双大超指引，产能利用率 93.7%、晶圆涨价落地，一致预期 2026 年归母净利 +46.7%；<b>但 A 股证券逻辑偏弱</b>——PE(TTM) 144.9 倍（近五年 62.6% 分位）、PB 6.1 倍对应 ROE 仅约 5%、零股息，A/H 溢价约一倍。当前 A 股价格已计入数年完美兑现，赔率不佳；H 股（65.15 港元，约为 A 股价格一半）是同一逻辑的更优载体。""",
    falsifier="若 3Q26 毛利率低于指引下限 26%、或产能利用率跌破 90%、或晶圆涨价停滞，则“利润收获期”叙事证伪，应退出观察。",
    kpi_note="as of 2026-09-18 unless noted",
    kpis=[
        ("A股收盘价（09-18）", "122.00 元", "近一年区间 91.78 – 163.02 元（iFinD，不复权周线）"),
        ("H股收盘价（09-18）", "65.15 港元", "按 0.92 CNY/HKD 折算 ≈60 元，A/H 溢价约 104%"),
        ("总市值（A股口径）", "10,446 亿元", "Gildata 股票价值分析，2026-09-18"),
        ("PE（TTM）/ 近五年分位", "144.9 倍 / 62.6%", "五年区间 24.6–293.5 倍，中位数 67.3（Gildata）"),
        ("PB（MRQ）", "6.09 倍", "2026H1 ROE 仅 2.77%（半年），年化约 5.5%"),
        ("一致目标价（A股）", "170.99 元", "隐含 +40%；Gildata 一致预期快照 2026-09-20"),
        ("2026E 归母净利（一致预期）", "73.9 亿元", "同比 +46.7%；2027E 92.6 亿、2028E 115.2 亿"),
        ("2Q26 毛利率", "25.3%", "超指引上限（20–22%）；3Q26 指引 26–28%（公司财报，兴业/招商研报转引）"),
    ],
    charts=[
        ("chart_price.png", "来源：iFinD 周线（不复权），2025-09-26 至 2026-09-18；H 股折算汇率 0.92 CNY/HKD 为假设值。"),
        ("chart_gm.png", "来源：公司 2026 半年报（华鑫证券研报转引）；1Q26 毛利率为按 H1 与 2Q 数据的推算值。"),
        ("chart_fin.png", "来源：Gildata 一致预期（2026-09-20 快照）；2026-2028E 为一致预期值。"),
    ],
    thesis=[
        ("正在发生的事：从“产能投入期”迈入“利润收获期”",
         """2Q26 收入 30.06 亿美元（同比 +36.1%、环比 +20.0%），高于指引上限；毛利率 25.3%（环比 +5.2pct）；归母净利 4.79 亿美元，高于市场一致预期约 91%（中信里昂）。驱动因素：产能爬坡 + AI 相关订单提前 + 晶圆涨价（ASP 环比 +5.7% 至 991 美元/片）+ 产能利用率 93.7%。公司指引 3Q26 收入环比 +2–4%、毛利率 26–28%，其中毛利率指引中值高于市场一致预期约 4.9 个百分点。"""),
        ("结构性需求：国产替代 + AI 外溢",
         """2025 年中国大陆及香港收入占比 84.7%（2Q26 升至 90.2%），本土自主可控红利持续兑现；12 英寸收入占比 2Q26 达 78.2%，产品结构升级。公司预计晶圆价格至少在整个 2026 年维持当前水平。来源：iFinD 分部数据（2025 年报，CAS 口径）；兴业证券研报 2026-09-04。"""),
    ],
    sixdim=[
        ("商业模式", "纯晶圆代工 2025 年收入 627.9 亿元、毛利率 21.25%；收入=出货量×ASP，总产能 109.7 万片/月（8 英寸等效，2Q26，招商研报）", "重资产、强周期，规模效应刚进入释放段"),
        ("行业地位", "中国大陆代工龙头、全球第二；成熟制程有政策与需求护城河，先进制程受出口管制约束", "地位稳固，但技术代差是硬约束"),
        ("财务质量", "收入 2024 578.0 亿→2025 673.2 亿（+16.5%）；归母净利 37.0→50.4 亿（+36.3%）；2026H1 归母 44.67 亿已接近 2025 全年；经营现金流 H1 207.6 亿，但同期购建资产现金支出 433.8 亿，FCF 深度为负", "利润表改善真实，现金流被资本开支吞噬"),
        ("管理与资本配置", "折旧 2026 年预计同比 +30% 至约 50 亿美元（公司指引）；少数股东损益 2Q26 达 2.54 亿美元、占利润 34.6%（12 英寸产线少数股权）；股息率 0", "扩产激进、利润漏损明显、股东回报弱"),
        ("估值", "PE(TTM) 144.9 倍（五年 62.6% 分位）、PB 6.1 倍、EV/EBITDA 19.3 倍；2028E 动态 PE 仍约 91.5 倍", "A 股定价远高于历史中枢与全球同业"),
        ("催化剂/风险", "催化剂：3Q26 财报（11 月）、涨价落地、国产 DUV 进展、先进制程良率；风险：AI 订单前置后的需求空窗、成熟制程同业扩产、管制升级、A/H 溢价收敛", "催化剂与风险时间密度都高"),
    ],
    bull=dict(
        items=[
            "2Q26 收入、毛利率、净利三线大超指引，3Q26 毛利率指引中值（27%）再超一致预期 4.9pct——上修周期未结束；",
            "利用率 93.7% + ASP 环比 +5.7% + 涨价延续至 2027 的概率上升，经营杠杆才刚刚开始；",
            "一致预期 2026-2028 归母净利 +46.7%/+25.3%/+24.4%，且仍在向上修正；",
            "中国区收入占比 90%+，国产替代是多年期确定性需求，不受全球消费电子周期单边支配。",
        ],
        fals="3Q26 毛利率低于 26%、或利用率跌破 90%、或 2027 年一致预期开始下修。"),
    bear=dict(
        items=[
            "A 股 PE(TTM) 144.9 倍、PB 6.1 倍 vs ROE 约 5%——估值透支到 2028 年以后，一致目标价 +40% 的空间本身就是“信念价”；",
            "利润的 34.6% 归属少数股东（12 英寸产线外部股权），A 股股东实际分享的盈利打了六五折；",
            "AI 订单存在前置（pull-forward）成分，2027 年折旧再上一个台阶后，一旦涨价停止毛利率将回落；",
            "A/H 溢价约 104%，同股同权下 A 股是全市场最贵的表达方式；出口管制随时可能掐断先进制程叙事。",
        ],
        fals="2027 年一致预期净利持续上破 100 亿元、或先进制程良率/国产设备出现可验证突破。"),
    scenarios=dict(
        note="以 A 股 122 元为基准",
        rows=[
            ("基准 Base", "55%", "涨价延续至 2026 年底，3Q26 指引兑现，估值维持一致目标价水平", "≈93 亿元（一致预期）", "≈171 元", "+40%", "up"),
            ("乐观 Upside", "25%", "AI 外溢持续、2027 继续涨价，2028E 盈利提前兑现", "110–115 亿元", "190–200 元", "+56%~+64%", "up"),
            ("悲观 Downside", "20%", "订单前置后需求空窗 + 折旧压力，毛利率回落至 22% 以下", "≈75 亿元", "90–100 元", "-18%~-26%", "dn"),
        ],
        summary="""概率加权中枢约 <b>160 元</b>（+31%），但分布左尾厚：悲观情景触发时回撤可达 -26%，而当前估值分位（62.6%）并未给出安全边际补偿。若看好该逻辑，H 股以约一半的价格表达同一基本面，风险收益比显著更优。""",
        src="情景与价位为分析判断（evidence_class: judgment），锚定 Gildata 一致目标价 170.99 元（2026-09-20 快照）与近一年价格区间；非收益承诺。"),
    watch=[
        ("2026-11 上旬", "3Q26 业绩发布", "毛利率是否 ≥26%（指引下限）；利用率是否维持 93%+"),
        ("持续跟踪", "晶圆代工报价 / 2027 长约谈判", "涨价是否延续至 2027（公司口径：至少 2026 全年）"),
        ("每季度", "一致预期 4 周变化率", "2027E 净利是否继续上修（当前 92.6 亿）"),
        ("不定期", "出口管制政策、国产 DUV/先进制程进展", "叙事期权是否兑现或证伪"),
        ("持续跟踪", "A/H 溢价、少数股东损益占比", "溢价收敛方向；2Q26 少数股东占利润 34.6% 是否继续扩大"),
    ],
    disclaimer="""财务与行情：iFinD（同花顺）财务报表与周线（CAS 口径，A股 688981.SH；截至 2026-09-18）；估值与一致预期：聚源 Gildata（2026-09-18/20 快照）；经营细节与指引：兴业证券（2026-09-04）、中信里昂/中信证券（2026-08-18）、招商证券（2026-08-16）、华鑫证券（2026-09-01）研报转引的公司财报数据。A/H 折算汇率 0.92 为假设值。<br>
本报告为研究分析，非投资建议或交易指令；情景概率与价位为分析判断。一致预期存在预测偏差，少数股东结构意味着 A 股股东所获盈利与公司总盈利存在系统性差异。""",
    lib_meta=dict(
        code="688981.SH / 0981.HK", name="中芯国际", stance="观察名单（A股）· 优先H股",
        thesis="基本面进入收获期（2Q26 双双超指引），但 A 股 PE 144.9 倍处五年 63% 分位、A/H 溢价约一倍——好公司，贵股票。",
        mini="A股 122.00 元（09-18）｜ PE(TTM) 144.9 倍 / 五年 62.6% 分位 ｜ 一致目标价 170.99 元（+40%）｜ 证伪：3Q26 毛利率 <26%"),
)


STOCKS['eve'] = dict(
    nav_name="亿纬锂能",
    title="亿纬锂能（300014.SZ）单票深度验证",
    asof="as of 2026-09-21",
    h1="亿纬锂能（300014.SZ）：五年估值最低 10% 分位，买的不是电池是“量的确定性”",
    sub="EVE Energy Equity Deep Dive ｜ 数据源：iFinD（同花顺）、聚源 Gildata、券商研报（长江/国海/兴业）｜ 货币单位：人民币",
    verdict_stance="立场：逢低增持 Add（左侧布局，需分批并接受波动）",
    verdict_body="""与中芯国际“好公司贵股票”相反，亿纬锂能是“<b>增长可见度高、估值已至极端低位</b>”的组合：2026H1 动力出货 +66.5%、储能 +54.9%，一致预期 2026-2028 归母净利 +74.7%/+36.2%/+21.9%；而 PE(TTM) 19.2 倍仅处五年 10.2% 分位，2027E 前瞻 PE 约 11 倍、PEG 远低于 1。核心矛盾不在需求，而在<b>毛利率</b>：储能价格战使毛利率三连降至 14.3%，经营现金流转负、存货 +87%。本立场的本质是：以五年最低分位的估值，为“量增 + 毛利率企稳”的期权付费。""",
    falsifier="① 毛利率跌破 13% 或连续两个季度经营现金流为负；② 储能电芯价格战进一步升级（628Ah 等大容量产品跌破现金成本线竞争）；③ 2026E 一致预期（72.2 亿）开始下修。任一触发则降级为观察。",
    kpi_note="as of 2026-09-18 unless noted",
    kpis=[
        ("收盘价（09-18）", "51.56 元", "一年高点 91.00（2025-09-30）→ 低点 48.60（2026-09-11），回撤约 47%"),
        ("PE（TTM）/ 近五年分位", "19.2 倍 / 10.2%", "五年区间 15.4–96.6 倍，中位数 30.6（Gildata）"),
        ("总市值", "约 1,070–1,121 亿元", "iFinD 收盘价 × 20.74 亿股 ≈ 1,069 亿；Gildata 口径 1,120.6 亿"),
        ("一致预期 2026E 归母净利", "72.2 亿元", "+74.7%；2027E 98.4 亿（+36.2%）、2028E 119.9 亿（+21.9%）（Gildata，09-20）"),
        ("一致目标价", "83.31 元", "隐含 +62%；iFinD 预测口径 FY1 净利 71.3 亿（+72.5%）相互印证"),
        ("2026H1 毛利率", "14.3%", "2024A 17.4% → 2025A 16.2% → 2026H1 14.3%，三连降"),
        ("2026H1 出货", "80.2 GWh", "动力 35.76GWh（+66.5%）+ 储能 44.46GWh（+54.9%）（长江证券，09-14）"),
        ("资产负债率 / 经营现金流", "64.2% / -3.88 亿", "2025 年报；H1 存货 154.2 亿（较年初 +87.2%），现金流为战略备货所致"),
    ],
    charts=[
        ("eve_chart_price.png", "来源：iFinD 周线（不复权），2025-09-26 至 2026-09-18。"),
        ("eve_chart_ship.png", "来源：长江证券 2026-09-14 中报分析；国海证券 2025-08-26；兴业证券 2025-04-22。"),
        ("eve_chart_fin.png", "来源：iFinD 财务报表（CAS）；Gildata 一致预期（2026-09-20 快照，2026E 毛利率 15.81%）。"),
        ("eve_chart_pe.png", "来源：Gildata 估值分位（2026-09-20）；前瞻 PE 按 09-18 收盘价 51.56 元 × 总股本 20.74 亿股计算。两家数据源市值口径略有差异（约 5%），已并列标注。"),
    ],
    thesis=[
        ("量的确定性：动储双引擎，出货增速 55%–66%",
         """2026H1 收入 456.91 亿（+62.2%）、归母净利 33.01 亿（+105.7%）；其中 2Q26 单季归母 18.55 亿（+268%）。驱动来自出货量而非价格：动力 +66.5%、储能 +54.9%，费用率从 12.3% 降至 8.8%，经营杠杆释放。储能出货稳居全球第二（2024 年 50.45GWh，+91.9%），46 系列大圆柱进入规模化交付并成为宝马新世代车型首发供应商，628Ah Mr.Big 储能电芯产能陆续释放。来源：长江证券 2026-09-14；国海证券 2025-08-26；兴业证券 2025-04-22。"""),
        ("价的隐忧：毛利率三连降是本轮最大的未解之谜",
         """收入结构里储能占比已近 40% 而储能毛利率仅 12.3%–12.5% 且仍在下行（同比 -1.36pct），加上 5.3% 毛利率的材料贸易收入 68.66 亿，表观收入的高增有一部分是低质量收入。一致预期假设 2026-2028 毛利率稳定在 15.8%–16.0%——意味着市场已在押注“以量补价”阶段结束、价格企稳，这也是本报告情景分歧的核心变量。来源：iFinD 财务报表（CAS）；Gildata 一致预期（2026-09-20 快照）。"""),
    ],
    sixdim=[
        ("商业模式", "动力（42%）+ 储能（40%）+ 消费（18%）三轮驱动；海外收入占 23.6%、毛利率 20.2% 显著高于国内 14.9%（2025 分部，iFinD）", "多元且全球化，但本质上仍是制造环节，议价权有限"),
        ("行业地位", "储能电池出货全球第二；国内首家量产大圆柱动力电池企业（已装车超 6 万台），宝马新世代首发供应商；全球首家量产 600Ah+ 储能电芯", "储能与大圆柱具备真实的产品领先地位"),
        ("财务质量", "2026H1 收入 +62.2%、归母 +105.7%；但毛利率 14.3% 三连降；经营现金流 -3.88 亿（上年同期 +23.7 亿），存货 154.2 亿（+87.2%）；资产负债率 64.2%，少数股东损益占比仅约 4%（利润基本归母）", "利润表高增、现金流量表恶化，需要 Q3 验证备货回报"),
        ("管理与资本配置", "产能全球化：马来西亚已量产、匈牙利 2026 年投产、ACT 布局北美商用车；固态电池 2026 年目标工艺突破、2028 年推进 400Wh/kg；2025 年股权激励费用曾压低表观利润", "布局前瞻，但资本开支高峰未过（固定资产 351.5 亿+在建 194.3 亿）"),
        ("估值", "PE(TTM) 19.2 倍处五年 10.2% 分位；PB 2.2 倍、PS(TTM) 1.4 倍、股息率 1.4%；2026E/2027E/2028E 前瞻 PE 约 14.8/10.9/8.9 倍", "极端低分位 + PEG 远小于 1，安全边际来自估值而非基本面"),
        ("催化剂/风险", "催化剂：Q3 毛利率环比、储能提价落地、628Ah 与 46 大圆柱放量、固态中试进展、海外储能订单；风险：储能价格战、原材料波动、贸易壁垒、汇兑（H1 财务费用 +49.7%）", "未来两个季度是“以量补价”能否切换为“量价齐稳”的验证窗口"),
    ],
    bull=dict(
        items=[
            "量的确定性罕见：动储出货 +55%~66%，储能全球第二，宝马背书大圆柱，订单能见度延伸到 2027；",
            "估值极端：PE 五年 10.2% 分位、2027E 仅 11 倍，PEG 远小于 1，一致目标价 +62%；",
            "经营杠杆已验证：费用率 12.3%→8.8%，即便毛利率再降 1pct，净利仍能靠量增实现 +35% 以上；",
            "负经营现金流是“战略备货”而非需求恶化（公司披露口径），存货在涨价周期中是利润蓄水池而非减值风险。",
        ],
        fals="Q3 毛利率环比继续下行、或存货周转恶化引发减值、或储能报价再下台阶。"),
    bear=dict(
        items=[
            "毛利率三连降（17.4%→16.2%→14.3%），储能仅 12.5% 且仍在跌——“以量补价”可能是持续失血而非过渡；",
            "经营现金流 -3.88 亿 + 存货 +87% + 负债率 64%：在价格战环境中，这组组合历史上通常以减值收场；",
            "收入质量打折：5.3% 毛利的材料贸易贡献了近 70 亿营收，剔除后“真实”增速与盈利能力要下修一档；",
            "2025 年表观净利仅 +1.4%（剔除股权激励与坏账后才有增长），证明盈利质量并非一贯扎实。",
        ],
        fals="Q3 毛利率环比回升 ≥1pct、储能提价落地、或经营现金流转正——则价格战底部确认。"),
    scenarios=dict(
        note="以 51.56 元为基准",
        rows=[
            ("基准 Base", "55%", "2026E 72 亿兑现，毛利率 15.5–16% 企稳，估值修复至一致目标价", "≈98 亿元（一致预期）", "≈83 元", "+61%", "up"),
            ("乐观 Upside", "20%", "储能提价 + 大圆柱上量，2027E 上修至 110 亿+，估值回到五年 30% 分位", "110–120 亿元", "100–110 元", "+94%~+113%", "up"),
            ("悲观 Downside", "25%", "价格战延续，毛利率跌破 13%，2026E 低于 60 亿，估值维持 12 倍", "≈75 亿元", "35–40 元", "-22%~-32%", "dn"),
        ],
        summary="""概率加权中枢约 <b>76 元（+47%）</b>。赔率结构优于中芯国际（左尾 -30% vs 右尾 +100%，且起点估值在最低 10% 分位），但胜率取决于 Q3 毛利率方向——这是与中芯“好公司贵价格”完全不同的风险收益形态：<b>左侧、赔率型仓位</b>，适合分批而非一次性建仓。""",
        src="情景价位为分析判断（evidence_class: judgment），锚定一致目标价 83.31 元（Gildata 2026-09-20）、近一年价格区间与一致预期增速；非收益承诺。"),
    watch=[
        ("2026-10 下旬", "3Q26 业绩发布", "毛利率是否环比回升（关键中的关键）；经营现金流是否转正；存货是否继续攀升"),
        ("持续跟踪", "储能电芯价格（尤其 628Ah 大容量产品报价）", "价格战是否见底——决定 2027E 一致预期方向"),
        ("2026Q4–2027", "46 大圆柱（宝马新世代）交付放量、匈牙利工厂投产", "高毛利动力订单能否对冲储能低价"),
        ("不定期", "固态电池中试线进展（2026 工艺突破目标）", "叙事期权是否兑现"),
        ("每季度", "一致预期 4 周变化率、海外收入占比", "预期方向与结构优化进度"),
    ],
    disclaimer="""财务与行情：iFinD（同花顺）财务报表（CAS）、周线与预测数据（截至 2026-09-18/21）；估值分位与一致预期：聚源 Gildata（2026-09-20 快照）；经营细节：长江证券（2026-09-14）、国海证券（2025-08-26）、兴业证券（2025-04-22）研报转引的公司披露。<br>
本报告为研究分析，非投资建议或交易指令；情景概率与价位为分析判断。一致预期存在预测偏差；毛利率与经营现金流是本报告结论的两个关键脆弱点，请以季度财报持续验证。""",
    lib_meta=dict(
        code="300014.SZ", name="亿纬锂能", stance="逢低增持 Add（左侧分批）",
        thesis="动储出货 +55%~66%、一致预期净利三年复合 +40%+，而 PE 处五年 10.2% 分位——以最低分位估值为“量增+毛利率企稳”的期权付费。",
        mini="现价 51.56 元（09-18，距高点 -47%）｜ PE(TTM) 19.2 倍 / 五年 10.2% 分位 ｜ 一致目标价 83.31 元（+62%）｜ 证伪：毛利率破 13% 或连续两季现金流为负"),
)


STOCKS['fii'] = dict(
    nav_name="工业富联",
    title="工业富联（601138.SH）单票深度验证",
    asof="as of 2026-09-21",
    h1="工业富联（601138.SH）：AI 算力硬件最强业绩兑现者，但五年估值 78% 分位上没有追高赔率",
    sub="Foxconn Industrial Internet Equity Deep Dive ｜ 数据源：iFinD（同花顺）、聚源 Gildata ｜ 货币单位：人民币",
    verdict_stance="立场：持有 Hold —— 已持仓继续持有，回调至 55 元下方（2026E 约 17–18 倍）再转增持",
    verdict_body="""工业富联是当前 A 股<b>业绩兑现最猛的 AI 算力链标的</b>：2025A 收入 9,028.9 亿（+48.2%）、归母 352.9 亿（+52.0%）；2026H1 收入 5,578.6 亿（+54.6%）、归母 237.4 亿（+96.0%），一致预期 2026E 归母 616.7 亿（+74.6%）。但证券层面：PE(TTM) 26.9 倍已处<b>五年 77.7% 分位</b>（中位数仅 17.98 倍），现价 62.71 元对应 2026E 约 20.5 倍——业绩高增已被大幅定价。<b>公司论点（强）与证券论点（中性偏贵）方向相反</b>：现金流结构（2025A 经营现金流仅 52 亿 vs 归母 353 亿）、存货 +56%、负债率 65.7% 说明这是高周转垫资模式，估值容错空间小于表观增速给人的安全感。结论：好公司 + 合理偏贵的股票 = 持有，不在 78% 分位追价。""",
    falsifier="① 北美四大云厂商资本开支指引下修，或英伟达新一代平台出货节奏延后；② 2026E 一致预期（616.7 亿）出现 4 周以上的持续下修；③ 2026H1 起经营现金流与净利润的裂口（H1 OCF 73.9 亿 vs 归母 237.4 亿）在年报继续扩大。任一触发则下调至观察/减仓。",
    kpi_note="as of 2026-09-18/21，分别标注",
    kpis=[
        ("收盘价（09-18）", "62.71 元", "一年高点 80.12（2026-01）→ 低点 47.05（2025-09），现价距高点回撤 -21.7%"),
        ("PE（TTM）/ 近五年分位", "26.9 倍 / 77.7%", "五年区间 7.83–60.34 倍，中位数 17.98（Gildata，2021-09-21 至 2026-09-20）"),
        ("总市值", "约 12,444–12,621 亿元", "Gildata 口径（09-18/09-21）；自由流通市值仅约 2,046–2,099 亿元，筹码集中度高"),
        ("一致预期 2026E 归母净利", "616.7 亿元", "+74.6%；2027E 841.8 亿（+36.5%）、2028E 1,070.1 亿（iFinD，09-21）"),
        ("前瞻估值", "2026E ≈20.5 倍 / 2027E ≈15.0 倍", "按现价市值 12,621 亿 ÷ 一致预期归母计算；PEG（TTM/26E 增速）约 0.36"),
        ("2026H1 盈利质量", "毛利率 5.21% / 归母净利率 4.26%", "2024A 4.51%/3.81% → 2025A 4.69%/3.91% → 2026H1，利润率逆势抬升"),
        ("2026H1 资产负债率 / 存货", "65.7% / 1,921 亿", "存货较年初 +56.2%（2025H1 末 1,229 亿）；高周转垫资模式"),
        ("经营现金流", "2026H1 73.9 亿（+425%）", "但 2025A 全年仅 52.4 亿 vs 归母净利 352.9 亿，利润-现金流裂口显著"),
    ],
    charts=[
        ("fii_chart_price.png", "来源：iFinD 日线（不复权），2025-09-22 至 2026-09-18。"),
        ("fii_chart_fin.png", "来源：iFinD 财务报表（CAS），2024A/2025A/2025H1/2026H1。"),
        ("fii_chart_cash.png", "来源：iFinD 财务报表（CAS）现金流量表与资产负债表。"),
        ("fii_chart_pe.png", "来源：Gildata 估值分位（2026-09-20 快照）；前瞻 PE 按 09-21 总市值 12,620.84 亿与 iFinD 一致预期计算。"),
    ],
    thesis=[
        ("业绩兑现：从“代工叙事”到“报表事实”，增速逐季加速",
         """工业富联是本轮 AI 资本开支周期中报表兑现度最高的 A 股标的之一：2025A 收入 9,028.9 亿（+48.2%）、归母净利 352.9 亿（+52.0%）；2026H1 收入 5,578.6 亿（+54.6%）、归母 237.4 亿（+96.0%），上半年已完成 2025 全年利润的 67%。利润率同样改善：毛利率 4.51%→4.69%→5.21%，归母净利率 3.81%→3.91%→4.26%——在收入近万亿体量上净利率每抬升 0.1pct 约对应 10 亿级利润弹性。少数股东损益占比极小（2026H1 仅 0.09 亿），利润几乎全部归母。来源：iFinD 财务报表（CAS），截至 2026H1。""",
        ),
        ("估值定价：五年 77.7% 分位，赚的是业绩的钱而不是估值的钱",
         """PE(TTM) 26.9 倍处五年 77.7% 分位，远高于中位数 17.98 倍；PB 7.18 倍同样不便宜。支撑估值的是前瞻口径：现价对应 2026E 约 20.5 倍、2027E 约 15.0 倍，PEG 约 0.36——若一致预期兑现，估值将在 12–18 个月内被业绩“消化”回中位区间。因此本票的收益来源排序是：① 业绩超预期兑现 ② 时间换估值消化，而<b>不是</b>③ 估值扩张（78% 分位上扩张空间极小）。这与亿纬锂能（10% 分位）是镜像的两类机会。来源：Gildata（2026-09-20）、iFinD 一致预期（09-21）。""",
        ),
        ("结构隐忧：万亿营收背后是 52 亿经营现金流",
         """2025A 经营现金流净额仅 52.4 亿，不足归母净利 353 亿的 15%；2026H1 改善至 73.9 亿（+425%）但仍远低于利润。同时存货 1,921 亿（较年初 +56.2%）、资产负债率 65.7%——典型的上游占款+存货垫资的高周转模式。该结构在需求上行期是利润放大器（存货随订单升值），但在资本开支退坡时会同时触发存货减值与现金流恶化，是熊市情景的第一块多米诺骨牌。来源：iFinD 财务报表（CAS）。""",
        ),
    ],
    sixdim=[
        ("商业模式", "电子制造服务（EMS）龙头：云计算/AI 服务器为核心增长极，通信及移动网络设备、工业互联网为基本盘；控股股东中坚企业（鸿海系）持股 61.76%（iFinD 公司资料）", "规模壁垒真实，但单客户/单主题集中度高"),
        ("行业地位", "AI 服务器整机与模组的核心组装厂之一，深度绑定全球头部 GPU 平台出货；万亿级营收体量在 A 股制造板块屈指可数", "AI 硬件β敞口最大的 A 股标的之一"),
        ("财务质量", "收入/利润三年台阶式跃升（2024A 232 亿 → 2025A 353 亿 → 2026E 617 亿一致预期）；2026H1 ROE 13.86%（iFinD 指标）；但 2025A OCF 仅 52 亿、存货 +56%、负债率 65.7%", "利润表 A+，现金流量表 B-，结构脆弱点明确"),
        ("管理与资本配置", "鸿海体系全球产能协同（越南基地 2025 年贡献收入 830.6 亿）；研发费率仅 0.9–1.75%，属于制造执行型而非技术定义型公司", "执行力强，技术护城河一般"),
        ("估值", "PE(TTM) 26.9 倍 / 五年 77.7% 分位；PB 7.18；前瞻 2026E 20.5 倍、2027E 15.0 倍；自由流通市值仅约 2,046 亿，筹码集中", "回溯口径贵、前瞻口径合理，分歧全在兑现度"),
        ("催化剂/风险", "催化剂：3Q26 业绩、北美 CSP 资本开支指引、新一代 GPU 平台放量、毛利率环比；风险：AI capex 退坡、存货减值、客户集中、中美贸易摩擦", "未来 6–12 个月的定价核心变量是“AI 资本开支是否见顶”"),
    ],
    bull=dict(
        items=[
            "业绩兑现度全市场顶级：2026H1 归母 +96%，一致预期 2026E +74.6%、2027E +36.5%，且过去几个季度持续超上修；",
            "前瞻估值不贵：2026E 约 20.5 倍、2027E 约 15.0 倍，PEG 约 0.36，业绩消化路径清晰；",
            "利润率逆势抬升（毛利率 4.51%→5.21%），说明 AI 服务器占比提升在真实改善结构，而非纯堆收入；",
            "自由流通市值仅约 2,046 亿，筹码集中，业绩超预期时股价弹性大。",
        ],
        fals="2026E 一致预期开始下修，或 3Q26 毛利率环比转降，或北美 CSP capex 指引转保守。"),
    bear=dict(
        items=[
            "PE 五年 77.7% 分位、PB 7.18 倍：市场已按“capex 多年期上行”定价，任何订单节奏波动都会引发戴维斯双杀；",
            "2025A 经营现金流 52 亿 vs 归母 353 亿 + 存货 1,921 亿（+56%）+ 负债率 65.7%：退坡情景下存货减值与现金流恶化会双杀；",
            "本质是 EMS 组装环节：研发费率不足 1%，议价权与客户结构受制于人，长期利润率天花板低；",
            "近一年股价 -9.5%、距高点 -21.7%，显示聪明资金已在质疑 2027 年之后的需求持续性。",
        ],
        fals="3Q26 经营现金流显著改善（年化向 200 亿靠拢）、存货增速回落至收入增速以下、或 CSP capex 再上修。"),
    scenarios=dict(
        note="以 62.71 元（09-18）为基准",
        rows=[
            ("基准 Base", "50%", "AI capex 延续，2026E 617 亿兑现、2027E 842 亿，估值按 2027E 18 倍", "2027E ≈842 亿元（一致预期）", "≈76 元", "+22%", "up"),
            ("乐观 Upside", "25%", "CSP capex 再上修、新一代平台提前放量，2027E 上修至 950 亿+，给 22 倍", "2027E 950 亿元+", "≈105 元", "+68%", "up"),
            ("悲观 Downside", "25%", "capex 退坡+毛利率回落，2027E 下修至 650 亿，估值回到五年中位下方 12 倍", "2027E ≈650 亿元", "≈39 元", "-37%", "dn"),
        ],
        summary="""概率加权中枢约 <b>74 元（+18%）</b>。右尾 +68% / 左尾 -37% 的不对称度明显差于亿纬锂能（+94% / -30%）——差距就在起点估值：一个是五年 10% 分位，一个是 77.7% 分位。<b>结论由证券论点主导而非公司论点</b>：公司是真成长，但当前价位买入赚的是“兑现”的钱，需要承担 capex 叙事逆转的左尾风险，持有 + 回调加仓优于现价追买。""",
        src="情景价位为分析判断（evidence_class: judgment），锚定 iFinD 一致预期（2026-09-21）、Gildata 五年估值分位（09-20）与近一年价格区间；非收益承诺。"),
    watch=[
        ("2026-10 下旬", "3Q26 业绩发布", "单季归母能否保持 +60% 以上；毛利率环比方向；经营现金流是否显著改善"),
        ("2026-10（美财报季）", "微软/谷歌/亚马逊/Meta 资本开支指引", "2027 年 AI capex 叙事的方向锚——本报告悲观/乐观情景的开关"),
        ("不定期", "英伟达新一代平台出货节奏与工业富联份额", "订单能见度是否延伸到 2027H2"),
        ("每月", "一致预期 4 周变化率（iFinD 预测数据）", "616.7 亿这一数字本身的方向——上修持有、下修降级"),
        ("每季度", "存货增速 vs 收入增速、经营现金流/净利润比", "垫资结构是否健康；存货增速低于收入增速是转增持信号"),
    ],
    disclaimer="""财务与行情：iFinD（同花顺）财务报表（CAS）、日线与公司资料（截至 2026-09-18/21）；估值分位：聚源 Gildata（2026-09-20 快照）；一致预期：iFinD 预测数据（2026-09-21）。<br>
本报告为研究分析，非投资建议或交易指令；情景概率与价位为分析判断。一致预期存在预测偏差；AI 资本开支周期位置与经营现金流质量是本报告结论的两个关键脆弱点，请以季度财报与北美 CSP 指引持续验证。""",
    lib_meta=dict(
        code="601138.SH", name="工业富联", stance="持有 Hold（回调至 55 元下转增持）",
        thesis="AI 算力链业绩兑现最猛：2026H1 归母 +96%、一致预期 2026E +74.6%；但 PE 处五年 77.7% 分位——好公司 + 合理偏贵的股票，赚兑现的钱而非估值的钱。",
        mini="现价 62.71 元（09-18，距高点 -22%）｜ PE(TTM) 26.9 倍 / 五年 77.7% 分位 ｜ 2026E 前瞻 PE 约 20.5 倍 ｜ 证伪：CSP capex 下修或 2026E 一致预期持续下修"),
    )


STOCKS['cmoc'] = dict(
    nav_name="洛阳钼业",
    title="洛阳钼业（603993.SH）单票深度验证",
    asof="as of 2026-09-21",
    h1="洛阳钼业（603993.SH）：五年估值 19% 分位上的铜钴印钞机，赔率高但方向盘在铜价手里",
    sub="CMOC Equity Deep Dive ｜ 数据源：iFinD（同花顺）、聚源 Gildata ｜ 货币单位：人民币",
    verdict_stance="立场：增持 Add（顺周期右侧分批，接受商品波动）",
    verdict_body="""洛阳钼业呈现出与亿纬锂能类似但更干净的赔率结构：<b>PE(TTM) 13.53 倍处五年 19.1% 分位</b>（中位数 18.76 倍），而 2026H1 收入 +42.8%、归母 +86.3%，一致预期 2026E 归母 327.8 亿（+61.2%）、PEG(LYR) 仅 0.37。与工业富联的垫资模式不同，其<b>利润现金含量极高</b>：2024A/2025A/2026H1 经营现金流净额 323.9/208.4/163.3 亿，连续高于归母净利；资产负债率稳定在 50% 左右。风险不在报表，在<b>商品周期</b>：盈利弹性直接绑定铜钴价格，左尾由 LME 铜价决定而非公司经营。结论：以低分位估值买入一台高现金含量的铜钴印钞机，但必须接受商品价格波动带来的 ±30% 区间摆动。""",
    falsifier="① LME 铜价趋势性跌破重要成本支撑区间、钴出口配额政策大幅收紧；② 2026E 一致预期（327.8 亿）出现 4 周以上持续下修；③ 海外矿山（刚果金/巴西）运营中断或税负政策突变；④ 经营现金流/净利润比跌破 0.6。任一触发则降级为持有/观察。",
    kpi_note="as of 2026-09-18/21，分别标注",
    kpis=[
        ("收盘价（09-18）", "17.51 元", "一年高点 26.52（2026-07）→ 低点 12.28（2025-09），现价距高点回撤 -34.0%，近一年 +40.4%"),
        ("PE（TTM）/ 近五年分位", "13.53 倍 / 19.1%", "五年区间 9.77–52.31 倍，中位数 18.76（Gildata，2021-09-21 至 2026-09-21）"),
        ("总市值", "3,763 亿元", "Gildata 口径（09-21）；PB(MRQ) 4.2 倍，滚动股息率 2.17%"),
        ("一致预期 2026E 归母净利", "327.8 亿元", "+61.2%；2027E 364.0 亿（+11.0%）、2028E 414.1 亿（iFinD，09-21）"),
        ("前瞻估值 / PEG", "2026E ≈11.5 倍 / 0.37", "按现价市值 3,763 亿 ÷ 一致预期归母；2027E 约 10.3 倍"),
        ("2026H1 盈利质量", "毛利率 18.5% / 归母净利率 11.9%", "2024A 12.1%/6.4% → 2025A 20.4%/9.8% → 2026H1，盈利能力两年台阶式抬升"),
        ("经营现金流", "2026H1 163.3 亿 ≥ 归母 161.5 亿", "2024A 323.9 亿、2025A 208.4 亿，四期 OCF 均不低于归母净利，现金含量约 100%+"),
        ("资产负债率 / 存货", "52.2% / 451 亿", "2026H1 末；负债率四期稳定在 49.5%–52.2%，无工业富联式垫资结构"),
    ],
    charts=[
        ("cmoc_chart_price.png", "来源：iFinD 日线（不复权），2025-09-22 至 2026-09-18。"),
        ("cmoc_chart_fin.png", "来源：iFinD 财务报表（CAS），2024A/2025A/2025H1/2026H1。"),
        ("cmoc_chart_cash.png", "来源：iFinD 财务报表（CAS）现金流量表与资产负债表。"),
        ("cmoc_chart_pe.png", "来源：Gildata 估值分位（2026-09-21 快照）；前瞻 PE 按 09-21 总市值 3,763.26 亿与 iFinD 一致预期计算。"),
    ],
    thesis=[
        ("业绩兑现：量增 + 价增双轮，利润率两年台阶式抬升",
         """2025A 在收入基本持平（-3.0%）的情况下归母净利 +50.3% 至 203.4 亿，靠的是铜钴产量与价格的共振；2026H1 更进一步：收入 +42.8%、归母 +86.3% 至 161.5 亿，半年完成 2025 全年利润的 79%。毛利率从 12.1% 抬升至 20.4%（2025A）再至 18.5%（2026H1），归母净利率从 6.4% 到 11.9%——在资源股中属于“量价齐升”的强兑现形态。来源：iFinD 财务报表（CAS），截至 2026H1。""",
        ),
        ("现金含量：四期经营现金流均不低于归母净利",
         """与工业富联（2025A OCF 52 亿 vs 归母 353 亿）形成鲜明对照：洛阳钼业 2024A/2025A/2026H1 经营现金流净额分别为 323.9/208.4/163.3 亿，全部不低于同期归母净利。负债率稳定在 50% 左右，无存货膨胀（451 亿对应半年收入 1,353 亿属正常备货）。这意味着<b>盈利质量高、报表左尾风险低</b>——本票的风险敞口几乎全部集中在商品价格这一个变量上。来源：iFinD 财务报表（CAS）。""",
        ),
        ("估值定价：19% 分位 + PEG 0.37，周期股折价已被充分定价",
         """PE(TTM) 13.53 倍处五年 19.1% 分位，仅高于五年最低 9.77 倍；前瞻 2026E 约 11.5 倍、2027E 约 10.3 倍，PEG(LYR) 0.37。市场对周期股的“盈利不可持续”折价已打得比较足——现价隐含的分歧不是“业绩好不好”（H1 +86% 已是事实），而是“铜钴价格能站多久”。这是一个<b>商品价格期权</b>：以低分位估值为铜价中枢抬升的持续性付费。来源：Gildata（09-21）、iFinD 一致预期（09-21）。""",
        ),
    ],
    sixdim=[
        ("商业模式", "铜钴（刚果金 TFM/KFM）为核心利润来源，钼钨（国内）、铌磷（巴西）提供多元化；本质是资源开采+贸易，盈利弹性直接绑定金属价格", "典型商品股：beta 在铜价，alpha 在产量与成本曲线位置"),
        ("行业地位", "全球领先铜钴生产商之一，TFM/KFM 为世界顶级铜钴矿资产；钴产量全球前列，受益于钴出口配额带来的价格支撑", "成本曲线位置靠左，周期底部存活能力强"),
        ("财务质量", "2026H1 收入 +42.8%、归母 +86.3%；毛利率 18.5%、净利率 11.9% 两年抬升；OCF/归母 ≥ 100% 四期连发；负债率 52.2% 稳定", "资源股中少见的“利润表+现金流量表双优”"),
        ("管理与资本配置", "产能扩张与海外资产运营能力经过周期验证；股息率（滚动）2.17%，兼顾股东回报", "执行力已验证，但海外属地政策（税负/配额）是外生变量"),
        ("估值", "PE(TTM) 13.53 倍 / 五年 19.1% 分位；PB 4.2 倍；前瞻 2026E 11.5 倍、2027E 10.3 倍；PEG(LYR) 0.37", "低分位 + 高增速的组合，赔率结构好"),
        ("催化剂/风险", "催化剂：3Q26 业绩、铜价创新高、钴配额收紧推价、TFM/KFM 产量指引上修；风险：铜钴价回落、刚果金政策、汇兑、地缘政治", "定价核心变量只有一个：商品周期位置"),
    ],
    bull=dict(
        items=[
            "量价齐升已兑现：2026H1 归母 +86.3%、半年完成去年全年利润 79%，一致预期 2026E +61.2%；",
            "估值极端便宜：PE 五年 19.1% 分位、2026E 前瞻仅 11.5 倍、PEG 0.37，周期折价已打足；",
            "现金含量顶级：四期 OCF ≥ 归母净利、负债率 50% 稳定，报表无雷；",
            "供给端有故事：钴出口配额 + 铜矿资本开支不足的中期缺口，价格中枢抬升逻辑仍在。",
        ],
        fals="铜价趋势性回落跌破成本支撑、钴配额放松、或 2026E 一致预期开始下修。"),
    bear=dict(
        items=[
            "资源股 PE 低分位可以是“盈利顶部信号”：周期股在利润最高、PE 最低时见顶是历史规律（本票的 PE-TTM 低恰因利润暴涨）；",
            "2027E 一致预期增速骤降至 +11.0%——市场已在预判铜钴价难再上台阶，盈利动能边际衰减；",
            "距一年高点 26.52 元已回撤 -34%，显示资金对商品持续性的定价正在收缩；",
            "海外资产占比高（刚果金/巴西），税负、配额、地缘等外生政策风险无法通过经营对冲。",
        ],
        fals="铜价创新高且站稳、2027E 一致预期重新上修、或公司给出 2027 产量+指引双升——则顶部论破产。"),
    scenarios=dict(
        note="以 17.51 元（09-18）为基准",
        rows=[
            ("基准 Base", "55%", "铜价中枢维持、产量按计划释放，2026E 328 亿兑现、2027E 364 亿，按 2027E 12 倍", "2027E ≈364 亿元（一致预期）", "≈20 元", "+16%", "up"),
            ("乐观 Upside", "25%", "铜价新高 + 钴配额收紧，2027E 上修至 400 亿+，估值修复至五年 30% 分位上方 14 倍", "2027E 400 亿元+", "≈26 元", "+49%", "up"),
            ("悲观 Downside", "20%", "铜钴价回落，2027E 下修至 300 亿，估值打到五年低位 9 倍", "2027E ≈300 亿元", "≈12.6 元", "-28%", "dn"),
        ],
        summary="""概率加权中枢约 <b>20 元（+15.5%）</b>。右尾 +49% / 左尾 -28% 的不对称度优于工业富联（+68% / -37%）、与中芯国际截然不同——因为起点估值在五年 19% 分位。与亿纬锂能相比，本票的<b>胜率更高（现金流扎实、报表无雷）、赔率略低</b>，且胜负手单一而清晰：铜钴价格方向。适合作为组合中的<b>资源/通胀对冲仓位</b>分批持有。""",
        src="情景价位为分析判断（evidence_class: judgment），锚定 iFinD 一致预期（2026-09-21）、Gildata 五年估值分位（09-21）与近一年价格区间；非收益承诺。"),
    watch=[
        ("2026-10 下旬", "3Q26 业绩发布", "单季归母能否保持 +50% 以上；OCF/净利润比是否维持 ≥1"),
        ("每周", "LME 铜价、MB 钴价及钴出口配额政策动向", "商品价格方向——本报告胜负手；铜价跌破关键成本线即触发证伪"),
        ("不定期", "TFM/KFM 产量指引与成本指引", "量的兑现度；指引上修=乐观情景概率上调"),
        ("每月", "一致预期 4 周变化率（iFinD 预测数据）", "327.8 亿的方向——下修即降级"),
        ("每半年", "刚果金税负/配额政策、巴西资产运营", "属地政策风险是唯一的非价格变量"),
    ],
    disclaimer="""财务与行情：iFinD（同花顺）财务报表（CAS）、日线数据（截至 2026-09-18/21）；估值分位与市值：聚源 Gildata（2026-09-21 快照）；一致预期：iFinD 预测数据（2026-09-21）。<br>
本报告为研究分析，非投资建议或交易指令；情景概率与价位为分析判断。一致预期存在预测偏差；铜钴价格方向是本报告结论的最关键变量，且商品价格波动不可由公司经营对冲，请以商品价格与季度财报持续验证。""",
    lib_meta=dict(
        code="603993.SH", name="洛阳钼业", stance="增持 Add（顺周期分批）",
        thesis="铜钴印钞机：2026H1 归母 +86.3%、四期现金流≥净利，而 PE 处五年 19.1% 分位、PEG 0.37——赔率好、报表干净，方向盘在铜价手里。",
        mini="现价 17.51 元（09-18，距高点 -34%）｜ PE(TTM) 13.53 倍 / 五年 19.1% 分位 ｜ 2026E 前瞻 PE 约 11.5 倍 ｜ 证伪：铜价跌破成本线或 2026E 一致预期持续下修"),
    )


STOCKS['yonyou'] = dict(
    nav_name="用友网络",
    title="用友网络（600588.SH）单票深度验证",
    asof="as of 2026-09-22",
    h1="用友网络（600588.SH）：亏损收窄 + 现金流先行转正，但“扭亏”这只靴子还没落地",
    sub="Yonyou Equity Deep Dive ｜ 数据源：iFinD（同花顺）、聚源 Gildata ｜ 货币单位：人民币",
    verdict_stance="立场：观察 Watchlist —— 等“单季扭亏”或“全年亏损收窄至 5 亿以内”的确认信号再升级为增持",
    verdict_body="""用友网络是典型的<b>困境反转候选</b>：归母亏损从 2024A 的 -20.6 亿收窄至 2025A 的 -13.9 亿（-32.6%），2026H1 -9.3 亿继续收窄；收入重回正增长（2026H1 +4.1%），毛利率站上 50.9%；最关键的是<b>现金流先于利润修复</b>——2025A 经营现金流 +8.1 亿转正（2024A 为 -2.7 亿）。估值端 PB 4.87 倍处五年 22.3% 分位、PS(TTM) 3.5 倍，对一家 50% 毛利率的国产 ERP 龙头并不贵。但一致预期 2026E 归母仍为 -2.7 亿、2027E 才转正 +1.2 亿——<b>“反转”目前是收窄斜率，不是既成事实</b>。在亏损期给估值溢价，本质是为期权付费，胜率依赖扭亏时点，因此立场是观察而非左侧增持。""",
    falsifier="① 2026 全年归母亏损超过 5 亿（即显著差于一致预期 -2.7 亿）；② 收入增速再度转负；③ 2026 全年经营现金流重新转负；④ 毛利率跌破 47%。任一触发则排除反转假设，下调为回避。",
    kpi_note="as of 2026-09-21/22，分别标注",
    kpis=[
        ("收盘价（09-21）", "9.57 元", "一年高点 19.01 → 低点 8.75，距高点回撤 -49.7%，近一年 -35.9%；09-22 盘中 9.89 元（+3.34%）"),
        ("PB / 近五年分位", "4.87 倍 / 22.3%", "五年区间 2.91–19.78 倍，中位数 6.03（Gildata，2021-09-22 至 2026-09-21）；亏损期 PE 失效"),
        ("PS（TTM）/ 总市值", "3.51 倍 / 327 亿元", "Gildata（09-21）；对 50% 毛利率的软件公司处于历史偏低区域"),
        ("一致预期 2026E 归母", "-2.7 亿元", "2027E 转正 +1.2 亿、2028E +2.9 亿；2026E 收入 101.0 亿（+10.1%）（iFinD，09-21）"),
        ("2026H1 业绩", "收入 37.27 亿（+4.1%）", "归母 -9.28 亿，较上年同期 -9.45 亿继续减亏；毛利率 50.9% 创新高"),
        ("经营现金流", "2025A +8.12 亿转正", "2024A 为 -2.74 亿；H1 为软件行业回款季节性低谷（2026H1 -10.0 亿，与上年同期相当）"),
        ("减亏斜率", "-20.6 → -13.9 亿", "2025A 同比减亏 32.6%；按一致预期 2026E 再收窄至 -2.7 亿"),
        ("资产负债率", "约 57–61%", "四期区间 57.3%–61.0%，杠杆平稳"),
    ],
    charts=[
        ("yonyou_chart_price.png", "来源：iFinD 日线（不复权），2025-09-22 至 2026-09-21。"),
        ("yonyou_chart_fin.png", "来源：iFinD 财务报表（CAS），2024A/2025A/2025H1/2026H1。"),
        ("yonyou_chart_pb.png", "来源：iFinD 现金流量表（CAS）；Gildata PB 五年分位（2026-09-21 快照）。"),
    ],
    thesis=[
        ("反转的三个先行指标已经全部出现",
         """① 亏损斜率：-20.6 亿 → -13.9 亿 → 一致预期 2026E -2.7 亿，减亏在加速而非减速；② 收入企稳：2025A +0.3% 止跌，2026H1 +4.1% 重回正增长，云订阅转型对收入的拖累期基本过去；③ 现金流先行：2025A 经营现金流 +8.1 亿转正，较利润早至少一年——经营层面最困难的阶段大概率已经过去。同时毛利率从 47.5% 抬升至 50.9%，说明收入结构在优化（云与订阅占比提升）。来源：iFinD 财务报表（CAS）、iFinD 一致预期（09-21）。""",
        ),
        ("但“扭亏”尚未发生，当前买入是在为拐点期权付费",
         """一致预期显示 2026E 仍亏 2.7 亿、2027E 才转正 1.2 亿——即便兑现，2027E 对应市值 327 亿的隐含 PE 仍高达 260 倍+。因此本票的定价不依赖利润，而依赖 PS/PB 分位与“国产 ERP 龙头 + AI 应用落地”的叙事。这种结构下，<b>买点出现在拐点被财报确认之前才有赔率</b>，但过早介入要承担“亏损年限再延长一年”的估值压缩风险。观察立场的本质是：用一次财报确认的代价，换取胜率的跳升。来源：iFinD 一致预期（09-21）、Gildata（09-21）。""",
        ),
    ],
    sixdim=[
        ("商业模式", "国产 ERP/企业管理软件龙头，向云订阅（YonSuite/YonBIP）转型中；毛利率 50.9% 具备典型软件属性", "商业模式本身优秀，问题出在转型期的费用前置"),
        ("行业地位", "国内企业级应用软件头部厂商，国产替代核心受益者之一；大型企业市场与 SAP/Oracle 正面竞争", "品牌与客户基础是真实壁垒"),
        ("财务质量", "连续亏损但收窄：-20.6 → -13.9 亿；毛利率 47.5%→50.9%；OCF 2025A +8.1 亿转正；负债率约 60%", "现金流先于利润修复，是反转假设最强的证据"),
        ("管理与资本配置", "转型期研发与销售费用前置导致亏损；费用管控见效是减亏主因；分红已暂停（滚动股息率为 0）", "减亏靠节流已验证，开源（订阅放量）待验证"),
        ("估值", "PB 4.87 倍 / 五年 22.3% 分位；PS(TTM) 3.51 倍；PE 亏损期失效；距一年高点回撤 -49.7%", "分位偏低但不极端，定价已部分反映减亏预期"),
        ("催化剂/风险", "催化剂：3Q26 单季亏损大幅收窄或扭亏、订阅收入增速、AI+ERP 产品落地；风险：减亏不及预期、宏观 IT 支出疲弱、竞争加剧", "3Q26 是反转假设的关键验证点"),
    ],
    bull=dict(
        items=[
            "减亏加速：-20.6 → -13.9 → 2026E 一致预期 -2.7 亿，2027E 转正——斜率本身在改善；",
            "现金流先行转正（2025A OCF +8.1 亿），历史上现金流拐点平均领先利润拐点一年以上；",
            "PB 五年 22.3% 分位 + PS 3.5 倍 + 50% 毛利率：估值下行空间有限，上行弹性大；",
            "国产替代 + AI 应用是企业软件长逻辑，用友是 A 股最纯正的标的之一。",
        ],
        fals="2026 全年亏损超 5 亿、收入增速转负、或 OCF 再度转负。"),
    bear=dict(
        items=[
            "连亏三年且 2026E 仍亏：扭亏时点已多次后移，“今年转正”的预期历史上被反复证伪；",
            "即便 2027E 转正 1.2 亿，对 327 亿市值隐含 PE 270 倍+——反转兑现后的估值依然不便宜；",
            "收入增速仅 +4.1%：减亏主要靠费用管控而非收入放量，节流型减亏的天花板低；",
            "宏观 IT 支出疲弱背景下，大型企业 ERP 预算可能继续压缩。",
        ],
        fals="3Q26 单季扭亏或亏损收窄至 2 亿以内、订阅收入增速回到 20%+、或 2026E 一致预期上修至盈亏平衡。"),
    scenarios=dict(
        note="以 9.57 元（09-21）为基准，亏损期以 PS 估值",
        rows=[
            ("基准 Base", "50%", "2026E 收入 101 亿、减亏至 -2.7 亿兑现，PS 维持 3.5 倍", "2026E -2.7 亿元（一致预期）", "≈10.3 元", "+8%", "up"),
            ("乐观 Upside", "25%", "3Q26 单季接近扭亏+订阅放量，2027E 净利上修至 3 亿+，PS 修复至 5 倍", "2027E 3 亿元+", "≈14.8 元", "+55%", "up"),
            ("悲观 Downside", "25%", "减亏失速，2026 亏损 >8 亿，PS 压至 2.2 倍（五年最低附近）", "2026E -8 亿元", "≈5.9 元", "-38%", "dn"),
        ],
        summary="""概率加权中枢约 <b>10.3 元（+8%）</b>。右尾 +55% / 左尾 -38% 的不对称度尚可，但与亿纬锂能/洛阳钼业不同——那两票的胜负手是单一外部变量（毛利率/铜价），本票的胜负手是<b>公司内部扭亏时点</b>，可预测性更低。观察立场下，升级触发器非常明确：<b>单季扭亏或全年亏损收窄至 5 亿以内的财报证据</b>。""",
        src="情景价位为分析判断（evidence_class: judgment），锚定 iFinD 一致预期（2026-09-21）、Gildata PB 分位（09-21）；亏损期采用 PS 估值；非收益承诺。"),
    watch=[
        ("2026-10 下旬", "3Q26 业绩发布", "单季亏损是否收窄至 2 亿以内甚至扭亏——反转假设的关键验证"),
        ("每季度", "经营现金流累计值", "全年 OCF 能否维持正值（2026H1 -10.0 亿属季节性，Q4 回款是决胜局）"),
        ("每月", "一致预期 4 周变化率（iFinD 预测数据）", "2026E -2.7 亿的方向——上修至盈亏平衡=立即升级立场"),
        ("不定期", "云订阅收入增速、AI+ERP 产品落地进展", "开源型增长能否接棒节流型减亏"),
        ("持续", "宏观企业 IT 支出景气（招标数据）", "需求端贝塔方向"),
    ],
    disclaimer="""财务与行情：iFinD（同花顺）财务报表（CAS）、日线与预测数据（截至 2026-09-21）；估值分位与市值：聚源 Gildata（2026-09-21 快照）。<br>
本报告为研究分析，非投资建议或交易指令；情景概率与价位为分析判断。一致预期存在预测偏差；扭亏时点与经营现金流持续性是本报告结论的两个关键脆弱点，请以季度财报持续验证。""",
    lib_meta=dict(
        code="600588.SH", name="用友网络", stance="观察 Watchlist（待扭亏信号）",
        thesis="困境反转候选：亏损三年收窄（-20.6→-13.9→预期-2.7亿）、现金流先行转正、毛利率站上 50%，PB 处五年 22% 分位——但“扭亏”尚未发生，等财报确认再上仓位。",
        mini="现价 9.57 元（09-21，距高点 -50%）｜ PB 4.87 倍 / 五年 22.3% 分位 ｜ 2026E 一致预期归母 -2.7 亿 ｜ 证伪：2026 亏损 >5 亿或 OCF 再度转负"),
    )


STOCKS['xiaomi'] = dict(
    nav_name="小米集团",
    title="小米集团-W（1810.HK）单票深度验证",
    asof="as of 2026-09-22",
    h1="小米集团-W（1810.HK）：从 +146% 到 -38%，汽车叙事的定价泡沫挤掉了一半",
    sub="Xiaomi Equity Deep Dive ｜ 数据源：iFinD（同花顺）、聚源 Gildata ｜ 货币单位：港元（财务数据为人民币）",
    verdict_stance="立场：持有 Hold —— 已持仓可守，新仓等 2026H2 盈利环比拐点确认后再加",
    verdict_body="""小米正在经历<b>戴维斯双杀的中段</b>：2025A 收入 4,572.9 亿（+25.0%）、归母 416.4 亿（+76.0%）的高光之后，2026H1 收入 -8.4%、归母 -37.9%，股价从一年高点 59.45 港元回撤 -53.6% 至 27.58 港元。当前 PE(TTM) 18.7 倍、PB 2.29 倍，估值泡沫已挤出大半，但<b>盈利下行的底还没看到</b>：归母净利率从 25H1 的 10.1% 回落至 6.8%。需要注意，本票的<b>一致预期与五年估值分位两个专业数据源（iFinD、Gildata）均未覆盖港股该股</b>，本报告情景完全基于历史财务与情景假设推演，确定性低于其他四票。持有而非增持的理由：盈利拐点未确认；持有而非回避的理由：18.7 倍 PE + 手机×AIoT 基本盘 + 汽车产能爬坡的期权仍在。""",
    falsifier="① 2026 全年归母低于 280 亿（即 H2 环比无改善）；② 汽车业务亏损扩大或交付量环比连续下滑；③ 手机毛利率受存储涨价等挤压继续下行；④ 2026H2 收入同比降幅扩大至双位数。任一触发则下调为回避。",
    kpi_note="as of 2026-09-21，财务数据单位：人民币",
    kpis=[
        ("收盘价（09-21）", "27.58 港元", "一年高点 59.45 → 低点 21.42，距高点回撤 -53.6%，近一年 -50.8%"),
        ("PE（TTM）/ PB", "18.70 倍 / 2.29 倍", "Gildata 港股价值分析（09-21）；PS(TTM) 1.41 倍；五年分位数据两数据源均未覆盖（已披露缺口）"),
        ("总市值", "7,104 亿港元", "Gildata（09-21）；自由流通市值约 5,883 亿港元"),
        ("2025A 业绩（CNY）", "收入 4,572.9 亿（+25.0%）", "归母 416.4 亿（+76.0%）；归母净利率 9.1%（Gildata 港股财务报表）"),
        ("2026H1 业绩（CNY）", "收入 2,080.6 亿（-8.4%）", "归母 141.9 亿（-37.9%）；净利率回落至 6.8%（25H1 为 10.1%）"),
        ("半年度利润轨迹", "228.3 → 188.1 → 141.9 亿", "25H1 → 25H2 → 26H1，利润连续两个半年回落（按累计值推算）"),
        ("一致预期", "两数据源均未覆盖", "iFinD 预测接口与 Gildata 一致预期接口对该港股均无数据——本报告不引用任何卖方预期数字"),
        ("估值锚", "PE-TTM 18.70 倍", "2026-05 至 09 区间约 13.8–20.5 倍（Gildata 港股价值分析逐日序列），当前处于该区间上沿"),
    ],
    charts=[
        ("xiaomi_chart_price.png", "来源：iFinD 日线（不复权），2025-09-22 至 2026-09-21。"),
        ("xiaomi_chart_fin.png", "来源：Gildata 港股财务报表（合并报表，CNY），2024A/2025A/2025H1/2026H1。"),
        ("xiaomi_chart_half.png", "来源：Gildata 港股财务报表，半年度按累计值推算（25H2 = 2025A - 2025H1）。"),
        ("xiaomi_chart_pe.png", "来源：Gildata 港股价值分析逐日 PE-TTM 序列（2026-05 至 2026-09）。"),
    ],
    thesis=[
        ("盈利拐点：从量价齐升到量价齐缩，只用了一年",
         """25H1 归母 +146%（228.3 亿）是本轮顶点；随后 25H2 回落至 188.1 亿，26H1 进一步降至 141.9 亿（-37.9%）。收入端同样走弱：26H1 收入 -8.4%，为转型以来首次半年度负增长。净利率从 10.1% 回落至 6.8%——汽车业务的高投入、手机行业的成本上行与高基数共同作用。<b>当前的核心问题不是“小米好不好”，而是“盈利下行的底部在哪里”</b>，而这个问题只有 2026H2 的财报能回答。来源：Gildata 港股财务报表。""",
        ),
        ("估值：泡沫挤出大半，但缺少分位锚与预期锚",
         """PE(TTM) 18.7 倍较 2026 年中的高点明显回落，PB 2.29 倍、PS 1.41 倍对硬件+生态公司不算贵。但必须披露：本票的五年估值分位与卖方一致预期，iFinD 与 Gildata 均未提供港股覆盖，因此无法像其他四票一样给出“分位数 + 一致预期增速”的双锚定位。退而求其次的锚：2026-05 以来 PE-TTM 区间 13.8–20.5 倍，当前 18.7 倍处区间上沿——<b>如果 2026H2 盈利继续下行，PE 将被盈利而非股价推高</b>，这是持有而非增持的关键原因。来源：Gildata 港股价值分析（09-21）。""",
        ),
        ("期权仍在：汽车产能爬坡与 AIoT 生态是右尾的来源",
         """左尾（盈利继续下行）已被股价定价一半，右尾尚未定价：汽车新车型与产能爬坡、手机高端化、AIoT 出海，任何一项在 2026H2-2027 兑现都能重建增长叙事。这是“持有”而非“回避”的原因——在 27.58 港元（距高点 -54%）交出筹码，等于在盈利底部区域卖出期权。情景加权中枢与现价基本持平，意味着<b>当前价位的风险收益是对称的，方向选择交给下一份财报</b>。""",
        ),
    ],
    sixdim=[
        ("商业模式", "手机 × AIoT × 汽车的生态闭环：硬件获客、互联网服务变现、汽车打开第二曲线", "生态协同是真实壁垒，但硬件本质决定毛利率天花板"),
        ("行业地位", "全球手机出货量头部厂商；汽车首年交付即放量，是新势力中罕见的“出道即主流”玩家", "两个主业均处第一梯队"),
        ("财务质量", "2025A 归母 +76.0% 高光后，26H1 收入 -8.4%、归母 -37.9%、净利率 10.1%→6.8%；港股现金流与资产负债明细本次未完整获取，已披露缺口", "利润下行通道中，底部未确认"),
        ("管理与资本配置", "造车重投入期仍能维持整体盈利，费用管控与供应链能力经过验证；研发投入持续加大（iFinD 口径 2025A 研发费用 47.1 亿 CNY，同比 +40.9%）", "执行力强，资本开支高峰未过"),
        ("估值", "PE(TTM) 18.70 倍、PB 2.29 倍；2026-05 以来 PE 区间 13.8–20.5 倍，当前处上沿；五年分位与一致预期数据缺失（已披露）", "估值合理偏中性，盈利下行可能被动推高 PE"),
        ("催化剂/风险", "催化剂：2026Q3/H2 盈利环比拐点、汽车新车型与交付量、手机毛利率企稳；风险：存储等成本上行、汽车价格战、海外地缘", "胜负手：2026H2 财报的环比方向"),
    ],
    bull=dict(
        items=[
            "估值泡沫已挤出大半：股价距高点 -54%，PE 从 20.5 回落至 18.7，悲观预期已大量定价；",
            "基本盘未坏：手机×AIoT 每年 200 亿+ 归母利润的现金牛仍在，汽车是增量期权而非存量替代；",
            "研发高投入（2025A +40.9%）为下一轮产品力蓄能；",
            "若 2026H2 盈利环比转正，市场将同时上修盈利与估值，弹性可观。",
        ],
        fals="2026H2 归母环比继续下滑、汽车交付量环比连续萎缩、或手机毛利率跌破关键支撑。"),
    bear=dict(
        items=[
            "盈利下行未确认底部：利润已连续两个半年回落（228→188→142 亿），收入出现转型以来首次半年度负增长；",
            "PE 18.7 倍看似合理，但若 2026 全年归母仅 280 亿，前瞻 PE 将被动升至 23 倍+（按 CNY 计）——并不便宜；",
            "汽车价格战 + 存储涨价两头挤压，2027 年之前看不到毛利率修复的明确路径；",
            "一致预期数据缺失本身说明覆盖不足，信息不对称风险高于其他标的。",
        ],
        fals="2026H2 归母环比转正（>160 亿）、汽车月交付创新高、或手机毛利率环比回升——则底部确认。"),
    scenarios=dict(
        note="以 27.58 港元（09-21）为基准；无一致预期，情景基于历史财务推演（judgment）",
        rows=[
            ("基准 Base", "50%", "2026 全年归母约 300 亿（H2 环比改善），2027E 350 亿，给 2027E 18 倍（CNY）", "2027E ≈350 亿元", "≈26.7 港元", "-3%", "dn"),
            ("乐观 Upside", "25%", "汽车产能爬坡+手机高端化兑现，2027E 上修至 420 亿，给 22 倍", "2027E ≈420 亿元", "≈39.1 港元", "+42%", "up"),
            ("悲观 Downside", "25%", "盈利下行延续，2027E 仅 280 亿，估值压至 15 倍", "2027E ≈280 亿元", "≈17.8 港元", "-35%", "dn"),
        ],
        summary="""概率加权中枢约 <b>27.6 港元（≈0%）</b>——当前价位风险收益完全对称，这正是“持有”立场的定量表达：既没有便宜到值得左侧加仓（对比亿纬/洛钼的极端分位），也没有贵到需要卖出（对比中芯 A 股）。<b>方向选择的触发器是 2026H2 财报</b>：归母环比转正则乐观情景概率上调、转增持；继续下行则证伪、转回避。""",
        src="情景价位为分析判断（evidence_class: judgment），锚定 Gildata 港股财务报表（26H1）、PE-TTM 区间（2026-05 至 09）与汇率 1 CNY≈1.09 HKD；iFinD/Gildata 对该股无一致预期与五年分位覆盖，已如实披露；非收益承诺。"),
    watch=[
        ("2026-11", "3Q26 业绩发布", "单季归母环比方向——底部确认或证伪的第一信号"),
        ("2027-03", "2026 年报", "全年归母是否 ≥300 亿；经营现金流与汽车分部亏损披露"),
        ("每月", "汽车交付量数据", "第二曲线的斜率；环比连续下滑触发证伪"),
        ("每季度", "手机毛利率、存储价格走势", "成本端挤压是否缓解"),
        ("不定期", "新车型发布与 AIoT 出海进展", "右尾期权的兑现进度"),
    ],
    disclaimer="""财务与行情：Gildata 港股财务报表（合并报表，CNY，截至 2026H1）与港股价值分析（2026-09-21）；iFinD 日线数据（截至 2026-09-21）。iFinD 一致预期接口与 Gildata 一致预期/五年分位接口对 1810.HK 均无数据覆盖，本报告不使用任何卖方预期数字，相应结论的不确定性高于其他报告。<br>
本报告为研究分析，非投资建议或交易指令；情景概率与价位为分析判断。2026H2 盈利方向是本报告结论的最关键变量，请以季度财报持续验证。""",
    lib_meta=dict(
        code="1810.HK", name="小米集团-W", stance="持有 Hold（待 H2 拐点）",
        thesis="戴维斯双杀中段：25H1 归母 +146% 见顶后连续回落，股价距高点 -54%、PE 18.7 倍——泡沫挤出大半但盈利底部未确认，方向交给 2026H2 财报。",
        mini="现价 27.58 港元（09-21，距高点 -54%）｜ PE(TTM) 18.70 倍 / PB 2.29 ｜ 26H1 归母 -37.9% ｜ 证伪：2026 全年归母 <280 亿或汽车交付连续下滑"),
    )


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    for code, st in STOCKS.items():
        out = os.path.join(REPORTS_DIR, f"{code}.html")
        open(out, "w", encoding="utf-8").write(render_report(code, st))
        print("written:", out)
    home = os.path.join(ROOT, "index.html")
    open(home, "w", encoding="utf-8").write(render_home())
    print("written:", home)


if __name__ == "__main__":
    main()
