import streamlit as st
import yfinance as yf
import json
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta
import time

# 1. 앱 페이지 설정 (깔끔한 모던 스타일 복구)
st.set_page_config(layout="wide", page_title="AI 실시간 생태계 맵", page_icon="📱")

st.title("📱 AI 산업 실시간 주가 대시보드 (Galaxy S26 Ultra 최적화)")
st.info("SYS_MSG: 원 위치 고정 및 오늘(Live) 데이터 연동이 적용된 깔끔한 버전입니다.")

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

# 트리 데이터
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

# 트리 노드 재귀 탐색 및 추가 함수 (복구됨!)
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

# 사이드바 (종목 검색 및 추가 기능 복구)
with st.sidebar:
    st.header("⚙️ 모바일 모니터링 설정")
    auto_refresh = st.checkbox("🔄 10초마다 자동 새로고침", value=False)
    if auto_refresh:
        st.success("자동 새로고침 켜짐")
    
    st.divider()

    # 🚀 신규 기능: 종목 검색 창
    st.header("🔍 종목 검색 (맵에서 찾기)")
    search_query = st.text_input("기업명 또는 티커 입력", placeholder="예: NVDA, Apple")
    
    st.divider()
    
    # 🚀 복구된 기능: 항목 추가
    st.header("➕ 새 항목 추가")
    all_nodes = []
    get_all_node_names(st.session_state.tree_data, all_nodes)
    parent_node_name = st.selectbox("어느 항목 아래에?", all_nodes)
    
    new_node_name = st.text_input("새 항목 이름", placeholder="예: Tesla")
    new_ticker = st.text_input("티커 (주식인 경우 필수)", placeholder="예: TSLA")
    
    if st.button("🚀 트리에 추가하기", use_container_width=True):
        if new_node_name:
            is_company = bool(new_ticker.strip())
            new_child = {
                "originalName": new_node_name, 
                "name": new_node_name,
                "value": 1 if is_company else 0
            }
            if not is_company:
                new_child["itemStyle"] = {"color": "#8b5cf6"}
            
            success = add_child_to_node(st.session_state.tree_data, parent_node_name, new_child)
            
            if success and is_company:
                st.session_state.tickers_map[new_node_name] = new_ticker.strip().upper()
                
            if success:
                st.success(f"'{new_node_name}' 추가 완료!")
                st.rerun()
        else:
            st.error("이름을 입력해주세요.")

# 2. 데이터 수집 함수 (퀀텀 스나이퍼 엔진 장착)
@st.cache_data(ttl=60)
def get_market_data(tickers_dict):
    results = {}
    kst = timezone(timedelta(hours=9)) # 한국 시간(KST) 세팅
    fetch_time = datetime.now(kst).strftime('%H:%M:%S')

    try:
        # 1. 과거 차트(6개월) 데이터 일괄 다운로드 (시간 절약)
        tickers_list = list(tickers_dict.values())
        all_data = yf.download(tickers_list, period="6mo", interval="1d", group_by='ticker', auto_adjust=True, progress=False, timeout=10)
    except:
        all_data = pd.DataFrame()

    # 2. [강력한 실시간 엔진] fast_info로 '절대 최신(Live)' 호가창 가격을 1:1 저격
    for name, ticker in tickers_dict.items():
        try:
            t = yf.Ticker(ticker)
            # fast_info는 과거 차트가 덜 만들어졌더라도, 현재 거래소에서 체결되는 가장 최신 가격을 즉시 가져옵니다.
            live_price = float(t.fast_info.last_price)
            prev_close = float(t.fast_info.previous_close)
            volume = float(t.fast_info.last_volume)
            change = ((live_price - prev_close) / prev_close) * 100 if prev_close else 0.0

            dates = []
            prices = []
            
            # 과거 차트 데이터 추출
            if not all_data.empty:
                if len(tickers_list) > 1 and ticker in all_data:
                    hist = all_data[ticker].dropna()
                elif len(tickers_list) == 1:
                    hist = all_data.dropna()
                else:
                    hist = pd.DataFrame()
                    
                if not hist.empty:
                    dates = [d.strftime('%m-%d') for d in hist.index]
                    prices = [float(p) for p in hist['Close']]
            
            # 실시간 가격을 차트 마지막에 강제 주입!
            if len(prices) > 0:
                today_str = datetime.now(kst).strftime('%m-%d')
                # 만약 차트의 마지막 가격이 현재 라이브 가격과 다르면 (야후 서버가 아직 차트 업데이트를 안 했다면)
                if abs(prices[-1] - live_price) > (live_price * 0.001): 
                    dates.append(f"{today_str} (Live)")
                    prices.append(live_price)
                else:
                    # 이미 반영되어 있다면 태그만 추가
                    dates[-1] = f"{today_str} (Live)"
                    prices[-1] = live_price
            else:
                dates = ["Live"]
                prices = [live_price]

            results[name] = {
                "price": live_price, 
                "change": change, 
                "volume": volume, 
                "isKRW": ".KS" in ticker or ".KQ" in ticker,
                "isMock": False, 
                "dates": dates, 
                "history": prices
            }
        except Exception as e:
            # 데이터 수집 실패 시 빈 데이터 방지
            results[name] = {"price": 100.0, "change": 0.0, "volume": 0, "isKRW": False, "isMock": True, "dates": ["Error"], "history": [100.0]}
            
    return results, fetch_time

