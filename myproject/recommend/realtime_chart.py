import time
import pandas as pd
import streamlit as st
from kis import get_stock_price  # ← 네가 만든 kis.py 함수 그대로 import 

st.set_page_config(
    page_title="실시간 주가 차트",
    layout="wide"
)

st.title("📈 삼성전자 실시간 차트 (2초마다 업데이트)")

chart_placeholder = st.empty()

prices = []

while True:
    data = get_stock_price("삼성전자")   # ← 한글 입력도 지원됨
    if not data["error"]:
        now_price = int(data["price"])
        timestamp = pd.Timestamp.now()

        prices.append({"time": timestamp, "price": now_price})

        df = pd.DataFrame(prices)

        chart_placeholder.line_chart(
            df.rename(columns={"time": "index"}).set_index("index")
        )

    time.sleep(2)   # 2초마다 업데이트
