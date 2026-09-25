import datetime
import pandas as pd
import plotly.graph_objects as plotly_go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

# 1. 모바일 맞춤 페이지 기본 설정
st.set_page_config(
    page_title="글로벌 원자재 & 배터리/메모리 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed", # 모바일에서 차트를 먼저 보여주기 위해 사이드바 접음
)

st.title("📊 글로벌 원자재 · 배터리/메모리 대시보드")
st.caption("💡 화면 왼쪽 상단의 **`>`** 버튼을 터치하면 종목 및 섹터를 변경할 수 있습니다.")

# 2. 벤치마크 데이터 수집
@st.cache_data(ttl=14400)
def load_daily_market_benchmarks():
    try:
        start_date = "2014-01-01"
        end_date = datetime.date.today().strftime("%Y-%m-%d")

        lit_data = yf.download("LIT", start=start_date, end=end_date, progress=False)
        soxx_data = yf.download("SOXX", start=start_date, end=end_date, progress=False)

        if isinstance(lit_data.columns, pd.MultiIndex):
            lit_close = lit_data["Close"].iloc[:, 0]
        else:
            lit_close = lit_data["Close"]

        if isinstance(soxx_data.columns, pd.MultiIndex):
            soxx_close = soxx_data["Close"].iloc[:, 0]
        else:
            soxx_close = soxx_data["Close"]

        df = pd.DataFrame(
            {
                "Lithium_Index": lit_close,
                "Memory_Semi_Index": soxx_close,
            }
        ).dropna()

        df = df.resample("D").ffill().bfill()
        return df

    except Exception as ex:
        st.error(f"벤치마크 데이터 수집 실패: {ex}")
        return pd.DataFrame()

# 3. 주가 및 ETF 수집 함수
@st.cache_data(ttl=14400)
def load_daily_stock_data(ticker_symbol):
    try:
        start_date = "2014-01-01"
        data = yf.download(
            ticker_symbol, start=start_date, end=datetime.date.today(), progress=False
        )
        if data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            data = data["Close"]
        else:
            data = data[["Close"]]
        return data
    except Exception as ex:
        st.error(f"주가 수집 실패 ({ticker_symbol}): {ex}")
        return pd.DataFrame()

market_df = load_daily_market_benchmarks()

# ---------------------------------------------------------
# ⚙️ 사이드바 컨트롤러 (종목 선택)
# ---------------------------------------------------------
st.sidebar.header("⚙️ 대시보드 컨트롤러")

sector = st.sidebar.radio(
    "분석할 섹터를 선택하세요",
    ["2차전지 · 전고체배터리 · 원자재", "메모리 반도체 · AI 소부장"],
)

if sector == "2차전지 · 전고체배터리 · 원자재":
    stock_options = {
        "--- [전고체 배터리 & 셀 메이커] ---": None,
        "삼성SDI [전고체배터리] (006400.KS)": "006400.KS",
        "LG에너지솔루션 (373220.KS)": "373220.KS",
        "SK이노베이션 (096770.KS)": "096770.KS",
        "--- [원자재 Top 10 & 주요 소재] ---": None,
        "POSCO홀딩스 [리튬/니켈] (005490.KS)": "005490.KS",
        "고려아연 [비철금속 Top] (010130.KS)": "010130.KS",
        "포스코퓨처엠 (003670.KS)": "003670.KS",
        "에코프로 (086520.KQ)": "086520.KQ",
        "에코프로비엠 (247540.KQ)": "247540.KQ",
        "앨버말 / Albemarle [글로벌 리튬1위] (ALB)": "ALB",
        "SQM [글로벌 리튬] (SQM)": "SQM",
        "--- [전고체 & 원자재 ETF] ---": None,
        "KODEX 차세대배터리 [전고체/소재] (305720.KS)": "305720.KS",
        "TIGER 2차전지테마 (305540.KS)": "305540.KS",
        "SOL 2차전지소재Fn (462330.KS)": "462330.KS",
        "TIGER 금속선물Enhanced [원자재] (139320.KS)": "139320.KS",
        "Global X Lithium & Battery ETF (LIT)": "LIT",
        "Amplify Lithium & Battery ETF (BATT)": "BATT",
    }
    commodity_col = "Lithium_Index"
    commodity_label = "글로벌 리튬/배터리 지수 (LIT)"

else:
    stock_options = {
        "--- [국내 대표 반도체] ---": None,
        "삼성전자 (005930.KS)": "005930.KS",
        "SK하이닉스 (000660.KS)": "000660.KS",
        "--- [글로벌 메이커 & 장비] ---": None,
        "마이크론 (MU)": "MU",
        "엔비디아 (NVDA)": "NVDA",
        "ASML (ASML)": "ASML",
        "--- [국내 소부장/HBM 관련] ---": None,
        "한미반도체 (042700.KS)": "042700.KS",
        "ISC (095340.KQ)": "095340.KQ",
        "HPSP (403870.KQ)": "403870.KQ",
        "--- [국내외 대표 반도체 ETF] ---": None,
        "TIGER 반도체 ETF (091230.KS)": "091230.KS",
        "KODEX 반도체 ETF (091160.KS)": "091160.KS",
        "iShares Semiconductor ETF (SOXX)": "SOXX",
        "VanEck Semiconductor ETF (SMH)": "SMH",
    }
    commodity_col = "Memory_Semi_Index"
    commodity_label = "글로벌 반도체 업황 지수 (SOXX)"

