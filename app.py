import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Z-score Fear & Greed", layout="centered")
st.title("📈 주식 시장 심리 분석기 (Z-score)")

@st.cache_data(ttl=3600)
def get_cnn_data():
    # CNN 서버를 속이기 위한 매우 상세한 브라우저 정보
    headers = {
        'authority': 'production.dataviz.cnn.io',
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'origin': 'https://www.cnn.com',
        'referer': 'https://www.cnn.com/markets/fear-and-greed',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    url = "https://production.dataviz.cnn.io/index/feargreed/static/data"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            # CNN 데이터 구조에 맞춰 추출
            s_raw = data['indicators']['stock_price_strength']['data']
            b_raw = data['indicators']['stock_price_breadth']['data']
            
            df_s = pd.DataFrame(s_raw).rename(columns={'x': 'date', 'y': 'strength'})
            df_b = pd.DataFrame(b_raw).rename(columns={'x': 'date', 'y': 'breadth'})
            
            # 날짜(ms)를 기준으로 병합
            df = pd.merge(df_s, df_b, on='date')
            df['date'] = pd.to_datetime(df['date'], unit='ms')
            return df.sort_values('date').tail(20)
        else:
            return None
    except Exception as e:
        return None

df_recent = get_cnn_data()

if df_recent is not None and not df_recent.empty:
    # 2단계: 표준화 (Z-score)
    df_recent['z_strength'] = (df_recent['strength'] - df_recent['strength'].mean()) / df_recent['strength'].std()
    df_recent['z_breadth'] = (df_recent['breadth'] - df_recent['breadth'].mean()) / df_recent['breadth'].std()

    # 3단계: 그래프 그리기
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # 사분면 배경
    ax.axvspan(-3, 0, 0.5, 1, alpha=0.1, color='orange') # 2사분면
    ax.axvspan(0, 3, 0.5, 1, alpha=0.1, color='green')  # 1사분면
    ax.axvspan(-3, 0, 0, 0.5, alpha=0.1, color='red')    # 3사분면
    ax.axvspan(0, 3, 0, 0.5, alpha=0.1, color='blue')   # 4사분면
    
    # 데이터 플로팅
    ax.scatter(df_recent['z_breadth'][:-1], df_recent['z_strength'][:-1], c='gray', alpha=0.4, label='Past Days')
    ax.scatter(df_recent['z_breadth'].iloc[-1], df_recent['z_strength'].iloc[-1], c='red', s=300, edgecolors='black', label='Today')
    
    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)
    ax.set_xlabel('Stock Price Breadth (Z-score)')
    ax.set_ylabel('Stock Price Strength (Z-score)')
    ax.legend()
    
    st.pyplot(fig)
    st.success(f"데이터 업데이트 완료: {df_recent['date'].iloc[-1].strftime('%Y-%m-%d')}")
else:
    st.error("현재 CNN 서버에서 데이터를 차단 중입니다. 1시간 뒤에 자동으로 다시 시도합니다.")
    st.info("Tip: 새로고침을 너무 자주 하면 접속이 차단될 수 있습니다.")
