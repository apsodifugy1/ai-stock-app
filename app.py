import streamlit as st
import yfinance as yf
import json
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta
import time
import urllib.request
import urllib.parse

# 1. 앱 페이지 설정 (모바일 및 데스크탑 최적화)
st.set_page_config(layout="wide", page_title="AI 실시간 생태계 맵 V5.5", page_icon="📱")

# CSS 커스텀: 프리미엄 다크 UI 및 반응형 정돈
st.markdown("""
    <style>
    .stAlert { background-color: #1e293b; border: 1px solid #334155; color: #f8fafc; }
    div[data-testid="stSidebar"] { background-color: #0f172a; padding-top: 2rem; }
    .stButton button { margin-top: 2px; font-weight: bold; border-radius: 8px; border: 1px solid #334155; width: 100%; }
    .stTextInput input { background-color: #1e293b; color: white; border-radius: 8px; border: 1px solid #334155; }
    .stSelectbox div[data-baseweb="select"] { background-color: #1e293b; color: white; border-radius: 8px; }
    .main { background-color: #0f172a; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("📱 AI 산업 실시간 주가 지휘소 (V5.5)")
st.info("NOTICE: 장비 섹터(AMAT, ASML) 및 에너지망 동기화 완료. 모든 가격은 실시간 서버 기준입니다.")

# ==========================================
# 2. 세션 상태(Session State) 및 데이터 초기화
# ==========================================
if 'tickers_map' not in st.session_state:
    st.session_state.tickers_map = {
        # 에이전트 & 서비스
        'Google (Gemini)': 'GOOGL', 'Palantir (PLTR)': 'PLTR', 'Salesforce (CRM)': 'CRM',
        # 클라우드 플랫폼 (지주)
        'Microsoft (MSFT)': 'MSFT', 'Amazon (AMZN)': 'AMZN', 'Google Cloud': 'GOOGL', 'Oracle (ORCL)': 'ORCL',
        # 하드웨어 & 제조
        'NVIDIA (NVDA)': 'NVDA', 'AMD (AMD)': 'AMD', 'TSMC (TSM)': 'TSM',
        'SK하이닉스': '000660.KS', '삼성전자': '005930.KS', 'Western Digital (SSD)': 'WDC',
        # 장비 & 설계 도구 (핵심 보강)
        'AMAT (증착/식각)': 'AMAT', 'ASML (EUV)': 'ASML', 'KLA (검사)': 'KLAC', 'Synopsys (EDA)': 'SNPS', '한미반도체': '042700.KS',
        # 네트워킹 & 인프라
        'Coherent (COHR)': 'COHR', 'Arista (ANET)': 'ANET', 'Vertiv (VRT)': 'VRT',
        # 에너지 & 전력망
        'Eaton (ETN)': 'ETN', 'HD현대일렉트릭': '267260.KS', 'LS ELECTRIC': '010120.KS', 'Constellation Energy': 'CEG'
    }

if 'tree_data' not in st.session_state:
    st.session_state.tree_data = {
        "name": "AI 가치사슬 생태계", "itemStyle": {"color": "#0f766e"},
        "children": [
            {"name": "1. 파운데이션 & 에이전트", "itemStyle": {"color": "#10b981"}, "children": [{"originalName": "Google (Gemini)", "value": 1}, {"name": "에이전트 AI", "children": [{"originalName": "Palantir (PLTR)", "value": 1}, {"originalName": "Salesforce (CRM)", "value": 1}]}]},
            {"name": "2. 클라우드 플랫폼", "itemStyle": {"color": "#0891b2"}, "children": [{"originalName": "Microsoft (MSFT)", "value": 1}, {"originalName": "Amazon (AMZN)", "value": 1}, {"originalName": "Google Cloud", "value": 1}, {"originalName": "Oracle (ORCL)", "value": 1}]},
            {"name": "3. 하드웨어 & 제조", "itemStyle": {"color": "#6366f1"}, "children": [{"name": "가속기/메모리", "children": [{"originalName": "NVIDIA (NVDA)", "value": 1}, {"originalName": "TSMC (TSM)", "value": 1}, {"originalName": "SK하이닉스", "value": 1}, {"originalName": "삼성전자", "value": 1}]}, {"originalName": "Western Digital (SSD)", "value": 1}]},
            {"name": "4. 장비 & 설계 도구", "itemStyle": {"color": "#8b5cf6"}, "children": [{"originalName": "AMAT (증착/식각)", "value": 1}, {"originalName": "ASML (EUV)", "value": 1}, {"originalName": "KLA (검사)", "value": 1}, {"originalName": "Synopsys (EDA)", "value": 1}, {"originalName": "한미반도체", "value": 1}]},
            {"name": "5. 네트워킹 & 인프라", "itemStyle": {"color": "#f59e0b"}, "children": [{"originalName": "Coherent (COHR)", "value": 1}, {"originalName": "Arista (ANET)", "value": 1}, {"originalName": "Vertiv (VRT)", "value": 1}]},
            {"name": "6. 에너지 & 전력망", "itemStyle": {"color": "#ef4444"}, "children": [{"originalName": "Eaton (ETN)", "value": 1}, {"originalName": "HD현대일렉트릭", "value": 1}, {"originalName": "LS ELECTRIC", "value": 1}, {"originalName": "Constellation Energy", "value": 1}]}
        ]
    }

# 트리 관리 유틸리티
def get_all_node_names(node, names_list):
    name = node.get("originalName", node.get("name", ""))
    names_list.append(name.split('\n')[0])
    if "children" in node:
        for child in node["children"]: get_all_node_names(child, names_list)

def add_child_to_node(node, parent_name, new_child):
    if node.get("originalName", node.get("name", "")).split('\n')[0] == parent_name:
        if "children" not in node: node["children"] = []
        node["children"].append(new_child)
        return True
    if "children" in node:
        for child in node["children"]:
            if add_child_to_node(child, parent_name, new_child): return True
    return False

# ==========================================
# 3. 사이드바 제어판
# ==========================================
with st.sidebar:
    st.header("⚙️ 전략 단말기")
    auto_refresh = st.checkbox("🔄 자동 새로고침 (10s)", value=False)
    st.divider()
    
    st.header("➕ 신규 자산 배치")
    all_nodes = []
    get_all_node_names(st.session_state.tree_data, all_nodes)
    parent_select = st.selectbox("상위 섹터", sorted(list(set(all_nodes))))
    
    if 'found_ticker' not in st.session_state: st.session_state.found_ticker = ""
    new_name = st.text_input("기업 이름")
    
    col1, col2 = st.columns([6, 4])
    with col1: ticker_val = st.text_input("티커", value=st.session_state.found_ticker)
    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔍 찾기"):
            q = urllib.parse.quote((new_name if new_name else ticker_val) + " Stock")
            try:
                url = f"https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=1"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as res:
                    search_res = json.loads(res.read().decode())
                    if search_res.get('quotes'):
                        st.session_state.found_ticker = search_res['quotes'][0]['symbol']
                        st.rerun()
            except: st.error("검색 실패")

    if st.button("🚀 전장 배치"):
        if new_name:
            ticker = ticker_val.strip().upper()
            nc = {"originalName": new_name, "name": new_name, "value": 1 if ticker else 0}
            if add_child_to_node(st.session_state.tree_data, parent_select, nc):
                if ticker: st.session_state.tickers_map[new_name] = ticker
                st.session_state.found_ticker = ""; st.success("배치 완료"); st.rerun()

# ==========================================
# 4. 실시간 데이터 수집 엔진
# ==========================================
@st.cache_data(ttl=60)
def get_market_data(t_map):
    res = {}
    kst = timezone(timedelta(hours=9))
    t_list = list(t_map.values())
    try:
        h = yf.download(t_list, period="6mo", interval="1d", group_by='ticker', auto_adjust=True, progress=False)
        l = yf.download(t_list, period="1d", interval="1m", group_by='ticker', auto_adjust=True, progress=False)
    except: h = pd.DataFrame(); l = pd.DataFrame()

    for name, t in t_map.items():
        try:
            df = h[t].dropna() if len(t_list) > 1 else h.dropna()
            ld = l[t].dropna() if len(t_list) > 1 else l.dropna()
            dates = [d.strftime('%m-%d') for d in df.index]
            prices = [float(p) for p in df['Close']]
            
            if not ld.empty:
                cp = float(ld['Close'].iloc[-1])
                today = datetime.now(kst).strftime('%m-%d')
                if dates[-1] != today:
                    dates.append(today + "(L)"); prices.append(cp)
                else: prices[-1] = cp
                
            curr = prices[-1]; prev = prices[-2] if len(prices) > 1 else curr
            chg = ((curr - prev) / prev) * 100 if prev != 0 else 0
            res[name] = {"price": curr, "change": chg, "isKRW": ".KS" in t or ".KQ" in t, "dates": dates, "history": prices}
        except: res[name] = {"price": 0, "change": 0, "isKRW": False, "dates": [], "history": []}
    return res, datetime.now(kst).strftime('%H:%M:%S')

stock_data, f_time = get_market_data(st.session_state.tickers_map)

# ==========================================
# 5. 시각화 HTML/JS 프레임워크
# ==========================================
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        body { margin: 0; background-color: #0f172a; overflow: hidden; font-family: sans-serif; touch-action: none; }
        #chart { width: 100vw; height: 92vh; }
        .controls { position: absolute; top: 10px; left: 10px; right: 10px; z-index: 10; display: flex; gap: 8px; }
        .search-bar { flex-grow: 1; padding: 12px; border-radius: 12px; background: #1e293b; color: white; border: 1px solid #334155; outline: none; font-size: 14px; }
        .update-time { position: absolute; bottom: 15px; right: 15px; color: #10b981; font-size: 11px; font-weight: bold; background: rgba(15,23,42,0.8); padding: 5px 10px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="controls"><input type="text" id="searchInput" class="search-bar" placeholder="🔍 자산 실시간 검색 (예: AMAT, 삼전)"></div>
    <div class="update-time" id="time-display">⏱️ __TIME__</div>
    <div id="chart"></div>

    <div id="modal" class="fixed inset-0 bg-black/90 hidden flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 p-6 rounded-3xl w-full max-w-md relative border border-slate-700 shadow-2xl">
            <button onclick="document.getElementById('modal').classList.add('hidden')" class="absolute top-4 right-4 text-slate-400 text-2xl">✕</button>
            <h2 id="m-title" class="text-2xl font-bold text-white mb-1"></h2>
            <p id="m-price" class="text-xl font-semibold mb-6"></p>
            <div id="sub-chart" style="width:100%; height:300px;"></div>
        </div>
    </div>

<script>
    const ld = __LIVE_DATA__; const td = __TREE_DATA__;
    const chart = echarts.init(document.getElementById('chart'), 'dark');
    const deleted = JSON.parse(localStorage.getItem('ai_del_v5')) || [];

    function filter(node) {
        if (node.children) {
            node.children = node.children.filter(c => !deleted.includes(c.originalName || c.name));
            node.children.forEach(filter);
        }
    }
    filter(td);

    function prep(n) {
        n.originalName = n.originalName || n.name; n.id = n.originalName;
        if (n.value && ld[n.id]) {
            const d = ld[n.id]; n.raw = d; n.value = d.price;
            let c = d.change > 0 ? '#ef4444' : (d.change < 0 ? '#3b82f6' : '#94a3b8');
            let pS = d.isKRW ? '₩'+Math.round(d.price).toLocaleString() : '$'+d.price.toFixed(2);
            let cS = '\\n' + (d.change > 0 ? '▲' : '▼') + Math.abs(d.change).toFixed(2) + '%';
            n.name = n.id + '\\n' + pS + cS; n.itemStyle = { color: c }; n.symbolSize = 32;
        } else { n.symbolSize = n.children ? 18 : 10; }
        if (n.children) n.children.forEach(prep);
    }
    prep(td);

    let gNodes = [], gLinks = [];
    function parse(n, pid) {
        let nd = { id: n.id, name: n.name, orig: n.id, symbolSize: n.symbolSize*1.3, itemStyle: n.itemStyle, raw: n.raw };
        nd.origStyle = { ...n.itemStyle }; nd.origSize = nd.symbolSize;
        gNodes.push(nd); if (pid) gLinks.push({ source: pid, target: n.id });
        if (n.children) n.children.forEach(c => parse(c, n.id));
    }
    parse(td, null);

    chart.setOption({
        series: [{ type: 'graph', layout: 'force', data: gNodes, links: gLinks, roam: true, draggable: true, force: { repulsion: 4000, edgeLength: [130, 260], gravity: 0.1 }, label: { show: true, position: 'bottom', fontSize: 11, color: '#f8fafc' }, zoom: 1 }]
    });

    // 검색
    document.getElementById('searchInput').oninput = (e) => {
        const q = e.target.value.toLowerCase();
        gNodes.forEach(n => {
            if (q && n.orig.toLowerCase().includes(q)) {
                n.itemStyle = { color: '#facc15', borderWidth: 2, borderColor: '#fff' }; n.symbolSize = n.origSize * 1.6;
            } else { n.itemStyle = n.origStyle; n.symbolSize = n.origSize; }
        });
        chart.setOption({ series: [{ data: gNodes }] });
    };

    // 상세 팝업
    chart.on('click', (pa) => {
        if (pa.data && pa.data.raw) {
            const d = pa.data.raw; document.getElementById('modal').classList.remove('hidden');
            document.getElementById('m-title').innerText = pa.data.orig;
            document.getElementById('m-price').innerText = (d.isKRW ? '₩'+Math.round(d.price).toLocaleString() : '$'+d.price.toFixed(2)) + " (" + d.change.toFixed(2) + "%)";
            document.getElementById('m-price').style.color = d.change >= 0 ? '#ef4444' : '#3b82f6';
            let sc = echarts.init(document.getElementById('sub-chart'), 'dark');
            sc.setOption({
                grid: { left: '15%', right: '5%', bottom: '15%', top: '10%' },
                dataZoom: [{ type: 'inside' }, { type: 'slider', height: 20 }],
                xAxis: { type: 'category', data: d.dates }, yAxis: { scale: true },
                series: [{ type: 'line', data: d.history, smooth: true, lineStyle: { color: '#facc15' }, symbol: 'none' }]
            });
        }
    });

    // 삭제 (3초)
    let h;
    chart.on('mousedown', (pa) => {
        if (pa.data && pa.data.orig) {
            h = setTimeout(() => {
                if (confirm(pa.data.orig + " 삭제?")) {
                    deleted.push(pa.data.orig); localStorage.setItem('ai_del_v5', JSON.stringify(deleted));
                    location.reload();
                }
            }, 3000);
        }
    });
    chart.on('mouseup', () => clearTimeout(h));
    window.onresize = () => chart.resize();
</script>
</body>
</html>
"""
components.html(html_template.replace("__LIVE_DATA__", json.dumps(stock_data)).replace("__TREE_DATA__", json.dumps(st.session_state.tree_data)).replace("__TIME__", f_time), height=900)

if auto_refresh: time.sleep(10); st.rerun()
