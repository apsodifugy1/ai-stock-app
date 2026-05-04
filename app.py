import streamlit as st
import yfinance as yf
import json
import streamlit.components.v1 as components
from datetime import datetime
import time

# 1. 앱 페이지 설정 (모바일 최적화)
st.set_page_config(layout="wide", page_title="AI 실시간 생태계 맵", page_icon="📱")

st.title("📱 AI 산업 실시간 주가 대시보드 (모바일 버전)")
st.info("왼쪽 위 '〉' 버튼을 눌러 메뉴를 열고, 두 손가락으로 줌인/줌아웃 하세요.")

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

# 트리 노드 재귀 탐색 함수
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

# 모바일 호환 사이드바 UI
with st.sidebar:
    st.header("⚙️ 모바일 모니터링 설정")
    auto_refresh = st.checkbox("🔄 10초마다 자동 새로고침", value=False)
    if auto_refresh:
        st.success("자동 새로고침 켜짐")
    
    st.divider()
    
    st.header("➕ 항목 추가")
    all_nodes = []
    get_all_node_names(st.session_state.tree_data, all_nodes)
    parent_node_name = st.selectbox("어느 항목 아래에?", all_nodes)
    
    new_node_name = st.text_input("새 항목 이름", placeholder="예: Tesla")
    new_ticker = st.text_input("티커 (옵션)", placeholder="예: TSLA")
    
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

# 2. 데이터 수집 함수 (6개월 데이터)
# 야후 파이낸스 Rate Limit 방지를 위해 실제 데이터 통신 주기는 60초로 상향 조정합니다.
@st.cache_data(ttl=60)
def get_market_data(tickers_dict):
    results = {}
    fetch_time = datetime.now().strftime('%H:%M:%S')
    
    mock_dates = [f"D-{i}" for i in range(120, 0, -1)] + ["Today"]
    mock_history = [100.0] * 121
    
    for name in tickers_dict.keys():
        results[name] = {
            "price": 100.0, "
