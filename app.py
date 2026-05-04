import streamlit as st
import yfinance as yf
import json
import streamlit.components.v1 as components
from datetime import datetime, timezone, timedelta
import time

# 1. 앱 페이지 설정 (Pro 트레이더 터미널 스타일)
st.set_page_config(layout="wide", page_title="AI SECTOR TERMINAL", page_icon="📈")

# 블룸버그 터미널 스타일의 제목 (CSS로 감춤 처리 후 커스텀)
st.markdown("""
<style>
    div[data-testid="stAppViewBlockContainer"] { padding-top: 2rem; background-color: #000000; color: #00FF00; }
    h1 { color: #00FFCC !important; font-family: 'Courier New', Courier, monospace; font-size: 1.8rem !important; border-bottom: 1px solid #00FFCC; padding-bottom: 10px;}
    .stAlert { background-color: #111111; border: 1px solid #333333; color: #aaaaaa; }
</style>
""", unsafe_allow_html=True)

st.title("■ [PRO] AI SECTOR REAL-TIME TERMINAL")
st.info("SYS_MSG: 레이아웃 고정 완료. 화면 터치로 툴팁 확인 및 정밀 줌(1.1x)을 지원합니다.")

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
        "name": "[AI VALUE CHAIN]", "itemStyle": {"color": "#00FFCC"},
        "children": [
            {
                "name": "1. FOUNDATION", "itemStyle": {"color": "#00FFCC"},
                "children": [
                    {"originalName": "Google (Gemini)", "value": 1},
                    {"originalName": "OpenAI (ChatGPT)\n*Private", "value": 0},
                    {
                        "name": "AGENTIC AI", "itemStyle": {"color": "#00FFCC"},
                        "children": [
                            {"originalName": "Palantir (PLTR)", "value": 1},
                            {"originalName": "Salesforce (CRM)", "value": 1}
                        ]
                    }
                ]
            },
            {
                "name": "2. CLOUD INFRA", "itemStyle": {"color": "#00FFCC"},
                "children": [
                    {"originalName": "Microsoft (MSFT)", "value": 1},
                    {"originalName": "Amazon (AMZN)", "value": 1}
                ]
            },
            {
                "name": "3. HARDWARE", "itemStyle": {"color": "#00FFCC"},
                "children": [
                    {
                        "name": "AI ACCELERATOR", "itemStyle": {"color": "#00FFCC"},
                        "children": [
                            {"originalName": "NVIDIA (NVDA)", "value": 1},
                            {"originalName": "AMD (AMD)", "value": 1},
                            {"originalName": "Intel (INTC)", "value": 1}
                        ]
                    },
                    {
                        "name": "MEMORY/FOUNDRY", "itemStyle": {"color": "#00FFCC"},
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
                "name": "4. NETWORKING", "itemStyle": {"color": "#00FFCC"},
                "children": [
                    {
                        "name": "OPTICS/SWITCH", "itemStyle": {"color": "#00FFCC"},
                        "children": [
                            {"originalName": "Coherent (COHR)", "value": 1},
                            {"originalName": "Lumentum (LITE)", "value": 1},
                            {"originalName": "Arista (ANET)", "value": 1},
                            {"originalName": "Cisco (CSCO)", "value": 1}
                        ]
                    },
                    {
                        "name": "POWER/COOLING", "itemStyle": {"color": "#00FFCC"},
                        "children": [ {"originalName": "Vertiv (VRT)", "value": 1} ]
                    }
                ]
            },
            {
                "name": "5. ON-DEVICE", "itemStyle": {"color": "#00FFCC"},
                "children": [
                    {"originalName": "Apple (AAPL)", "value": 1},
                    {"originalName": "Qualcomm (QCOM)", "value": 1},
                    {"originalName": "ARM (ARM)", "value": 1}
                ]
            }
        ]
    }

# 사이드바 (Pro 스타일)
with st.sidebar:
    st.markdown("<h2 style='color:#00FFCC; font-family:monospace;'>⚙️ TERMINAL SETTINGS</h2>", unsafe_allow_html=True)
    auto_refresh = st.checkbox("🔄 AUTO REFRESH (10s)", value=False)
    if auto_refresh:
        st.success("STATUS: AUTO REFRESH ON")
    
    st.divider()

# 2. 데이터 수집 함수 (듀얼 엔진 장착)
@st.cache_data(ttl=60)
def get_market_data(tickers_dict):
    results = {}
    kst = timezone(timedelta(hours=9)) # 한국 시간(KST) 세팅
    fetch_time = datetime.now(kst).strftime('%H:%M:%S')
    
    mock_dates = [f"D-{i}" for i in range(120, 0, -1)] + ["Today"]
    mock_history = [100.0] * 121
    
    for name in tickers_dict.keys():
        results[name] = {
            "price": 100.0, "change": 0.0, "volume": 1000000, 
            "isKRW": False, "isMock": True, "dates": mock_dates, "history": mock_history
        }

    try:
        tickers_list = list(tickers_dict.values())
        
        # 1. 6개월치 일봉 데이터 수집 (한국 주식은 하루씩 지연될 수 있음)
        all_data = yf.download(tickers_list, period="6mo", interval="1d", group_by='ticker', auto_adjust=True, progress=False, timeout=10)
        
        # 2. 오늘자 실시간 분봉 데이터 수집 (지연 방어 및 현재가 확보용)
        try:
            live_data = yf.download(tickers_list, period="1d", interval="5m", group_by='ticker', auto_adjust=True, progress=False, timeout=10)
        except:
            live_data = pd.DataFrame()
            
        if not all_data.empty:
            for name, ticker in tickers_dict.items():
                try:
                    if len(tickers_list) > 1:
                        hist = all_data[ticker].dropna()
                    else:
                        hist = all_data.dropna()
                    
                    if len(hist) >= 1:
                        dates = [d.strftime('%m-%d') for d in hist.index]
                        prices = [float(p) for p in hist['Close']]
                        volume = float(hist['Volume'].iloc[-1])
                        
                        # [핵심] 실시간 데이터 병합 로직
                        if not live_data.empty:
                            if len(tickers_list) > 1:
                                l_hist = live_data[ticker].dropna()
                            else:
                                l_hist = live_data.dropna()
                                
                            if not l_hist.empty:
                                live_price = float(l_hist['Close'].iloc[-1])
                                today_str = datetime.now(kst).strftime('%m-%d')
                                
                                # 일봉의 마지막 날짜가 오늘(KST)이 아니라면? -> 실시간 가격을 오늘 날짜로 강제 추가!
                                if dates[-1] != today_str:
                                    dates.append(f"{today_str} (Live)")
                                    prices.append(live_price)
                                else:
                                    # 이미 오늘 날짜가 있다면 실시간 가격으로 덮어쓰기
                                    dates[-1] = f"{today_str} (Live)"
                                    prices[-1] = live_price

                        current = prices[-1]
                        prev = prices[-2] if len(prices) > 1 else current
                        change = ((current - prev) / prev) * 100 if prev != 0 else 0.0
                        
                        results[name] = {
                            "price": current, "change": change, 
                            "volume": volume, "isKRW": ".KS" in ticker or ".KQ" in ticker,
                            "isMock": False, "dates": dates, "history": prices
                        }
                except Exception as e:
                    continue
    except Exception as e:
        pass
        
    return results, fetch_time

# 데이터 불러오기
with st.spinner('CONNECTING TO MARKET DATA... (DUAL ENGINE)'):
    stock_data, fetch_time = get_market_data(st.session_state.tickers_map)

# 3. 시각화 HTML/JS 템플릿 (Pro HTS/Bloomberg 스타일 & 둥둥 떠다니기 완전 고정)
html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <style>
        /* 터미널 스타일 CSS */
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        
        body { margin: 0; padding: 0; background-color: #030303; overflow: hidden; touch-action: none; font-family: 'Share Tech Mono', monospace; }
        #chart { width: 100vw; height: 90vh; background: radial-gradient(circle at center, #0a1118 0%, #000000 100%); } 
        
        /* 격자 무늬 배경 (Pro 스타일) */
        body::before {
            content: ""; position: absolute; top: 0; left: 0; width: 100vw; height: 100vh;
            background-image: linear-gradient(rgba(0, 255, 204, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 204, 0.05) 1px, transparent 1px);
            background-size: 40px 40px; pointer-events: none; z-index: 1;
        }

        .controls { position: absolute; top: 15px; left: 15px; right: 15px; z-index: 10; display: flex; flex-wrap: wrap; gap: 8px; }
        
        .btn-pro { 
            background: #000; border: 1px solid #00FFCC; color: #00FFCC; 
            padding: 8px 12px; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
            box-shadow: 0 0 5px rgba(0,255,204,0.3); flex-grow: 1; text-align: center;
        }
        .btn-pro:active { background: #00FFCC; color: #000; }
        
        .btn-alert { border-color: #FF3366; color: #FF3366; box-shadow: 0 0 5px rgba(255,51,102,0.3); }
        .btn-alert:active { background: #FF3366; color: #000; }

        .update-time { 
            position: absolute; bottom: 15px; right: 15px; z-index: 10; 
            color: #00FFCC; font-size: 12px; background: #000; 
            padding: 6px 12px; border: 1px solid #00FFCC; box-shadow: 0 0 8px rgba(0,255,204,0.4); 
        }

        /* 모달 스타일 (트레이딩 팝업) */
        #chart-modal .modal-content {
            background: #050505; border: 1px solid #00FFCC; box-shadow: 0 0 20px rgba(0,255,204,0.2);
            border-radius: 0; /* 네모 반듯한 디자인 */
            max-height: 90vh; overflow-y: auto;
        }
        .modal-header { border-bottom: 1px dashed #333; padding-bottom: 10px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="controls" style="z-index: 20;">
        <button id="centerGraph" class="btn-pro">▣ RE-CENTER GRAPH</button>
        <button id="resetPos" class="btn-pro btn-alert">⚠️ RESET LAYOUT</button>
    </div>
    
    <div class="update-time" id="update-time-display">SYS_TIME: 연동 중...</div>
    
    <div id="chart" style="z-index: 5;"></div>

    <div id="chart-modal" class="fixed inset-0 bg-black/95 z-50 hidden flex items-center justify-center p-4 transition-opacity">
        <div class="modal-content p-4 w-full max-w-md relative">
            <button id="close-modal" class="absolute top-2 right-2 p-1 text-[#00FFCC] hover:text-white transition-colors">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
            <div class="modal-header mt-2">
                <h2 id="modal-title" class="text-xl text-white mb-1 tracking-wider">TICKER</h2>
                <p id="modal-price" class="text-2xl font-bold">PRICE</p>
            </div>
            <div id="stock-chart" style="width: 100%; height: 250px;"></div>
            <p class="text-[10px] text-[#555] mt-2 text-right font-mono">DATA RANGE: 6M | SOURCE: YFINANCE</p>
        </div>
    </div>

<script>
    const liveData = __LIVE_DATA__;
    const treeData = __TREE_DATA__;
    const chart = echarts.init(document.getElementById('chart'), 'dark');
    const savedPos = JSON.parse(localStorage.getItem('ai_ecosystem_nodes_pro')) || {};

    document.getElementById('update-time-display').innerText = 'SYS_TIME: __UPDATE_TIME__ (KST)';

    function process(node) {
        node.id = node.originalName || node.name;
        if (node.value !== undefined && node.value !== 0 && liveData[node.originalName]) {
            const d = liveData[node.originalName];
            node.rawData = d; 
            node.value = d.price; 
            
            node.symbolSize = Math.max(25, Math.min(60, 20 + (d.volume / 2500000))); 
            
            // HTS 트레이더 색상 (형광초록 상승, 형광빨강 하락)
            let color = '#777777';
            let pStr = d.isKRW ? '₩' + Math.round(d.price).toLocaleString() : '$' + d.price.toFixed(2);
            let cStr = '\\n[ 0.00% ]';
            
            if (d.change > 0) { color = '#00FF00'; cStr = '\\n[▲ ' + d.change.toFixed(2) + '%]'; }
            else if (d.change < 0) { color = '#FF003C'; cStr = '\\n[▼ ' + Math.abs(d.change).toFixed(2) + '%]'; }
            
            node.name = node.originalName.split(' ')[0] + '\\n' + pStr + cStr; // 이름 간소화
            
            // HTS 스타일 속이 빈 빛나는 원형
            node.itemStyle = { 
                color: '#000000', // 속은 까맣게
                borderColor: color, 
                borderWidth: 2,
                shadowBlur: 10,
                shadowColor: color
            };
            node.label = { color: color, textShadowBlur: 5, textShadowColor: '#000' };
        } else { 
            node.symbolSize = node.children ? 16 : 10; 
            node.itemStyle = { color: '#00FFCC', borderColor: '#00FFCC', shadowBlur: 10, shadowColor: '#00FFCC' };
            node.label = { color: '#00FFCC' };
        }
        if (node.children) node.children.forEach(process);
    }
    process(treeData);

    const customTooltip = {
        trigger: 'item', backgroundColor: 'rgba(0, 0, 0, 0.9)', borderColor: '#00FFCC', borderWidth: 1, 
        textStyle: { color: '#fff', fontSize: 12, fontFamily: 'monospace' },
        confine: true, 
        formatter: function (info) {
            if (!info.data || !info.data.rawData) return `<span style="color:#00FFCC">DIR: ${info.name.replace(/\\n/g, ' ')}</span>`;
            const d = info.data.rawData;
            let title = info.data.originalName.split('\\n')[0];
            let pStr = d.isKRW ? '₩' + Math.round(d.price).toLocaleString() : '$' + d.price.toFixed(2);
            let cStr = d.change > 0 ? '+'+d.change.toFixed(2)+'%' : (d.change < 0 ? d.change.toFixed(2)+'%' : '0.00%');
            let color = d.change > 0 ? '#00FF00' : (d.change < 0 ? '#FF003C' : '#777777');
            return `
                <div style="border-bottom: 1px solid #333; padding-bottom: 4px; margin-bottom: 4px; font-weight:bold;">${title}</div>
                <div style="color: ${color}; font-size: 16px; font-weight: bold;">${pStr}</div>
                <div style="color: ${color}; font-size: 12px;">CHG: ${cStr}</div>
                <div style="font-size: 9px; color: #555; margin-top: 6px;">[TAP TO VIEW CHART]</div>
            `;
        }
    };

    let gNodes = [], gLinks = [];
    function parseGraph(node, pId) {
        let nData = { 
            id: node.id, name: node.name, originalName: node.originalName || node.name, 
            symbolSize: node.symbolSize * 1.3, itemStyle: node.itemStyle, label: node.label,
            value: node.value, rawData: node.rawData 
        };
        
        if (savedPos[node.id]) {
            nData.x = savedPos[node.id].x;
            nData.y = savedPos[node.id].y;
            nData.fixed = true; 
        }

        gNodes.push(nData);
        if (pId) gLinks.push({ source: pId, target: node.id, lineStyle: { width: 1, color: '#334155', curveness: 0.1 } });
        if (node.children) node.children.forEach(c => parseGraph(c, node.id));
    }
    parseGraph(treeData, null);

    const graphOpt = {
        tooltip: customTooltip,
        series: [{
            type: 'graph', layout: 'force', data: gNodes, links: gLinks, roam: true, draggable: true,
            scaleLimit: { min: 0.1, max: 20 },
            // 🚨 원들 둥둥 떠다니기 완전 금지 (layoutAnimation: false)
            force: { repulsion: 3500, edgeLength: [60, 180], gravity: 0.05, layoutAnimation: false }, 
            label: { show: true, position: 'bottom', fontSize: 10, fontFamily: 'monospace', formatter: p => p.data.originalName.split(' ')[0], color: '#fff' },
            zoom: 1
        }]
    };

    chart.setOption(graphOpt);

    function savePositions() {
        const layoutData = chart.getModel().getSeriesByIndex(0).getData();
        const posMap = JSON.parse(localStorage.getItem('ai_ecosystem_nodes_pro')) || {};
        gNodes.forEach((n, i) => {
            const layout = layoutData.getItemLayout(i);
            if (layout && !isNaN(layout[0])) posMap[n.id] = { x: layout[0], y: layout[1] };
        });
        localStorage.setItem('ai_ecosystem_nodes_pro', JSON.stringify(posMap));
    }

    chart.on('mouseup', function() { savePositions(); });

    // 중앙 정렬 버튼 (Pro 스타일)
    document.getElementById('centerGraph').onclick = () => {
        chart.setOption({ series: [{ center: null, zoom: 1 }] });
    };
    
    // 배치 초기화 버튼
    document.getElementById('resetPos').onclick = () => { localStorage.removeItem('ai_ecosystem_nodes_pro'); location.reload(); };

    const modal = document.getElementById('chart-modal');
    let stockChartInstance = null;

    chart.on('click', function(params) {
        if (params.data && params.data.rawData) openModal(params.data.rawData, params.data.originalName.split('\\n')[0], params.data.itemStyle.borderColor);
    });

    function openModal(data, title, color) {
        modal.classList.remove('hidden');
        document.getElementById('modal-title').innerText = "> " + title.toUpperCase();
        let pStr = data.isKRW ? '₩' + Math.round(data.price).toLocaleString() : '$' + data.price.toFixed(2);
        let cStr = data.change > 0 ? '▲ ' + data.change.toFixed(2) + '%' : (data.change < 0 ? '▼ ' + Math.abs(data.change).toFixed(2) + '%' : '0.00%');
        document.getElementById('modal-price').innerText = pStr + " [" + cStr + "]";
        document.getElementById('modal-price').style.color = color;

        if (!stockChartInstance) stockChartInstance = echarts.init(document.getElementById('stock-chart'), 'dark');
        
        // 차트 디자인도 날카로운 스텝라인(TradingView) 스타일로 변경
        stockChartInstance.setOption({
            backgroundColor: 'transparent',
            tooltip: { trigger: 'axis', confine: true, backgroundColor: '#000', borderColor: color, textStyle: { fontFamily: 'monospace' }, formatter: p => `DATE: ${p[0].name}<br/>PRC: <b style="color:${color}">${data.isKRW ? '₩'+Math.round(p[0].value).toLocaleString() : '$'+p[0].value.toFixed(2)}</b>` },
            grid: { left: '15%', right: '5%', bottom: '15%', top: '10%' },
            xAxis: { type: 'category', data: data.dates, axisLabel: { color: '#666', fontFamily: 'monospace', fontSize: 10 }, axisLine: { lineStyle: { color: '#333' } } },
            yAxis: { type: 'value', scale: true, splitLine: { lineStyle: { color: '#222', type: 'dashed' } }, axisLabel: { color: '#666', fontFamily: 'monospace', fontSize: 10, formatter: v => data.isKRW ? (v/10000)+'만' : v } },
            dataZoom: [
                { type: 'inside', start: 80, end: 100 },
                { type: 'slider', show: true, bottom: 0, height: 15, borderColor: '#222', textStyle: { color: '#666' }, fillerColor: 'rgba(0,255,204,0.1)' }
            ],
            series: [{ type: 'line', data: data.history, smooth: false, step: 'end', lineStyle: { color: color, width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: color }, { offset: 1, color: 'transparent' }]) }, symbol: 'none', itemStyle: { color: color } }]
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

components.html(html_template.replace("__LIVE_DATA__", json.dumps(stock_data)).replace("__TREE_DATA__", json.dumps(st.session_state.tree_data)).replace("__UPDATE_TIME__", fetch_time), height=900)

if auto_refresh:
    time.sleep(10)
    st.rerun()
