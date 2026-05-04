import streamlit as st
import yfinance as yf
import json
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta
import time
import urllib.request
import urllib.parse

# 1. 앱 페이지 설정
st.set_page_config(layout="wide", page_title="AI 실시간 생태계 맵", page_icon="📱")

st.title("📱 AI 산업 실시간 주가 대시보드 (Galaxy S26 Ultra 최적화)")
st.info("SYS_MSG: 변동률 색상 등급화 및 원 크기 통일 설정이 적용되었습니다.")

# ==========================================
# 세션 상태(Session State) 초기화
# ==========================================
if 'tickers_map' not in st.session_state:
    st.session_state.tickers_map = {
        'Google (Gemini)': 'GOOGL', 'Palantir (PLTR)': 'PLTR', 'Salesforce (CRM)': 'CRM',
        'Microsoft (MSFT)': 'MSFT', 'Amazon (AMZN)': 'AMZN', 'NVIDIA (NVDA)': 'NVDA',
        'AMD (AMD)': 'AMD', 'Intel (INTC)': 'INTC', 'TSMC (TSM)': 'TSM',
        'SK하이닉스 (000660)': '000660.KS', '삼성전자 (005930)': '005930.KS',
        'ASML (ASML)': 'ASML', 'Coherent (COHR)': 'COHR', 'Lumentum (LITE)': 'LITE',
        'Arista (ANET)': 'ANET', 'Cisco (CSCO)': 'CSCO', 'Vertiv (VRT)': 'VRT',
        'Apple (AAPL)': 'AAPL', 'Qualcomm (QCOM)': 'QCOM', 'ARM (ARM)': 'ARM'
    }

if 'tree_data' not in st.session_state:
    st.session_state.tree_data = {
        "name": "AI 가치사슬 생태계", "itemStyle": {"color": "#0f766e"},
        "children": [
            {
                "name": "1. 파운데이션 & 에이전트", "itemStyle": {"color": "#10b981"},
                "children": [
                    {"originalName": "Google (Gemini)", "value": 1},
                    {"originalName": "OpenAI (ChatGPT)\n*비상장", "value": 0},
                    {
                        "name": "에이전트 AI", "itemStyle": {"color": "#34d399"},
                        "children": [
                            {"originalName": "Palantir (PLTR)", "value": 1},
                            {"originalName": "Salesforce (CRM)", "value": 1}
                        ]
                    }
                ]
            },
            {
                "name": "2. 클라우드 플랫폼", "itemStyle": {"color": "#0891b2"},
                "children": [
                    {"originalName": "Microsoft (MSFT)", "value": 1},
                    {"originalName": "Amazon (AMZN)", "value": 1}
                ]
            },
            {
                "name": "3. 하드웨어 & 제조", "itemStyle": {"color": "#6366f1"},
                "children": [
                    {
                        "name": "AI 가속기", "itemStyle": {"color": "#818cf8"},
                        "children": [
                            {"originalName": "NVIDIA (NVDA)", "value": 1},
                            {"originalName": "AMD (AMD)", "value": 1},
                            {"originalName": "Intel (INTC)", "value": 1}
                        ]
                    },
                    {
                        "name": "메모리 & 파운드리", "itemStyle": {"color": "#a855f7"},
                        "children": [
                            {"originalName": "TSMC (TSM)", "value": 1},
                            {"originalName": "SK하이닉스 (000660)", "value": 1},
                            {"originalName": "삼성전자 (005930)", "value": 1},
                            {"originalName": "ASML (ASML)", "value": 1}
                        ]
                    }
                ]
            },
            {
                "name": "4. 네트워킹 & 인프라", "itemStyle": {"color": "#f59e0b"},
                "children": [
                    {
                        "name": "광통신 & 스위치", "itemStyle": {"color": "#fbbf24"},
                        "children": [
                            {"originalName": "Coherent (COHR)", "value": 1},
                            {"originalName": "Lumentum (LITE)", "value": 1},
                            {"originalName": "Arista (ANET)", "value": 1},
                            {"originalName": "Cisco (CSCO)", "value": 1}
                        ]
                    },
                    {
                        "name": "전력/냉각", "itemStyle": {"color": "#f97316"},
                        "children": [ {"originalName": "Vertiv (VRT)", "value": 1} ]
                    }
                ]
            },
            {
                "name": "5. 온디바이스 / 엣지", "itemStyle": {"color": "#ec4899"},
                "children": [
                    {"originalName": "Apple (AAPL)", "value": 1},
                    {"originalName": "Qualcomm (QCOM)", "value": 1},
                    {"originalName": "ARM (ARM)", "value": 1}
                ]
            }
        ]
    }

def get_all_node_names(node, names_list):
    name = node.get("originalName", node.get("name", ""))
    display_name = name.split('\n')[0]
    names_list.append(display_name)
    for child in node.get("children", []):
        get_all_node_names(child, names_list)

