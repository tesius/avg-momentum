import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Momentum Check",
    page_icon="📈",
    layout="wide"
)

# --- CSS 스타일링 ---
st.markdown("""
<style>
    /* 결과 박스 스타일 */
    div[data-testid="stMetric"] {
        background-color: #2D2E33;
        border: 1px solid #3c4043;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }
    div[data-testid="stMetricLabel"] { color: #9aa0a6 !important; }
    
    /* 제목 중앙 정렬 */
    h1 { text-align: center; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 타이틀 ---
st.title("Momentum Check")

# --- 레이아웃 ---
col_left, col_center, col_right = st.columns([1, 1.5, 1])

with col_center:
    # [핵심 변경 1] st.form으로 감싸기 (border=False로 투명하게)
    with st.form(key="search_form", border=False):
        
        # 컬럼 배치는 폼 안에서 수행
        c_input, c_btn = st.columns([3, 1], gap="small", vertical_alignment="bottom")
        
        with c_input:
            ticker_input = st.text_input("Ticker", value="SPY", label_visibility="collapsed").upper()
        
        with c_btn:
            # [핵심 변경 2] 일반 button 대신 form_submit_button 사용
            # 이제 엔터를 치거나 이 버튼을 누르면 submitted가 True가 됩니다.
            submitted = st.form_submit_button("GO", type="primary", use_container_width=True)

# --- 로직 ---
# submitted 변수가 True일 때 (엔터 or 클릭) 실행
if submitted and ticker_input:
    try:
        with st.spinner(f"Searching {ticker_input}..."):
            df = yf.download(ticker_input.strip(), period="2y", progress=False)
            
            if df.empty:
                st.error("데이터를 찾을 수 없습니다.")
            else:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                price_col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
                monthly_df = df[[price_col]].resample('ME').last()

                if len(monthly_df) < 13:
                    st.error("데이터 부족 (최소 13개월 필요)")
                else:
                    curr = float(monthly_df.iloc[-1].item())
                    p3 = float(monthly_df.iloc[-4].item())
                    p6 = float(monthly_df.iloc[-7].item())
                    p9 = float(monthly_df.iloc[-10].item())
                    p12 = float(monthly_df.iloc[-13].item())

                    m3 = (curr / p3) - 1
                    m6 = (curr / p6) - 1
                    m9 = (curr / p9) - 1
                    m12 = (curr / p12) - 1
                    avg_mom = (m3 + m6 + m9 + m12) / 4

                    # --- 결과 출력 ---
                    st.divider()
                    st.markdown(f"<h3 style='text-align: center;'>{ticker_input} Analysis Result</h3>", unsafe_allow_html=True)
                    st.write("")

                    m_left, m_center, m_right = st.columns([1, 1, 1])
                    with m_center:
                        st.metric("Avg Momentum Score", f"{avg_mom:.2%}", delta=f"{avg_mom:.2%}")

                    st.write("")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("3 Months", f"{m3:.2%}", delta=f"{m3:.2%}")
                    c2.metric("6 Months", f"{m6:.2%}", delta=f"{m6:.2%}")
                    c3.metric("9 Months", f"{m9:.2%}", delta=f"{m9:.2%}")
                    c4.metric("12 Months", f"{m12:.2%}", delta=f"{m12:.2%}")

                    # --- Altair 차트 ---
                    st.write("")
                    st.write("")
                    st.caption(f"📉 {ticker_input} 1 Year Trend")
                    
                    chart_df = df[[price_col]].tail(252).reset_index()
                    chart_df.columns = ['Date', 'Price']
                    
                    chart_color = "#4cd964" if avg_mom > 0 else "#ff3b30"
                    
                    chart = alt.Chart(chart_df).mark_line(color=chart_color, strokeWidth=2).encode(
                        x=alt.X('Date:T', axis=alt.Axis(format='%Y.%m', title=None, grid=False)),
                        y=alt.Y('Price:Q', scale=alt.Scale(zero=False), title=None),
                        tooltip=[
                            alt.Tooltip('Date', format='%Y-%m-%d', title='날짜'),
                            alt.Tooltip('Price', format=',.2f', title='가격')
                        ]
                    ).properties(
                        height=300
                    ).interactive()

                    st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        st.error(f"오류 발생: {e}")