valid_keys = [k for k, v in stock_options.items() if v is not None]
selected_stock_label = st.sidebar.selectbox("연동할 종목 또는 ETF", valid_keys)
selected_ticker = stock_options[selected_stock_label]

stock_df = load_daily_stock_data(selected_ticker)

# ---------------------------------------------------------
# 📅 [모바일 최적화] 터치 스크롤형 기간 선택 UI (st.pills)
# ---------------------------------------------------------
st.markdown("#### 📅 기간 선택")
periods = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "4Y", "5Y", "10Y", "ALL"]

# 모바일에서 좌우 스크롤로 가볍게 터치 선택 가능한 pills 컨트롤 사용
period_choice = st.pills(
    "기간",
    options=periods,
    default="1Y",
    label_visibility="collapsed"
)

if not period_choice:
    period_choice = "1Y"

max_date = market_df.index.max().date()

if period_choice == "1M":
    init_start = max_date - datetime.timedelta(days=30)
elif period_choice == "3M":
    init_start = max_date - datetime.timedelta(days=90)
elif period_choice == "6M":
    init_start = max_date - datetime.timedelta(days=180)
elif period_choice == "1Y":
    init_start = max_date - datetime.timedelta(days=365)
elif period_choice == "2Y":
    init_start = max_date - datetime.timedelta(days=365 * 2)
elif period_choice == "3Y":
    init_start = max_date - datetime.timedelta(days=365 * 3)
elif period_choice == "4Y":
    init_start = max_date - datetime.timedelta(days=365 * 4)
elif period_choice == "5Y":
    init_start = max_date - datetime.timedelta(days=365 * 5)
elif period_choice == "10Y":
    init_start = max_date - datetime.timedelta(days=365 * 10)
else:
    init_start = market_df.index.min().date()

# ---------------------------------------------------------
# 📌 기간 맞춤 정합성(%) 및 데이터 계산
# ---------------------------------------------------------
filtered_market = market_df.loc[market_df.index.date >= init_start]
filtered_stock = (
    stock_df.loc[stock_df.index.date >= init_start] if not stock_df.empty else pd.DataFrame()
)

match_rate = 0.0
corr_val = 0.0

if not filtered_market.empty and not filtered_stock.empty:
    merged = pd.merge(
        filtered_market[[commodity_col]],
        filtered_stock,
        left_index=True,
        right_index=True,
    ).dropna()

    if len(merged) > 1:
        corr_val = merged.iloc[:, 0].corr(merged.iloc[:, 1])
        match_rate = (corr_val**2) * 100

# ---------------------------------------------------------
# 📱 [모바일 최적화] 핵심 지표 카드 및 정합성 강조 배지
# ---------------------------------------------------------
# 모바일 세로 화면을 위해 정합성 지표를 맨 위 상단에 강조 배너로 표시
st.info(
    f"🔥 **{period_choice} 정합성 비율: {match_rate:.1f}%** (상관계수 r = {corr_val:.2f})"
)

# 모바일 화면 너비 고려하여 세로 배치로 깔끔히 정렬
if not filtered_market.empty:
    raw_start = filtered_market[commodity_col].iloc[0]
    raw_end = filtered_market[commodity_col].iloc[-1]
    raw_chg = ((raw_end - raw_start) / raw_start) * 100

    st.metric(
        "원자재/업황 지수",
        f"${raw_end:.2f}",
        f"{raw_chg:+.2f}% ({period_choice})",
    )

if not filtered_stock.empty:
    st_start = float(filtered_stock.iloc[0].values[0])
    st_end = float(filtered_stock.iloc[-1].values[0])
    st_chg = ((st_end - st_start) / st_start) * 100

    unit = "원" if ".KS" in selected_ticker or ".KQ" in selected_ticker else "$"
    fmt = f"{st_end:,.0f}{unit}" if unit == "원" else f"${st_end:,.2f}"

    st.metric(
        f"{selected_stock_label.split(' ')[0]} 종가",
        fmt,
        f"{st_chg:+.2f}% ({period_choice})",
    )

st.markdown("---")

# ---------------------------------------------------------
# 📈 [모바일 최적화] 차트 렌더링
# ---------------------------------------------------------
stock_short_name = selected_stock_label.split(" ")[0]

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    plotly_go.Scatter(
        x=filtered_market.index,
        y=filtered_market[commodity_col],
        name=commodity_label,
        line=dict(color="#0068c9", width=2),
    ),
    secondary_y=False,
)

if not filtered_stock.empty:
    fig.add_trace(
        plotly_go.Scatter(
            x=filtered_stock.index,
            y=filtered_stock.iloc[:, 0],
            name=f"{stock_short_name}",
            line=dict(color="#ff2b2b", width=2),
        ),
        secondary_y=True,
    )

fig.update_layout(
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        font=dict(size=10) # 모바일용 범례 글자 크기 축소
    ),
    template="plotly_white",
    height=480, # 모바일 한 화면에 쏙 들어오도록 높이 조절
    margin=dict(l=10, r=10, t=30, b=20), # 여백 최소화
    xaxis=dict(type="date", fixedrange=True), # 스크롤 간섭 방지
    yaxis=dict(fixedrange=True),
    yaxis2=dict(fixedrange=True),
)

fig.update_yaxes(title_text=f"<b>{commodity_label}</b>", secondary_y=False)
fig.update_yaxes(title_text=f"<b>{stock_short_name}</b>", secondary_y=True)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------
# 📄 데이터표
# ---------------------------------------------------------
with st.expander("📄 선택 기간 일별 데이터표 조회"):
    st.dataframe(filtered_market.sort_index(ascending=False), use_container_width=True)