# 데이터 불러오기
with st.spinner('📡 퀀텀 엔진으로 실시간 가격을 추적 중입니다...'):
    stock_data, fetch_time = get_market_data(st.session_state.tickers_map)

# 3. 시각화 HTML/JS 템플릿 (깔끔한 테마 원복 + 기능 유지 + 검색 하이라이트 추가)
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
        
        .controls { 
            position: absolute; top: 10px; left: 10px; right: 10px; z-index: 10; 
            display: flex; flex-wrap: wrap; gap: 5px; 
        }
        .controls button { 
            padding: 8px 10px; font-size: 12px; flex-grow: 1; text-align: center;
        }
        
        .update-time { 
            position: absolute; bottom: 15px; right: 10px; z-index: 10; 
            color: #34d399; font-size: 11px; font-weight: bold; background: rgba(2,44,34,0.9); 
            padding: 6px 10px; border-radius: 6px; border: 1px solid #047857; 
        }

        #chart-modal .modal-content {
            max-height: 90vh;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="controls">
        <button id="centerGraph" class="bg-blue-600 hover:bg-blue-500 text-white rounded shadow font-bold transition-colors w-full">🎯 네트워크 중앙 정렬</button>
        <button id="resetPos" class="bg-slate-700 hover:bg-slate-600 text-white rounded shadow transition-colors w-full mt-1">🔄 맵 초기화 (처음 1회 클릭)</button>
    </div>
    
    <div class="update-time" id="update-time-display">⏱️ 연동 중...</div>
    
    <div id="chart"></div>

    <div id="chart-modal" class="fixed inset-0 bg-black/90 z-50 hidden flex items-center justify-center p-2 transition-opacity">
        <div class="modal-content bg-slate-800 rounded-xl shadow-2xl p-4 w-full max-w-md relative border border-slate-700">
            <button id="close-modal" class="absolute top-2 right-2 p-2 text-slate-400 hover:text-white transition-colors focus:outline-none">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
            <div class="mb-2 mt-2">
                <h2 id="modal-title" class="text-xl font-bold text-white mb-1 leading-tight">기업명</h2>
                <p id="modal-price" class="text-lg font-semibold">현재가</p>
            </div>
            <div id="stock-chart" style="width: 100%; height: 250px;"></div>
            <p class="text-[10px] text-slate-500 mt-2 text-right">* 최근 6개월 추이 (스크롤 가능)</p>
        </div>
    </div>

