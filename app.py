import os
import time
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="トレンド反転サイン スクリーニング", layout="wide"
)

# --- 1. ログイン認証 ---
if "authenticated" not in st.session_state:
  st.session_state.authenticated = False

if not st.session_state.authenticated:
  st.title("🔒 ログイン画面")
  input_pass = st.text_input("パスワードを入力してください", type="password")
  if st.button("ログイン"):
    if input_pass == "16KTMtdcd7432":
      st.session_state.authenticated = True
      st.rerun()
    else:
      st.error("パスワードが違います")
  st.stop()

st.title("📊 トレンド反転サイン スクリーニング")


# --- 2. データ取得処理 ---
@st.cache_data(ttl=1800)
def fetch_data():
  TARGET_TICKERS = [
      "AAPL",
      "MSFT",
      "GOOGL",
      "AMZN",
      "NVDA",
      "META",
      "TSLA",
      "7203.T",
      "8306.T",
      "6758.T",
      "9984.T",
      "6861.T",
  ]
  results = []

  def get_signal_symbol(df, index_offset):
    if len(df) < abs(index_offset):
      return "-"
    close = df["Close"].iloc[index_offset]
    open_p = df["Open"].iloc[index_offset]
    if close > open_p * 1.05:
      return "▲"
    elif close < open_p * 0.95:
      return "▼"
    return "-"

  for symbol in TARGET_TICKERS:
    try:
      stock = yf.Ticker(symbol)
      # 正しいパラメータ(6mo, 3mo, 1mo)
      df_m = stock.history(period="6mo", interval="1mo")
      df_w = stock.history(period="3mo", interval="1wk")
      df_d = stock.history(period="1mo", interval="1d")

      if df_m.empty or df_d.empty:
        continue

      market = "日本株" if symbol.endswith(".T") else "米国株"
      results.append({
          "市場": market,
          "銘柄": symbol.replace(".T", ""),
          "月足_直近": get_signal_symbol(df_m, -1),
          "月足_前月": get_signal_symbol(df_m, -2),
          "週足_直近": get_signal_symbol(df_w, -1),
          "週足_前週": get_signal_symbol(df_w, -2),
          "日足_直近": get_signal_symbol(df_d, -1),
          "日足_前日": get_signal_symbol(df_d, -2),
      })
      time.sleep(0.05)
    except Exception:
      continue

  return pd.DataFrame(results)


# ローカルCSVがあれば読み込み、無ければ通信取得
if os.path.exists("results.csv") and os.path.getsize("results.csv") > 10:
  df = pd.read_csv("results.csv")
else:
  with st.spinner("最新データを取得中..."):
    df = fetch_data()

# --- 3. メインUI表示 ---
st.sidebar.header("⚙️ 抽出条件設定")
market_filter = st.sidebar.selectbox(
    "対象市場", ["すべて", "米国株", "日本株"]
)

st.sidebar.subheader("🔍 銘柄抽出フィルター")
filter_enabled = st.sidebar.checkbox(
    "特定のシグナルで絞り込む", value=False
)
target_timeframe = st.sidebar.selectbox(
    "対象の時間足", ["月足", "週足", "日足"]
)
target_signal = st.sidebar.selectbox(
    "検出したいシグナル", ["▲ (買シグナル)", "▼ (売シグナル)"]
)

if not df.empty:
  if market_filter != "すべて":
    df = df[df["市場"] == market_filter]

  if filter_enabled:
    signal_char = "▲" if "▲" in target_signal else "▼"
    col_name = f"{target_timeframe}_直近"
    if col_name in df.columns:
      df = df[df[col_name] == signal_char]
      st.info(
          f"🔍 抽出結果: **【{market_filter}】** /"
          f" **【{target_timeframe}】** で **【{target_signal}】**"
          f" が発生中 ({len(df)} 件)"
      )

  st.subheader("📋 最新スクリーニング結果一覧")
  st.dataframe(df, use_container_width=True)
else:
  st.error("データの取得に失敗しました。")