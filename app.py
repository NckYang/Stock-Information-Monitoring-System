import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import plotly.graph_objects as go
import os

# ----------------------------
# 基本設定與狀態初始化
# ----------------------------
st.set_page_config(page_title="股市監測儀表板", layout="wide")

# 初始化 session_state 用來儲存使用者設定的警報
if "price_alerts" not in st.session_state:
    st.session_state.price_alerts = {}

# 初始化 session_state 用來儲存歷史監控清單
if "monitor_list" not in st.session_state:
    st.session_state.monitor_list = ["2330.TW", "2454.TW", "2317.TW", "NVDA", "^TWII", "0056.TW", "00878.TW"]

st.markdown("""
<style>
html, body, [class*="css"]  {
    font-size: 18px;
}
h1 {
    font-size: 42px !important;
}
h2 {
    font-size: 32px !important;
}
h3 {
    font-size: 26px !important;
}
div[data-testid="stDataFrame"] {
    font-size: 18px !important;
}
/* 確保指標卡內的標籤文字允許自動換行 */
div[data-testid="stMetricLabel"] {
    white-space: normal !important;
    word-wrap: break-word !important;
}
</style>
""", unsafe_allow_html=True)

st.title("股市監測儀表板")
st.caption("可自訂股票代號，查看報酬率、新聞聲量，並設定價格警報")

# ----------------------------
# 工具函式
# ----------------------------
def parse_tickers(text: str):
    return [t.strip() for t in text.split(",") if t.strip()]

def send_discord_notify(webhook_url: str, message: str):
    """傳送 Discord Webhook 訊息的輔助函式"""
    if not webhook_url:
        return
    data = {"content": message}
    try:
        requests.post(webhook_url, json=data, timeout=5)
    except:
        pass

@st.cache_data
def get_company_name(ticker: str, default_name: str):
    """透過 Google Finance 取得股票的中文名稱"""
    if ticker == "^TWII":
        return "加權指數"
        
    try:
        if ticker.endswith(".TW"):
            gf_ticker = f"{ticker.replace('.TW', '')}:TPE"
        elif ticker.endswith(".TWO"):
            gf_ticker = f"{ticker.replace('.TWO', '')}:TWO"
        else:
            gf_ticker = ticker 

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Safari/537.36"}
        url = f"https://www.google.com/finance/quote/{gf_ticker}?hl=zh-TW"
        res = requests.get(url, headers=headers, timeout=5)
        
        if res.status_code != 200 and ":" not in gf_ticker:
            res = requests.get(f"https://www.google.com/finance/quote/{gf_ticker}:NASDAQ?hl=zh-TW", headers=headers, timeout=5)
            if res.status_code != 200:
                res = requests.get(f"https://www.google.com/finance/quote/{gf_ticker}:NYSE?hl=zh-TW", headers=headers, timeout=5)

        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            if soup.title and soup.title.text:
                title_text = soup.title.text
                if "股價" in title_text or "price" in title_text.lower() or "- Google" in title_text:
                    name = title_text.split("(")[0].strip()
                    if name:
                        return name
            name_div = soup.find("div", class_="zzDege")
            if name_div and name_div.text:
                return name_div.text.strip()
    except:
        pass
    return default_name

@st.cache_data
def get_today_data(ticker: str):
    df = yf.Ticker(ticker).history(period="2d", interval="1d", auto_adjust=False)
    if df.empty:
        return None

    try:
        info = yf.Ticker(ticker).info
        name_en = info.get("shortName") or info.get("longName") or ticker
    except:
        name_en = ticker

    stock_name = get_company_name(ticker, name_en)

    latest = df.iloc[-1]
    prev_close = df["Close"].iloc[-2] if len(df) >= 2 else None

    if prev_close is None or pd.isna(prev_close):
        change_pct = None
    else:
        change_pct = (latest["Close"] - prev_close) / prev_close * 100

    return {
        "股票代號": ticker,
        "股票名稱": stock_name,
        "現價": latest["Close"],
        "前一日收盤價": prev_close,
        "當日漲跌幅(%)": change_pct,
        "成交量": latest.get("Volume", None),
        "日期": df.index[-1].date(),
    }

