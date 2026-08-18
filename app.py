import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="トレンド反転サイン スクリーニング", layout="wide")

st.title("📊 トレンド反転サイン - 2段ヘッダー表示スクリーニング")
st.markdown("各時間足ごとに直近3期間のシグナルを独立した列として表示します。")

tickers = [
    "AAPL", "NVDA", "TSLA", "AMD", "MSFT", "AMZN",
    "GOOGL", "META", "NFLX", "INTC",
    "7203.T", "9984.T", "6758.T", "6861.T", "7974.T",
    "8306.T", "9432.T", "6501.T", "8035.T", "4063.T"
]

timeframes = ["月足", "週足", "日足", "4時間足", "1時間足"]

# パラメータ設定 (Pine Script v5 準拠)
numTrendFollowLng = 100
numTrendFollowMid = 50
numTrendFollowSht = 25
numTrendConstSht = 5
numSmooth = 2
no_tsl = 10


def calc_rma(series, length):
    return series.ewm(alpha=1 / length, adjust=False).mean()


def calc_rsi(series, length):
    series = pd.Series(series.values.flatten(), index=series.index)
    delta = series.diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    rma_up = calc_rma(up, length)
    rma_down = calc_rma(down, length)

    rs = rma_up / rma_down.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def calc_stoch_rsi(rsi_series, length, smooth_k):
    rsi_series = pd.Series(rsi_series.values.flatten(), index=rsi_series.index)
    lowest_rsi = rsi_series.rolling(window=length, min_periods=1).min()
    highest_rsi = rsi_series.rolling(window=length, min_periods=1).max()
    denom = highest_rsi - lowest_rsi

    stoch_rsi = np.where(denom == 0, 100.0, 100.0 * (rsi_series - lowest_rsi) / denom)
    stoch_rsi_series = pd.Series(stoch_rsi, index=rsi_series.index)
    return stoch_rsi_series.rolling(window=smooth_k, min_periods=1).mean().round(4)


def format_bar_date(dt_val, tf):
    if pd.isna(dt_val):
        return ""
    if tf == "月足":
        return dt_val.strftime("%m月")
    elif tf in ["週足", "日足"]:
        return dt_val.strftime("%m/%d")
    else:
        return dt_val.strftime("%m/%d %H:%M")


