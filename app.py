import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="トレンド反転サイン スクリーニング", layout="wide"
)

# 1. ログイン認証
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

# 2. メイン画面
st.title("📊 トレンド反転サイン スクリーニング")

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
    "検出したいシグナル", ["▲ (買シグナル)", "▼ (売シグナル)", "■", "●"]
)

# CSVデータ読み込みの安全対策
CSV_FILE = "results.csv"

is_file_valid = False
if os.path.exists(CSV_FILE):
  try:
    if os.path.getsize(CSV_FILE) > 0:
      df = pd.read_csv(CSV_FILE)
      if not df.empty:
        is_file_valid = True
  except Exception:
    pass

if is_file_valid:
  # 市場絞り込み
  if market_filter != "すべて":
    df = df[df["市場"] == market_filter]

  # シグナル抽出処理
  if filter_enabled:
    signal_char = (
        "▲"
        if "▲" in target_signal
        else ("▼" if "▼" in target_signal else "■")
    )
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
  st.warning(
      "⚠️ 現在、表示できるデータ（results.csv）がないか、空の状態です。"
  )
  st.info(
      "GitHubの Actions タブから手動でワークフローを実行するか、次回の自動更新をお待ちください。"
  )