@st.cache_data
def get_return_stats(ticker: str, period: str):
    df = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=False)
    if df.empty or len(df) < 2:
        return None

    df = df.reset_index()
    df["每日報酬率(%)"] = df["Close"].pct_change() * 100
    first_close = df["Close"].iloc[0]
    df["累積報酬率(%)"] = (df["Close"] - first_close) / first_close * 100

    avg_daily_return = df["每日報酬率(%)"].dropna().mean()
    cum_return = df["累積報酬率(%)"].iloc[-1]

    return {
        "平均日報酬率": avg_daily_return,
        "累積報酬率": cum_return,
        "歷史資料": df
    }

def get_gemini_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def fetch_news_article_text(url: str) -> str:
    """Fetch a short article text snippet for AI sentiment classification."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    try:
        res = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        if res.status_code != 200:
            return ""

        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()

        parts = []
        article = soup.find("article")
        if article:
            parts.extend(p.get_text(" ", strip=True) for p in article.find_all("p"))
        if not parts:
            parts.extend(p.get_text(" ", strip=True) for p in soup.find_all("p"))

        text = " ".join(part for part in parts if part)
        return text[:3000]
    except Exception:
        return ""


def fallback_news_sentiment(title: str, description: str, article_text: str) -> str:
    text = f"{title} {description} {article_text}"
    positive_words = [
        "上漲", "成長", "獲利", "利多", "看好", "突破", "創高", "買進",
        "優於預期", "營收增", "轉強", "反彈", "升級", "漲停"
    ]
    negative_words = [
        "下跌", "衰退", "虧損", "利空", "看壞", "跌破", "重挫", "賣出",
        "不如預期", "營收減", "轉弱", "降級", "風險", "裁罰"
    ]

    score = 0
    for word in positive_words:
        if word in text:
            score += 1
    for word in negative_words:
        if word in text:
            score -= 1

    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def extract_gemini_text(data: dict) -> str:
    texts = []
    for candidate in data.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            if isinstance(part.get("text"), str):
                texts.append(part["text"])
    return "\n".join(texts)


def classify_news_sentiment_with_ai(
    ticker: str,
    stock_name: str,
    title: str,
    description: str,
    article_text: str
) -> str:
    api_key = get_gemini_api_key()
    fallback = fallback_news_sentiment(title, description, article_text)
    if not api_key:
        return fallback

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    prompt = f"""
請判斷以下新聞對「{stock_name} ({ticker})」的市場情緒是 positive、neutral、negative 三者之一。

判斷規則：
- positive：新聞內容偏利多，例如營收成長、獲利改善、訂單增加、展望上修、股價正向催化。
- negative：新聞內容偏利空，例如營收衰退、獲利下滑、展望下修、裁罰、需求疲弱、重大風險。
- neutral：資訊描述性、影響不明、正負混合，或與該股票關聯不強。

只輸出一個英文小寫單字：positive、neutral 或 negative。不要輸出任何解釋。

標題：
{title}

RSS摘要：
{description}