def get_signal_at_idx(close, high, low, tsl, k_dict, idx):
    if abs(idx) + 1 > len(close):
        return "-"

    c_val = close.iloc[idx]
    tsl_val = tsl.iloc[idx] if not np.isnan(tsl.iloc[idx]) else c_val
    h_val, h_prev = high.iloc[idx], high.iloc[idx - 1]
    l_val, l_prev = low.iloc[idx], low.iloc[idx - 1]

    is_uptrend = c_val >= tsl_val

    def is_100(val):
        return not np.isnan(val) and val >= 100.0

    def is_0(val):
        return not np.isnan(val) and val <= 0.0

    c_cyan = "#00F7FF"  # 超短期
    c_green = "#00FF2A"  # 短期
    c_yellow = "#FBFF00"  # 中期
    c_orange = "#FFA600"  # 長期

    # High判定
    high_priority, high_char, high_color = 0, "", ""
    if is_uptrend:
        if is_100(k_dict['LngHigh'].iloc[idx - 1]) and h_val < h_prev:
            high_priority, high_char, high_color = 6, "▼", c_orange
        elif is_100(k_dict['MidHigh'].iloc[idx - 1]) and h_val < h_prev:
            high_priority, high_char, high_color = 5, "▼", c_yellow
        elif is_100(k_dict['ShtHigh'].iloc[idx - 1]) and h_val < h_prev:
            high_priority, high_char, high_color = 4, "▼", c_green
        elif is_100(k_dict['LngHigh'].iloc[idx]):
            high_priority, high_char, high_color = 3, "■", c_orange
        elif is_100(k_dict['MidHigh'].iloc[idx]):
            high_priority, high_char, high_color = 2, "■", c_yellow
        elif is_100(k_dict['ShtHigh'].iloc[idx]):
            high_priority, high_char, high_color = 1, "■", c_green
    else:
        if is_100(k_dict['AntShtHigh'].iloc[idx - 1]) and h_val < h_prev:
            high_priority, high_char, high_color = 2, "▼", c_cyan
        elif is_100(k_dict['AntShtHigh'].iloc[idx]):
            high_priority, high_char, high_color = 1, "■", c_cyan

    # Bottom判定
    low_priority, low_char, low_color = 0, "", ""
    if is_uptrend:
        if is_0(k_dict['AntShtBottom'].iloc[idx - 1]) and l_val > l_prev:
            low_priority, low_char, low_color = 2, "▲", c_cyan
        elif is_0(k_dict['AntShtBottom'].iloc[idx]):
            low_priority, low_char, low_color = 1, "●", c_cyan
    else:
        if is_0(k_dict['LngBottom'].iloc[idx - 1]) and l_val > l_prev:
            low_priority, low_char, low_color = 6, "▲", c_orange
        elif is_0(k_dict['MidBottom'].iloc[idx - 1]) and l_val > l_prev:
            low_priority, low_char, low_color = 5, "▲", c_yellow
        elif is_0(k_dict['ShtBottom'].iloc[idx - 1]) and l_val > l_prev:
            low_priority, low_char, low_color = 4, "▲", c_green
        elif is_0(k_dict['LngBottom'].iloc[idx]):
            low_priority, low_char, low_color = 3, "●", c_orange
        elif is_0(k_dict['MidBottom'].iloc[idx]):
            low_priority, low_char, low_color = 2, "●", c_yellow
        elif is_0(k_dict['ShtBottom'].iloc[idx]):
            low_priority, low_char, low_color = 1, "●", c_green

    if high_priority > 0 and high_priority >= low_priority:
        return f'<span style="color:{high_color}; font-weight:bold;">{high_char}</span>'
    elif low_priority > 0:
        return f'<span style="color:{low_color}; font-weight:bold;">{low_char}</span>'
    else:
        return "-"


def evaluate_ticker(ticker):
    results = {}
    dates_dict = {}
    stock = yf.Ticker(ticker)

    tf_configs = {
        "月足": ("10y", "1mo"),
        "週足": ("5y", "1wk"),
        "日足": ("2y", "1d"),
        "4時間足": ("60d", "1h"),
        "1時間足": ("60d", "1h")
    }

    for tf, (period, interval) in tf_configs.items():
        try:
            df = stock.history(period=period, interval=interval, auto_adjust=False)
            if df.empty or len(df) < 30:
                results[tf] = ["-", "-", "-"]
                dates_dict[tf] = ["-", "-", "-"]
                continue

            if tf == "4時間足":
                df = df.resample('4h').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                }).dropna()
                if len(df) < 20:
                    results[tf] = ["-", "-", "-"]
                    dates_dict[tf] = ["-", "-", "-"]
                    continue

            close = pd.Series(df['Close'].values.flatten(), index=df.index)
            high = pd.Series(df['High'].values.flatten(), index=df.index)
            low = pd.Series(df['Low'].values.flatten(), index=df.index)

            res = high.rolling(window=no_tsl, min_periods=1).max()
            sup = low.rolling(window=no_tsl, min_periods=1).min()

            avd = pd.Series(0, index=df.index)
            avd[close > res.shift(1)] = 1
            avd[close < sup.shift(1)] = -1

            avn = avd.replace(0, np.nan).ffill().fillna(0)
            tsl = pd.Series(np.where(avn == 1, sup, res), index=df.index)

            k_dict = {
                'AntShtHigh': calc_stoch_rsi(calc_rsi(high, numTrendConstSht), numTrendConstSht, numSmooth),
                'AntShtBottom': calc_stoch_rsi(calc_rsi(low, numTrendConstSht), numTrendConstSht, numSmooth),
                'ShtHigh': calc_stoch_rsi(calc_rsi(high, numTrendFollowSht), numTrendFollowSht, numSmooth),
                'ShtBottom': calc_stoch_rsi(calc_rsi(low, numTrendFollowSht), numTrendFollowSht, numSmooth),
                'MidHigh': calc_stoch_rsi(calc_rsi(high, numTrendFollowMid), numTrendFollowMid, numSmooth),
                'MidBottom': calc_stoch_rsi(calc_rsi(low, numTrendFollowMid), numTrendFollowMid, numSmooth),
                'LngHigh': calc_stoch_rsi(calc_rsi(high, numTrendFollowLng), numTrendFollowLng, numSmooth),
                'LngBottom': calc_stoch_rsi(calc_rsi(low, numTrendFollowLng), numTrendFollowLng, numSmooth)
            }

            dates = df.index
            s3 = get_signal_at_idx(close, high, low, tsl, k_dict, -3)
            s2 = get_signal_at_idx(close, high, low, tsl, k_dict, -2)
            s1 = get_signal_at_idx(close, high, low, tsl, k_dict, -1)

            results[tf] = [s3, s2, s1]
            dates_dict[tf] = [
                format_bar_date(dates[-3], tf),
                format_bar_date(dates[-2], tf),
                format_bar_date(dates[-1], tf)
            ]

        except Exception:
            results[tf] = ["-", "-", "-"]
            dates_dict[tf] = ["-", "-", "-"]

    return results, dates_dict


