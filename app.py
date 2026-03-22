import os
import streamlit as st
from dotenv import load_dotenv
from anthropic import Anthropic
import yfinance as yf

load_dotenv()

# =========================
# 🔹 설정
# =========================
api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key)
model = "claude-sonnet-4-6"

TICKER_MAP = {
    "테슬라": "TSLA",
    "애플": "AAPL",
    "엔비디아": "NVDA",
    "마이크로소프트": "MSFT",
    "삼성전자": "005930.KS",
}

# =========================
# 🔹 데이터
# =========================
def get_stock_data(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="5d")

    if data.empty:
        return None

    latest = data.iloc[-1]
    prev = data.iloc[-2]

    price = round(float(latest["Close"]), 2)
    change = round(float(latest["Close"] - prev["Close"]), 2)
    change_pct = round((change / prev["Close"]) * 100, 2)

    return price, change, change_pct


def get_stock_news(symbol):
    ticker = yf.Ticker(symbol)
    try:
        news = ticker.news[:3]
        return [n["title"] for n in news]
    except:
        return []


def get_stock_chart(symbol, period):
    ticker = yf.Ticker(symbol)
    return ticker.history(period=period)


# =========================
# 🔹 점수 시스템
# =========================
def calculate_score(change_pct, news_list):
    score = 50

    if change_pct > 2:
        score += 15
    elif change_pct > 0:
        score += 10
    elif change_pct < -2:
        score -= 15
    else:
        score -= 5

    positive = ["상승", "호재", "성장", "AI"]
    negative = ["하락", "악재", "규제"]

    for news in news_list:
        for p in positive:
            if p in news:
                score += 5
        for n in negative:
            if n in news:
                score -= 5

    return max(0, min(100, score))


def ask_claude(prompt):
    res = client.messages.create(
        model=model,
        max_tokens=800,
        temperature=0.4,
        messages=[{"role": "user", "content": prompt}],
    )
    return res.content[0].text


# =========================
# 🔹 UI
# =========================
st.set_page_config(page_title="투자 AI", layout="wide")

st.title("📈 투자 분석 AI")
st.caption("뉴스 + 점수 + 차트 기반 분석")

stock_name = st.text_input("종목 입력 (예: 테슬라)")

period = st.selectbox(
    "📊 차트 기간",
    ["5d", "1mo", "3mo", "6mo", "1y"]
)

if st.button("분석하기"):

    if stock_name not in TICKER_MAP:
        st.error("❌ 지원하지 않는 종목")
    else:
        symbol = TICKER_MAP[stock_name]

        data = get_stock_data(symbol)

        if data is None:
            st.error("데이터 없음")
        else:
            price, change, change_pct = data
            news_list = get_stock_news(symbol)
            score = calculate_score(change_pct, news_list)

            news_text = "\n".join(news_list) if news_list else "뉴스 없음"

            prompt = f"""
            {stock_name}({symbol})
            가격: {price}
            변동: {change} ({change_pct}%)
            점수: {score}/100

            뉴스:
            {news_text}

            투자 판단 내려줘
            """

            with st.spinner("AI 분석 중..."):
                answer = ask_claude(prompt)

            # =========================
            # 🔥 UI 출력
            # =========================
            st.divider()

            # 📊 지표
            col1, col2, col3 = st.columns(3)
            col1.metric("현재가", price)
            col2.metric("변동", change, f"{change_pct}%")
            col3.metric("점수", f"{score}/100")

            # 📈 점수 바
            st.progress(score / 100)

            # 📈 차트
            st.subheader("📈 주가 차트")
            chart_data = get_stock_chart(symbol, period)

            if not chart_data.empty:
                st.line_chart(chart_data["Close"])
            else:
                st.warning("차트 데이터 없음")

            # 🎯 판단
            st.subheader("🎯 최종 판단")
            if score >= 70:
                st.success("✅ 매수 유리")
            elif score >= 50:
                st.warning("⚠️ 관망 추천")
            else:
                st.error("❌ 매수 비추천")

            # 🧠 AI 분석
            st.subheader("🧠 AI 분석")
            st.write(answer)

            # 📌 체크포인트
            st.subheader("📌 핵심 체크포인트")
            st.info("""
- 점수 50 이상 유지 여부  
- 거래량 동반 상승 여부  
- 시장 흐름 확인  
- 뉴스 모멘텀 지속 여부  
""")

            # 📰 뉴스
            st.subheader("📰 뉴스")
            for n in news_list:
                st.markdown(f"- {n}")