def add_child_to_node(node, parent_display_name, new_child):
    current_name = node.get("originalName", node.get("name", "")).split('\n')[0]
    if current_name == parent_display_name:
        if "children" not in node:
            node["children"] = []
        node["children"].append(new_child)
        return True
    for child in node.get("children", []):
        if add_child_to_node(child, parent_display_name, new_child):
            return True
    return False

# 사이드바
with st.sidebar:
    st.header("⚙️ 모바일 모니터링 설정")
    auto_refresh = st.checkbox("🔄 10초마다 자동 새로고침", value=False)
    st.divider()
    
    st.header("➕ 새 항목 추가")
    all_nodes = []
    get_all_node_names(st.session_state.tree_data, all_nodes)
    parent_node_name = st.selectbox("어느 항목 아래에?", all_nodes)
    new_node_name = st.text_input("새 항목 이름", placeholder="예: Tesla, 카카오")
    
    c1, c2 = st.columns([7, 3])
    with c1:
        if 'auto_ticker' not in st.session_state: st.session_state.auto_ticker = ""
        new_ticker = st.text_input("티커", key='auto_ticker', placeholder="비워두면 섹터로 생성")
    with c2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔍 찾기", use_container_width=True):
            if new_node_name:
                try:
                    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(new_node_name)}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=3) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        if data.get('quotes'):
                            ticker = data['quotes'][0]['symbol']
                            st.session_state.auto_ticker = ticker
                            st.rerun()
                except: st.warning("오류")

    if st.button("🚀 트리에 추가하기", use_container_width=True):
        if new_node_name:
            final_ticker = st.session_state.auto_ticker.strip()
            is_company = bool(final_ticker)
            new_child = {"originalName": new_node_name, "name": new_node_name, "value": 1 if is_company else 0}
            if not is_company: new_child["itemStyle"] = {"color": "#8b5cf6"}
            success = add_child_to_node(st.session_state.tree_data, parent_node_name, new_child)
            if success and is_company: st.session_state.tickers_map[new_node_name] = final_ticker.upper()
            if success:
                st.session_state.auto_ticker = ""
                st.success("추가 완료")
                st.rerun()

# 2. 데이터 수집 함수 (1분봉 스나이퍼)
@st.cache_data(ttl=60)
def get_market_data(tickers_dict):
    results = {}
    kst = timezone(timedelta(hours=9))
    fetch_time = datetime.now(kst).strftime('%H:%M:%S')
    tickers_list = list(tickers_dict.values())
    try:
        all_data = yf.download(tickers_list, period="6mo", interval="1d", group_by='ticker', auto_adjust=True, progress=False, timeout=10)
        live_data = yf.download(tickers_list, period="1d", interval="1m", group_by='ticker', auto_adjust=True, progress=False, timeout=10)
    except:
        all_data = pd.DataFrame(); live_data = pd.DataFrame()

    for name, ticker in tickers_dict.items():
        try:
            dates = []; prices = []
            if not all_data.empty:
                hist = all_data[ticker].dropna() if len(tickers_list) > 1 else all_data.dropna()
                if not hist.empty:
                    dates = [d.strftime('%m-%d') for d in hist.index]
                    prices = [float(p) for p in hist['Close']]

            live_price = None
            if not live_data.empty:
                l_hist = live_data[ticker].dropna() if len(tickers_list) > 1 else live_data.dropna()
                if not l_hist.empty: live_price = float(l_hist['Close'].iloc[-1])

            if live_price is not None:
                today_str = datetime.now(kst).strftime('%m-%d')
                if len(prices) > 0:
                    if dates[-1] != today_str:
                        dates.append(f"{today_str} (Live)"); prices.append(live_price)
                    else:
                        dates[-1] = f"{today_str} (Live)"; prices[-1] = live_price
                else:
                    dates = [f"{today_str} (Live)"]; prices = [live_price]

            current = prices[-1] if len(prices) > 0 else 100.0
            prev = prices[-2] if len(prices) > 1 else current
            change = ((current - prev) / prev) * 100 if prev != 0 else 0.0

            results[name] = {"price": current, "change": change, "isKRW": ".KS" in ticker or ".KQ" in ticker, "dates": dates, "history": prices}
        except:
            results[name] = {"price": 100.0, "change": 0.0, "isKRW": False, "dates": ["Error"], "history": [100.0]}
    return results, fetch_time

with st.spinner('📡 최신 데이터를 동기화 중입니다...'):
    stock_data, fetch_time = get_market_data(st.session_state.tickers_map)