if st.button("スクリーニングを実行する"):
    with st.spinner("スクリーニング計算中... (10〜20秒かかります)"):
        all_rows = []
        sample_dates = None

        for t in tickers:
            sig_dict, dates_dict = evaluate_ticker(t)
            if sample_dates is None and dates_dict["日足"][0] != "-":
                sample_dates = dates_dict

            row = {"銘柄": t}
            for tf in timeframes:
                sigs = sig_dict.get(tf, ["-", "-", "-"])
                for i in range(3):
                    # MultiIndexの列キーを作成
                    d_label = dates_dict[tf][i] if tf in dates_dict else f"T-{2 - i}"
                    row[(tf, d_label)] = sigs[i]
            all_rows.append(row)

        # MultiIndex DataFrame の構築
        columns = [("銘柄", "")]
        if sample_dates:
            for tf in timeframes:
                for d_label in sample_dates[tf]:
                    columns.append((tf, d_label))

        # データの整形
        formatted_rows = []
        for r in all_rows:
            f_row = {"(銘柄, '')": r["銘柄"]}
            for tf in timeframes:
                sigs = [r.get((tf, sample_dates[tf][i]), "-") if sample_dates else "-" for i in range(3)]
                for i in range(3):
                    d_label = sample_dates[tf][i] if sample_dates else f"T-{2 - i}"
                    f_row[f"('{tf}', '{d_label}')"] = r[(tf, d_label)] if (tf, d_label) in r else sigs[i]
            formatted_rows.append(f_row)

        # Pandasの多重カラム表を作成
        df_flat = pd.DataFrame(formatted_rows)

        # MultiIndexカラムに再変換
        tuples = [("銘柄", "銘柄")]
        for tf in timeframes:
            for i in range(3):
                d_label = sample_dates[tf][i] if sample_dates else f"T-{2 - i}"
                tuples.append((tf, d_label))

        df_result = pd.DataFrame([list(r.values()) for r in formatted_rows], columns=pd.MultiIndex.from_tuples(tuples))

        # インデックスから銘柄を排除して見た目をすっきり
        df_result = df_result.set_index(("銘柄", "銘柄"))
        df_result.index.name = "銘柄"

        st.write("### スクリーニング結果一覧")
        st.write(df_result.to_html(escape=False), unsafe_allow_html=True)
        st.success("計算が完了しました！")
else:
    st.info("上のボタンを押すとスクリーニングが始まります。")