新聞內文片段：
{article_text[:2500]}
""".strip()

    try:
        endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        res = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": 10,
                },
            },
            timeout=25,
        )
        res.raise_for_status()
        label = extract_gemini_text(res.json()).strip().lower()
        if "positive" in label:
            return "positive"
        if "negative" in label:
            return "negative"
        if "neutral" in label:
            return "neutral"
    except Exception:
        return fallback

    return fallback


@st.cache_data(ttl=3600)
def get_news_sentiment(ticker: str, stock_name: str):
    if ticker == "^TWII":
        search_keyword = "台股 大盤"
    else:
        clean_ticker = ticker.split('.')[0]
        search_keyword = f"{clean_ticker} {stock_name}"

    query = urllib.parse.quote(search_keyword)
    url = f"https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "xml")
        items = soup.find_all("item")[:20]

        news_list = []
        pos_count = 0
        neg_count = 0
        neutral_count = 0

        for item in items:
            title = item.title.text
            link = item.link.text
            pub_date = item.pubDate.text[:-13]
            description = item.description.text if item.description else ""
            article_text = fetch_news_article_text(link)
            ai_label = classify_news_sentiment_with_ai(
                ticker=ticker,
                stock_name=stock_name,
                title=title,
                description=description,
                article_text=article_text,
            )

            if ai_label == "positive":
                sentiment = "🟢 正向"
                pos_count += 1
            elif ai_label == "negative":
                sentiment = "🔴 負向"
                neg_count += 1
            else:
                sentiment = "⚪ 中性"
                neutral_count += 1

            news_list.append({
                "情緒": sentiment,
                "新聞標題": title,
                "發布時間": pub_date,
                "連結": link
            })

        return news_list, pos_count, neg_count, neutral_count
    except Exception:
        return None, 0, 0, 0

# ----------------------------
# 側邊欄設定區 (使用者輸入與警報設定)
# ----------------------------
st.sidebar.header("監控標的設定")

with st.sidebar.form("add_ticker_form", clear_on_submit=True):
    new_ticker_input = st.text_input("新增股票代號 (多檔請用逗號分隔)")
    submit_add = st.form_submit_button("新增至清單")
    
    if submit_add and new_ticker_input.strip():
        new_tickers = parse_tickers(new_ticker_input)
        for t in new_tickers:
            if t not in st.session_state.monitor_list:
                st.session_state.monitor_list.append(t)

TICKERS = st.sidebar.multiselect(
    "目前監控清單 (點擊 X 可移除)",
    options=st.session_state.monitor_list,
    default=st.session_state.monitor_list
)

st.session_state.monitor_list = TICKERS

st.sidebar.markdown("---")
st.sidebar.header("價格警報與通知設定")
discord_webhook = st.sidebar.text_input("Discord Webhook URL (選填)", type="password", help="輸入 Webhook 網址後，觸發警報時將自動傳送訊息至 Discord")

if TICKERS:
    alert_ticker = st.sidebar.selectbox("選擇要設定警報的標的", TICKERS)
    
    current_high = st.session_state.price_alerts.get(alert_ticker, {}).get("high", 0.0)
    current_low = st.session_state.price_alerts.get(alert_ticker, {}).get("low", 0.0)
    
    col_h, col_l = st.sidebar.columns(2)
    with col_h:
        target_high = st.number_input("突破目標價", value=float(current_high), min_value=0.0, format="%.2f")
    with col_l:
        target_low = st.number_input("跌破目標價", value=float(current_low), min_value=0.0, format="%.2f")

    col_btn1, col_btn2 = st.sidebar.columns(2)
    with col_btn1:
        if st.button("儲存警報", use_container_width=True):
            st.session_state.price_alerts[alert_ticker] = {"high": target_high, "low": target_low}
            st.sidebar.success("儲存成功")
    with col_btn2:
        if st.button("刪除警報", use_container_width=True):
            if alert_ticker in st.session_state.price_alerts:
                del st.session_state.price_alerts[alert_ticker]
                st.sidebar.success("已刪除")

if st.session_state.price_alerts:
    st.sidebar.write("目前生效的警報：")
    for t, limits in st.session_state.price_alerts.items():
        st.sidebar.caption(f"[{t}] 突破: {limits['high']:.2f} / 跌破: {limits['low']:.2f}")

if not TICKERS:
    st.warning("請先於左側面板輸入至少一個股票代號")
    st.stop()

# ----------------------------
# 取得資料與警報檢查
# ----------------------------
rows = []
history_map = {}
triggered_alerts = [] 

for ticker in TICKERS:
    try:
        today_data = get_today_data(ticker)
        stat_7d = get_return_stats(ticker, "7d")
        stat_30d = get_return_stats(ticker, "30d")

        if today_data is None or stat_7d is None or stat_30d is None:
            st.warning(f"{ticker} 沒有足夠資料")
            continue

        current_price = today_data["現價"]
        stock_name = today_data["股票名稱"]
        
        if ticker in st.session_state.price_alerts:
            high_limit = st.session_state.price_alerts[ticker]["high"]
            low_limit = st.session_state.price_alerts[ticker]["low"]
            
            if high_limit > 0 and current_price >= high_limit:
                alert_msg = f"[警報觸發] {stock_name} ({ticker}) 最新價格 {current_price:.2f} 已突破目標價 {high_limit:.2f}！"
                triggered_alerts.append(alert_msg)
            elif low_limit > 0 and current_price <= low_limit:
                alert_msg = f"[警報觸發] {stock_name} ({ticker}) 最新價格 {current_price:.2f} 已跌破目標價 {low_limit:.2f}！"
                triggered_alerts.append(alert_msg)

        today_data["今日報酬率(%)"] = today_data["當日漲跌幅(%)"]
        today_data["近7日平均報酬率(%)"] = stat_7d["平均日報酬率"]
        today_data["近30日平均報酬率(%)"] = stat_30d["平均日報酬率"]
        today_data["近7日累積報酬率(%)"] = stat_7d["累積報酬率"]
        today_data["近30日累積報酬率(%)"] = stat_30d["累積報酬率"]

        rows.append(today_data)
        history_map[ticker] = stat_30d["歷史資料"]

    except Exception as e:
        st.error(f"{ticker} 抓取失敗：{e}")

if not rows:
    st.stop()

if triggered_alerts:
    for msg in triggered_alerts:
        st.error(msg)
        if discord_webhook: 
            send_discord_notify(discord_webhook, msg)

df = pd.DataFrame(rows)

numeric_cols = [
    "現價", "前一日收盤價", "當日漲跌幅(%)", "今日報酬率(%)",
    "近7日平均報酬率(%)", "近30日平均報酬率(%)",
    "近7日累積報酬率(%)", "近30日累積報酬率(%)", "成交量"
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

# ==========================================
# 區塊 1：指標卡與報酬率排行 (移至最上方)
# ==========================================
st.markdown("---")
st.subheader("整體監控標的表現")

best_today = df.sort_values("當日漲跌幅(%)", ascending=False).iloc[0]
worst_today = df.sort_values("當日漲跌幅(%)", ascending=True).iloc[0]

c1, c2, c3 = st.columns(3)

c1.metric("監控標的數", len(df))

# 保留卡片外框排版，移除強制的 color 設定，讓字體顏色在深淺色模式下自適應
with c2:
    st.markdown(f"""
    <div style="padding: 14px; border-radius: 8px; background-color: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.2); min-height: 145px;">
        <span style="font-size: 14px; opacity: 0.7; font-weight: 500;">今日漲幅最佳</span><br>
        <span style="font-size: 18px; font-weight: bold; display: block; margin-top: 3px; line-height: 1.3; white-space: normal; word-wrap: break-word;">{best_today['股票名稱']} ({best_today['股票代號']})</span>
        <div style="margin-top: 10px; display: flex; align-items: baseline;">
            <span style="font-size: 28px; font-weight: bold;">{best_today['現價']:.2f}</span>
            <span style="font-size: 16px; color: #FF3333; font-weight: bold; margin-left: 10px;">+{best_today['當日漲跌幅(%)']:.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div style="padding: 14px; border-radius: 8px; background-color: rgba(128,128,128,0.05); border: 1px solid rgba(128,128,128,0.2); min-height: 145px;">
        <span style="font-size: 14px; opacity: 0.7; font-weight: 500;">今日跌幅最差</span><br>
        <span style="font-size: 18px; font-weight: bold; display: block; margin-top: 3px; line-height: 1.3; white-space: normal; word-wrap: break-word;">{worst_today['股票名稱']} ({worst_today['股票代號']})</span>
        <div style="margin-top: 10px; display: flex; align-items: baseline;">
            <span style="font-size: 28px; font-weight: bold;">{worst_today['現價']:.2f}</span>
            <span style="font-size: 16px; color: #00AA00; font-weight: bold; margin-left: 10px;">{worst_today['當日漲跌幅(%)']:.2f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("標的各項指標排行(點擊想排序的欄位顯示排行)")

tab1, tab2, tab3 = st.tabs(["當日", "近 7 日", "近 30 日"])

with tab1:
    best = df.sort_values("當日漲跌幅(%)", ascending=False).iloc[0]
    worst = df.sort_values("當日漲跌幅(%)", ascending=True).iloc[0]
    st.write(f"**今日漲幅最佳：** {best['股票名稱']}（{best['股票代號']}） {best['當日漲跌幅(%)']:.2f}%")
    st.write(f"**今日跌幅最差：** {worst['股票名稱']}（{worst['股票代號']}） {worst['當日漲跌幅(%)']:.2f}%")
    
    styled_df1 = df.sort_values("當日漲跌幅(%)", ascending=False)[
        ["股票代號", "股票名稱", "日期", "現價", "前一日收盤價", "當日漲跌幅(%)", "成交量"]
    ].style.format({
        "現價": "{:.2f}",
        "前一日收盤價": "{:.2f}",
        "當日漲跌幅(%)": "{:.2f}%",
        "成交量": "{:,.0f}"
    }).set_properties(subset=["現價", "當日漲跌幅(%)"], **{'font-size': '20px', 'font-weight': 'bold'})
    st.dataframe(styled_df1, use_container_width=True, hide_index=True)

with tab2:
    best = df.sort_values("近7日累積報酬率(%)", ascending=False).iloc[0]
    worst = df.sort_values("近7日累積報酬率(%)", ascending=True).iloc[0]
    st.write(f"**近7日漲幅最佳：** {best['股票名稱']}（{best['股票代號']}） {best['近7日累積報酬率(%)']:.2f}%")
    st.write(f"**近7日跌幅最差：** {worst['股票名稱']}（{worst['股票代號']}） {worst['近7日累積報酬率(%)']:.2f}%")
    
    styled_df2 = df.sort_values("近7日累積報酬率(%)", ascending=False)[
        ["股票代號", "股票名稱", "近7日平均報酬率(%)", "近7日累積報酬率(%)"]
    ].style.format({
        "近7日平均報酬率(%)": "{:.2f}%",
        "近7日累積報酬率(%)": "{:.2f}%"
    }).set_properties(subset=["近7日平均報酬率(%)", "近7日累積報酬率(%)"], **{'font-size': '20px', 'font-weight': 'bold'})
    st.dataframe(styled_df2, use_container_width=True, hide_index=True)

with tab3:
    best = df.sort_values("近30日累積報酬率(%)", ascending=False).iloc[0]
    worst = df.sort_values("近30日累積報酬率(%)", ascending=True).iloc[0]
    st.write(f"**近30日漲幅最佳：** {best['股票名稱']}（{best['股票代號']}） {best['近30日累積報酬率(%)']:.2f}%")
    st.write(f"**近30日跌幅最差：** {worst['股票名稱']}（{worst['股票代號']}） {worst['近30日累積報酬率(%)']:.2f}%")
    
    styled_df3 = df.sort_values("近30日累積報酬率(%)", ascending=False)[
        ["股票代號", "股票名稱", "近30日平均報酬率(%)", "近30日累積報酬率(%)"]
    ].style.format({
        "近30日平均報酬率(%)": "{:.2f}%",
        "近30日累積報酬率(%)": "{:.2f}%"
    }).set_properties(subset=["近30日平均報酬率(%)", "近30日累積報酬率(%)"], **{'font-size': '20px', 'font-weight': 'bold'})
    st.dataframe(styled_df3, use_container_width=True, hide_index=True)


# ==========================================
# 區塊 2：個股詳細分析與新聞輿情 (移至下方)
# ==========================================
st.markdown("---")
st.subheader("個股詳細分析與新聞輿情")

dropdown_options = {}
for t in history_map.keys():
    name = df[df['股票代號'] == t]['股票名稱'].iloc[0] if not df[df['股票代號'] == t].empty else t
    dropdown_options[f"{t} ({name})"] = t

selected_display = st.selectbox("選擇要查看詳細資訊及新聞的股票", list(dropdown_options.keys()))
selected_ticker = dropdown_options[selected_display]
current_stock_name = df[df['股票代號'] == selected_ticker]['股票名稱'].iloc[0] if not df[df['股票代號'] == selected_ticker].empty else selected_ticker

st.markdown("<br>", unsafe_allow_html=True)
st.write(f"### {current_stock_name} 近 30 天價格走勢與報酬率")

history_df = history_map[selected_ticker].copy()
if "Date" in history_df.columns:
    history_df = history_df.set_index("Date")
elif "Datetime" in history_df.columns:
    history_df = history_df.set_index("Datetime")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.caption("互動式 K 線圖 (支援縮放與滑鼠懸停)")
    fig_kline = go.Figure(data=[go.Candlestick(
        x=history_df.index,
        open=history_df['Open'],
        high=history_df['High'],
        low=history_df['Low'],
        close=history_df['Close'],
        name="K線",
        increasing_line_color='#FF3333', increasing_fillcolor='#FF3333',
        decreasing_line_color='#00AA00', decreasing_fillcolor='#00AA00'
    )])

    fig_kline.update_layout(
        xaxis_rangeslider_visible=False, 
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        yaxis_title="價格",
        template="plotly_white"
    )
    st.plotly_chart(fig_kline, use_container_width=True)

with col_chart2:
    st.caption("累積報酬率走勢")
    fig_return = go.Figure(data=[go.Scatter(
        x=history_df.index,
        y=history_df['累積報酬率(%)'],
        mode='lines',
        name='累積報酬率',
        line=dict(color='#3366FF', width=2),
        fill='tozeroy', 
        fillcolor='rgba(51, 102, 255, 0.1)'
    )])

    fig_return.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        yaxis_title="報酬率 (%)",
        template="plotly_white"
    )
    st.plotly_chart(fig_return, use_container_width=True)

st.markdown("---")

with st.spinner(f"正在分析 {current_stock_name} ({selected_ticker}) 的網路新聞..."):
    news_data, pos, neg, neu = get_news_sentiment(selected_ticker, current_stock_name)

if news_data:
    total_news = pos + neg + neu
    if total_news > 0:
        st.write(f"### {current_stock_name} 聲量風向球")
        col_p, col_neu, col_n = st.columns(3)
        col_p.metric("🟢 正向新聞", f"{pos} 則", f"佔比 {round(pos/total_news*100)}%")
        col_neu.metric("⚪ 中立新聞", f"{neu} 則", f"佔比 {round(neu/total_news*100)}%")
        col_n.metric("🔴 負向新聞", f"{neg} 則", f"佔比 {round(neg/total_news*100)}%", delta_color="inverse")
        
        st.progress(pos / (pos + neg + 0.0001))
        st.caption("情緒溫度計 (偏右為正向，偏左為負向)")
        
    st.write("### 最新相關報導")
    news_df = pd.DataFrame(news_data)
    st.dataframe(
        news_df,
        column_config={
            "連結": st.column_config.LinkColumn("閱讀原文")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("目前抓不到相關新聞，或是網路請求失敗。")