# 3. 시각화 HTML/JS
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        body { margin: 0; padding: 0; background-color: #0f172a; overflow: hidden; touch-action: none; }
        #chart { width: 100vw; height: 90vh; } 
        .controls { position: absolute; top: 10px; left: 10px; right: 10px; z-index: 10; display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }
        .live-search-input { flex-grow: 2; padding: 8px 10px; font-size: 13px; background-color: #1e293b; color: #f8fafc; border: 1px solid #475569; border-radius: 6px; outline: none; }
        .controls button { padding: 8px 10px; font-size: 12px; flex-grow: 1; text-align: center; }
        .update-time { position: absolute; bottom: 15px; right: 10px; z-index: 10; color: #34d399; font-size: 11px; font-weight: bold; background: rgba(2,44,34,0.9); padding: 6px 10px; border-radius: 6px; border: 1px solid #047857; }
        #chart-modal .modal-content { max-height: 90vh; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="controls">
        <input type="text" id="liveSearch" class="live-search-input w-full md:w-auto mb-1" placeholder="🔍 실시간 종목 검색">
        <button id="centerGraph" class="bg-blue-600 hover:bg-blue-500 text-white rounded shadow font-bold transition-colors w-full md:w-auto">🎯 중앙</button>
        <button id="resetPos" class="bg-slate-700 hover:bg-slate-600 text-white rounded shadow transition-colors w-full md:w-auto">🔄 초기화</button>
    </div>
    <div class="update-time" id="update-time-display">⏱️ 연동 중...</div>
    <div id="chart"></div>
    <div id="chart-modal" class="fixed inset-0 bg-black/90 z-50 hidden flex items-center justify-center p-2 transition-opacity">
        <div class="modal-content bg-slate-800 rounded-xl shadow-2xl p-4 w-full max-w-md relative border border-slate-700">
            <button id="close-modal" class="absolute top-2 right-2 p-2 text-slate-400 hover:text-white"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
            <div class="mb-2 mt-2"><h2 id="modal-title" class="text-xl font-bold text-white mb-1">기업명</h2><p id="modal-price" class="text-lg font-semibold">현재가</p></div>
            <div id="stock-chart" style="width: 100%; height: 250px;"></div>
        </div>
    </div>

<script>
    const liveData = __LIVE_DATA__;
    const treeData = __TREE_DATA__;
    const chart = echarts.init(document.getElementById('chart'), 'dark');
    const savedPos = JSON.parse(localStorage.getItem('ai_ecosystem_nodes_modern')) || {};
    const deletedNodes = JSON.parse(localStorage.getItem('ai_ecosystem_deleted_nodes')) || []; 

    document.getElementById('update-time-display').innerText = '⏱️ __UPDATE_TIME__ (KST)';

    function filterDeletedNodes(node) {
        if (node.children) {
            node.children = node.children.filter(c => !deletedNodes.includes(c.originalName || c.name));
            node.children.forEach(filterDeletedNodes);
        }
    }
    filterDeletedNodes(treeData);

    function process(node) {
        node.originalName = node.originalName || node.name;
        node.id = node.originalName;
        
        if (node.value !== undefined && node.value !== 0 && liveData[node.originalName]) {
            const d = liveData[node.originalName];
            node.rawData = d; 
            node.value = d.price; 
            
            // 🚨 크기 통일: 모든 기업 노드의 크기를 30으로 고정
            node.symbolSize = 30; 
            
            // 🚨 색상 2단계 로직 적용
            let color = '#94a3b8';
            if (d.change >= 10) color = '#FF0000'; // 10% 이상 폭등 (강렬한 빨강)
            else if (d.change > 0) color = '#EF4444'; // 상승 (일반 빨강)
            else if (d.change <= -10) color = '#0000FF'; // 10% 이상 폭락 (강렬한 파랑)
            else if (d.change < 0) color = '#3B82F6'; // 하락 (일반 파랑)
            
            let pStr = d.isKRW ? '₩' + Math.round(d.price).toLocaleString() : '$' + d.price.toFixed(2);
            let cStr = d.change > 0 ? '\\n▲ ' + d.change.toFixed(2) + '%' : (d.change < 0 ? '\\n▼ ' + Math.abs(d.change).toFixed(2) + '%' : '\\n- 0.00%');
            
            node.name = node.originalName + '\\n' + pStr + cStr;
            node.itemStyle = { color: color, borderColor: color };
            node.label = { color: '#f8fafc', fontSize: 10 };
        } else { 
            node.symbolSize = node.children ? 15 : 10; 
            node.label = { color: '#f8fafc', fontSize: 10 };
        }
        if (node.children) node.children.forEach(process);
    }
    process(treeData);

    let gNodes = [], gLinks = [];
    function parseGraph(node, pId) {
        let nData = { id: node.id, name: node.name, originalName: node.originalName, symbolSize: node.symbolSize * 1.3, itemStyle: node.itemStyle, value: node.value, rawData: node.rawData };
        nData.originalItemStyle = { ...node.itemStyle };
        nData.originalSymbolSize = nData.symbolSize;
        if (node.label) { nData.label = { ...node.label }; nData.label.formatter = p => p.data.originalName.split('\\n')[0]; }
        if (savedPos[node.id]) { nData.x = savedPos[node.id].x; nData.y = savedPos[node.id].y; nData.fixed = true; }
        gNodes.push(nData);
        if (pId) gLinks.push({ source: pId, target: node.id });
        if (node.children) node.children.forEach(c => parseGraph(c, node.id));
    }
    parseGraph(treeData, null);

    const graphOpt = {
        tooltip: { trigger: 'item', confine: true, backgroundColor: 'rgba(15, 23, 42, 0.95)', textStyle: { color: '#f8fafc', fontSize: 12 } },
        series: [{ type: 'graph', layout: 'force', data: gNodes, links: gLinks, roam: true, draggable: true, force: { repulsion: 4000, edgeLength: [100, 250], gravity: 0.05, layoutAnimation: false }, label: { show: true, position: 'bottom' }, zoom: 1 }]
    };
    chart.setOption(graphOpt);

    document.getElementById('liveSearch').addEventListener('input', function(e) {
        const query = e.target.value.trim().toLowerCase();
        let matchedIdx = -1;
        gNodes.forEach((node, i) => {
            node.itemStyle = { ...node.originalItemStyle }; node.symbolSize = node.originalSymbolSize;
            if (query && node.originalName.toLowerCase().includes(query)) {
                node.itemStyle = { color: '#fef08a', borderColor: '#eab308', borderWidth: 4, shadowBlur: 30, shadowColor: '#fde047' };
                node.symbolSize = node.originalSymbolSize * 1.5; matchedIdx = i;
            }
        });
        chart.setOption({ series: [{ data: gNodes }] });
        if (matchedIdx !== -1) chart.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: matchedIdx });
    });

    let holdTimer = null;
    chart.on('mousedown', function (params) {
        if (params.data && params.data.originalName) {
            holdTimer = setTimeout(() => {
                if (confirm(`[ ${params.data.originalName} ] 삭제하시겠습니까?`)) {
                    let deleted = JSON.parse(localStorage.getItem('ai_ecosystem_deleted_nodes')) || [];
                    deleted.push(params.data.originalName);
                    localStorage.setItem('ai_ecosystem_deleted_nodes', JSON.stringify(deleted));
                    location.reload();
                }
            }, 3000);
        }
    });
    chart.on('mouseup', () => clearTimeout(holdTimer));

    document.getElementById('centerGraph').onclick = () => chart.setOption({ series: [{ center: null, zoom: 1 }] });
    document.getElementById('resetPos').onclick = () => { localStorage.removeItem('ai_ecosystem_nodes_modern'); localStorage.removeItem('ai_ecosystem_deleted_nodes'); location.reload(); };

    chart.on('click', function(params) {
        if (params.data && params.data.rawData) {
            const data = params.data.rawData;
            document.getElementById('chart-modal').classList.remove('hidden');
            document.getElementById('modal-title').innerText = params.data.originalName;
            let cStr = data.change > 0 ? '▲ ' + data.change.toFixed(2) + '%' : (data.change < 0 ? '▼ ' + Math.abs(data.change).toFixed(2) + '%' : '0.00%');
            document.getElementById('modal-price').innerText = (data.isKRW ? '₩' + Math.round(data.price).toLocaleString() : '$' + data.price.toFixed(2)) + " (" + cStr + ")";
            document.getElementById('modal-price').style.color = params.data.itemStyle.color;
            let stockChart = echarts.init(document.getElementById('stock-chart'), 'dark');
            stockChart.setOption({
                backgroundColor: 'transparent', grid: { left: '15%', right: '5%', bottom: '15%', top: '10%' },
                xAxis: { type: 'category', data: data.dates, axisLabel: { color: '#94a3b8', fontSize: 10 } },
                yAxis: { type: 'value', scale: true, axisLabel: { color: '#94a3b8', fontSize: 10 } },
                series: [{ type: 'line', data: data.history, smooth: true, lineStyle: { color: params.data.itemStyle.color }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: params.data.itemStyle.color }, { offset: 1, color: 'transparent' }]) }, symbol: 'none' }]
            });
        }
    });
    document.getElementById('close-modal').onclick = () => document.getElementById('chart-modal').classList.add('hidden');
    window.onresize = () => chart.resize();
</script>
</body>
</html>
"""

final_html = html_template.replace("__LIVE_DATA__", json.dumps(stock_data)).replace("__TREE_DATA__", json.dumps(st.session_state.tree_data)).replace("__UPDATE_TIME__", fetch_time)
components.html(final_html, height=900)

if auto_refresh:
    time.sleep(10)
    st.rerun()
