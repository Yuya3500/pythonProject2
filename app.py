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

# --- 2. メイン画面 ---
st.title("📊 トレンド反転サイン スクリーニング")

CSV_FILE = "results.csv"


# データロード関数
def load_data():
  # パターン1: ディスク上のCSVを読む
  if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 10:
    try:
      df = pd.read_csv(CSV_FILE)
      if not df.empty:
        return df
    except Exception:
      pass

  # パターン2: 存在しない/空の場合はその場で最小セットを取得生成
  TARGET_TICKERS = [
      "AAPL",
      "MSFT",
      "GOOGL",
      "AMZN",
      "NVDA",
      "7203.T",
      "8306.T",
      "6758.T",
      "9984.T",
  ]
  results = []

  def get_signal_symbol(df_stock, index_offset):
    if len(df_stock) < abs(index_offset):
      return "-"
    close = df_stock["Close"].iloc[index_offset]
    open_p = df_stock["Open"].iloc[index_offset]
    if close > open_p * 1.05:
      return "▲"
    elif close < open_p * 0.95:
      return "▼"
    return "-"

  for symbol in TARGET_TICKERS:
    try:
      stock = yf.Ticker(symbol)
      df_m = stock.history(period="6m", interval="1mo")
      df_w = stock.history(period="3m", interval="1wk")
      df_d = stock.history(period="1m", interval="1d")

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
      time.sleep(0.1)
    except Exception:
      continue

  df_res = pd.DataFrame(results)
  if not df_res.empty:
    df_res.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
  return df_res


df = load_data()

# サイドバー設定
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
  st.error(
      "データの読み込み・自動生成に失敗しました。時間をおいて再読み込みしてください。"
  )