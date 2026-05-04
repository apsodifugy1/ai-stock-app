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

# CSS 커스텀: 경고창 및 기본 UI 정돈
st.markdown("""
    <style>
    .stAlert { background-color: #1e293b; border: 1px solid #334155; color: #f8fafc; }
    div[data-testid="stSidebar"] { background-color: #0f172a; }
    </style>
""", unsafe_allow_html=True)

st.title("📱 AI 산업 실시간 주가 대시보드 (Galaxy S26 Ultra 최적화)")
st.info("SYS_MSG: 시스템 엔진 업데이트 완료. 최신 버전(v2.5)이 구동 중입니다.")

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

# 트리 노드 관련 유틸리티
def get_all_node_names(node, names_list):
    name = node.get("originalName", node.get("name", ""))
    display_name = name.split('\n')[0]
    names_list.append(display_name)
    for child in node.get("children", []):
        get_all_node_names(child, names_list)

def add_child_to_node(node, parent_display_name, new_child):
    current_name = node.get("originalName", node.get("name", "")).split('\n')[0]
    if current_name == parent_display_name:
        if "children" not in node: node["children"] = []
        node["children"].append(new_child)
        return True
    for child in node.get("children", []):
        if add_child_to_node(child, parent_display_name, new_child): return True
    return False

# 사이드바 (티커 검색 엔진 강화 버전)
with st.sidebar:
    st.header("⚙️ 터미널 모니터링 설정")
    auto_refresh = st.checkbox("🔄 자동 새로고침 (10s)", value=False)
    st.divider()
    
    st.header("➕ 새 항목 추가")
    all_nodes = []
    get_all_node_names(st.session_state.tree_data, all_nodes)
    parent_node_name = st.selectbox("상위 항목 선택", all_nodes)
    
    if 'found_ticker' not in st.session_state:
        st.session_state.found_ticker = ""

    new_node_name = st.text_input("기업명 또는 그룹명", placeholder="예: Tesla, 삼성전자")
    
    col1, col2 = st.columns([6, 4])
    with col1:
        ticker_input = st.text_input("주식 티커", value=st.session_state.found_ticker, placeholder="티커 찾기 버튼 클릭")
    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔍 티커 찾기", use_container_width=True):
            if new_node_name:
                try:
                    # 야후 파이낸스 검색 API - 강력한 헤더 포함
                    encoded_query = urllib.parse.quote(new_node_name)
                    search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={encoded_query}&quotesCount=5"
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                    }
                    req = urllib.request.Request(search_url, headers=headers)
                    
                    with urllib.request.urlopen(req, timeout=5) as response:
                        search_data = json.loads(response.read().decode('utf-8'))
                        if search_data.get('quotes') and len(search_data['quotes']) > 0:
                            # 가장 적절한 티커 선정 (주식 우선)
                            best_match = search_data['quotes'][0]['symbol']
                            for quote in search_data['quotes']:
                                if quote.get('quoteType') == 'EQUITY':
                                    best_match = quote['symbol']
                                    break
                            st.session_state.found_ticker = best_match
                            st.rerun()
                        else:
                            st.warning("티커를 찾지 못했습니다.")
                except Exception:
                    st.error("검색 서버 오류. 직접 입력하세요.")
            else:
                st.warning("이름을 먼저 입력하세요.")

    if st.button("🚀 생태계 지도에 추가", use_container_width=True):
        if new_node_name:
            final_ticker = ticker_input.strip()
            is_company = bool(final_ticker)
            new_child = {"originalName": new_node_name, "name": new_node_name, "value": 1 if is_company else 0}
            if not is_company: new_child["itemStyle"] = {"color": "#8b5cf6"}
            
            success = add_child_to_node(st.session_state.tree_data, parent_node_name, new_child)
            if success and is_company: 
                st.session_state.tickers_map[new_node_name] = final_ticker.upper()
            
            if success:
                st.session_state.found_ticker = "" # 초기화
                st.success(f"'{new_node_name}' 등록 완료")
                st.rerun()

# 2. 데이터 수집 함수 (1분봉 스나이퍼 엔진)
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
                    dates = [f"{today_str} (Live