<script>
    const liveData = __LIVE_DATA__;
    const treeData = __TREE_DATA__;
    const searchQuery = __SEARCH_QUERY__.trim().toLowerCase();
    
    const chart = echarts.init(document.getElementById('chart'), 'dark');
    const savedPos = JSON.parse(localStorage.getItem('ai_ecosystem_nodes_modern')) || {};

    document.getElementById('update-time-display').innerText = '⏱️ __UPDATE_TIME__ (KST)';

    function process(node) {
        node.id = node.originalName || node.name;
        if (node.value !== undefined && node.value !== 0 && liveData[node.originalName]) {
            const d = liveData[node.originalName];
            node.rawData = d; 
            node.value = d.price; 
            
            node.symbolSize = Math.max(20, Math.min(50, 15 + (d.volume / 3000000))); 
            
            let color = '#94a3b8';
            let pStr = d.isKRW ? '₩' + Math.round(d.price).toLocaleString() : '$' + d.price.toFixed(2);
            let cStr = '\\n- 0.00%';
            
            if (d.change > 0) { color = '#ef4444'; cStr = '\\n▲ ' + d.change.toFixed(2) + '%'; }
            else if (d.change < 0) { color = '#3b82f6'; cStr = '\\n▼ ' + Math.abs(d.change).toFixed(2) + '%'; }
            
            node.name = node.originalName + '\\n' + pStr + cStr;
            node.itemStyle = { color: color, borderColor: color };
        } else { 
            node.symbolSize = node.children ? 14 : 10; 
        }
        if (node.children) node.children.forEach(process);
    }
    process(treeData);

    const customTooltip = {
        trigger: 'item', backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: '#334155', textStyle: { color: '#f8fafc', fontSize: 12 },
        confine: true, 
        formatter: function (info) {
            if (!info.data || !info.data.rawData) return info.name.replace(/\\n/g, '<br/>');
            const d = info.data.rawData;
            let title = info.data.originalName.split('\\n')[0];
            let pStr = d.isKRW ? '₩' + Math.round(d.price).toLocaleString() : '$' + d.price.toFixed(2);
            let cStr = d.change > 0 ? '▲ ' + d.change.toFixed(2) + '%' : (d.change < 0 ? '▼ ' + Math.abs(d.change).toFixed(2) + '%' : '- 0.00%');
            let color = d.change > 0 ? '#ef4444' : (d.change < 0 ? '#3b82f6' : '#94a3b8');
            return `
                <div style="font-weight:bold; border-bottom: 1px solid #475569; padding-bottom: 4px; margin-bottom: 4px; font-size: 13px;">${title}</div>
                <div style="color: ${color}; font-size: 14px; font-weight: bold;">${pStr} <span style="font-size: 11px;">(${cStr})</span></div>
                <div style="font-size: 10px; color: #94a3b8; margin-top: 4px;">터치하여 차트 열기 👆</div>
            `;
        }
    };

    let gNodes = [], gLinks = [];
    function parseGraph(node, pId) {
        let nData = { 
            id: node.id, name: node.name, originalName: node.originalName || node.name, 
            symbolSize: node.symbolSize * 1.3, itemStyle: node.itemStyle, 
            value: node.value, rawData: node.rawData 
        };
        
        if (savedPos[node.id]) {
            nData.x = savedPos[node.id].x;
            nData.y = savedPos[node.id].y;
            nData.fixed = true; 
        }

        gNodes.push(nData);
        if (pId) gLinks.push({ source: pId, target: node.id });
        if (node.children) node.children.forEach(c => parseGraph(c, node.id));
    }
    parseGraph(treeData, null);

    const graphOpt = {
        tooltip: customTooltip,
        series: [{
            type: 'graph', layout: 'force', data: gNodes, links: gLinks, roam: true, draggable: true,
            scaleLimit: { min: 0.1, max: 20 },
            // 둥둥 떠다니기 고정 및 겹침 방지(4000) 유지
            force: { repulsion: 4000, edgeLength: [80, 200], gravity: 0.05, layoutAnimation: false }, 
            label: { show: true, position: 'bottom', fontSize: 10, formatter: p => p.data.originalName.split('\\n')[0], color: '#f8fafc' },
            zoom: 1
        }]
    };

    chart.setOption(graphOpt);

    // 🚀 종목 검색 하이라이트 로직
    if (searchQuery) {
        let matchedNode = null;
        for (let i = 0; i < gNodes.length; i++) {
            if (gNodes[i].originalName.toLowerCase().includes(searchQuery)) {
                matchedNode = gNodes[i];
                break;
            }
        }
        if (matchedNode) {
            setTimeout(() => {
                chart.dispatchAction({ type: 'highlight', name: matchedNode.name });
                chart.dispatchAction({ type: 'showTip', name: matchedNode.name });
            }, 500);
        }
    }

    function savePositions() {
        const layoutData = chart.getModel().getSeriesByIndex(0).getData();
        const posMap = JSON.parse(localStorage.getItem('ai_ecosystem_nodes_modern')) || {};
        gNodes.forEach((n, i) => {
            const layout = layoutData.getItemLayout(i);
            if (layout && !isNaN(layout[0])) posMap[n.id] = { x: layout[0], y: layout[1] };
        });
        localStorage.setItem('ai_ecosystem_nodes_modern', JSON.stringify(posMap));
    }

    chart.on('mouseup', function() { savePositions(); });

    // 중앙 정렬 버튼
    document.getElementById('centerGraph').onclick = () => {
        chart.setOption({ series: [{ center: null, zoom: 1 }] });
    };
    
    // 배치 초기화
    document.getElementById('resetPos').onclick = () => { localStorage.removeItem('ai_ecosystem_nodes_modern'); location.reload(); };

    const modal = document.getElementById('chart-modal');
    let stockChartInstance = null;

    chart.on('click', function(params) {
        if (params.data && params.data.rawData) openModal(params.data.rawData, params.data.originalName.split('\\n')[0], params.data.itemStyle.color);
    });

    function openModal(data, title, color) {
        modal.classList.remove('hidden');
        document.getElementById('modal-title').innerText = title;
        let pStr = data.isKRW ? '₩' + Math.round(data.price).toLocaleString() : '$' + data.price.toFixed(2);
        let cStr = data.change > 0 ? '▲ ' + data.change.toFixed(2) + '%' : (data.change < 0 ? '▼ ' + Math.abs(data.change).toFixed(2) + '%' : '- 0.00%');
        document.getElementById('modal-price').innerText = pStr + " (" + cStr + ")";
        document.getElementById('modal-price').style.color = color;

        if (!stockChartInstance) stockChartInstance = echarts.init(document.getElementById('stock-chart'), 'dark');
        
        stockChartInstance.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', confine: true, formatter: p => `${p[0].name}<br/><b>${data.isKRW ? '₩'+Math.round(p[0].value).toLocaleString() : '$'+p[0].value.toFixed(2)}</b>` },
            grid: { left: '12%', right: '5%', bottom: '15%', top: '10%' },
            xAxis: { type: 'category', data: data.dates, axisLabel: { color: '#94a3b8', fontSize: 10 } },
            yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }, axisLabel: { color: '#94a3b8', fontSize: 10, formatter: v => data.isKRW ? (v/10000)+'만' : v } },
            dataZoom: [
                { type: 'inside', start: 80, end: 100 },
                { type: 'slider', show: true, bottom: 0, height: 15, borderColor: '#334155', textStyle: { color: '#94a3b8', fontSize: 9 } }
            ],
            series: [{ type: 'line', data: data.history, smooth: true, lineStyle: { color: color, width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: color }, { offset: 1, color: 'rgba(0,0,0,0)' }]) }, symbol: 'circle', symbolSize: 6, itemStyle: { color: color } }]
        });
        setTimeout(() => stockChartInstance.resize(), 100);
    }

    document.getElementById('close-modal').addEventListener('click', () => modal.classList.add('hidden'));
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });
    window.onresize = () => { chart.resize(); if (stockChartInstance && !modal.classList.contains('hidden')) stockChartInstance.resize(); };
</script>
</body>
</html>
"""

final_html = html_template.replace("__LIVE_DATA__", json.dumps(stock_data)) \
                          .replace("__TREE_DATA__", json.dumps(st.session_state.tree_data)) \
                          .replace("__UPDATE_TIME__", fetch_time) \
                          .replace("__SEARCH_QUERY__", json.dumps(search_query))

components.html(final_html, height=900)

if auto_refresh:
    time.sleep(10)
    st.rerun()
