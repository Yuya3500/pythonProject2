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

# --- 2. メインヘッダー ---
st.title("📊 トレンド反転サイン スクリーニング")

# --- 3. サイドバー設定 ---
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


# --- 4. データ読み込み機能 ---
@st.cache_data(ttl=600)
def load_data():
  if os.path.exists("results.csv") and os.path.getsize("results.csv") > 10:
    return pd.read_csv("results.csv")
  return pd.DataFrame()


df = load_data()

# --- 5. 画面表示 ---
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
  # hide_index=True で左端の 0, 1, 2... を非表示
  st.dataframe(df, use_container_width=True, hide_index=True)
else:
  st.warning(
      "現在、自動スクリーニングデータを準備中です。GitHub Actionsの完了をお待ちください。"
  )