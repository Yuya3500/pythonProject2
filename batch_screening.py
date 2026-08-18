import time
import pandas as pd
import yfinance as yf


def get_target_tickers():
    tickers = set()

    # --- 1. 米国株主要指数 (S&P500 / NASDAQ100 / NYダウ) ---
    try:
        sp500 = pd.read_html(
            'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        )[0]
        tickers.update(sp500['Symbol'].tolist())
    except Exception:
        pass

    try:
        nasdaq100 = pd.read_html(
            'https://en.wikipedia.org/wiki/Nasdaq-100'
        )[4]
        tickers.update(nasdaq100['Ticker'].tolist())
    except Exception:
        pass

    try:
        dow = pd.read_html(
            'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
        )[1]
        tickers.update(dow['Symbol'].tolist())
    except Exception:
        pass

    # --- 2. 日本株主要指数 (日経225) ---
    try:
        nikkei = pd.read_html(
            'https://en.wikipedia.org/wiki/Nikkei_225'
        )[1]
        nikkei_symbols = [
            f"{str(code).zfill(4)}.T"
            for code in nikkei['Ticker'].dropna().astype(int)
        ]
        tickers.update(nikkei_symbols)
    except Exception:
        pass

    # シンボル表記補正 (例: BRK.B -> BRK-B)
    cleaned_tickers = [
        str(t).replace('.', '-') if not str(t).endswith('.T') else str(t)
        for t in tickers
    ]

    # 自動取得失敗時用の予備リスト
    if not cleaned_tickers:
        cleaned_tickers = [
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

    return list(set(cleaned_tickers))


def run_batch():
    all_tickers = get_target_tickers()
    print(
        f"取得対象の銘柄数: {len(all_tickers)} 銘柄（重複除外済み）"
    )

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

    for i, symbol in enumerate(all_tickers):
        try:
            stock = yf.Ticker(symbol)
            df_m = stock.history(period="1y", interval="1mo")
            df_w = stock.history(period="6m", interval="1wk")
            df_d = stock.history(period="1m", interval="1d")

            if df_m.empty or df_d.empty:
                continue

            market = "日本株" if symbol.endswith(".T") else "米国株"

            row = {
                "市場": market,
                "銘柄": symbol.replace(".T", ""),
                "月足_直近": get_signal_symbol(df_m, -1),
                "月足_前月": get_signal_symbol(df_m, -2),
                "週足_直近": get_signal_symbol(df_w, -1),
                "週足_前週": get_signal_symbol(df_w, -2),
                "日足_直近": get_signal_symbol(df_d, -1),
                "日足_前日": get_signal_symbol(df_d, -2),
            }
            results.append(row)

            # Yahoo Finance側の制限回避用のウェイト
            time.sleep(0.15)

        except Exception:
            continue

    df_res = pd.DataFrame(results)
    df_res.to_csv("results.csv", index=False, encoding="utf-8-sig")
    print(
        f"スクリーニング完了: {len(df_res)} 銘柄を results.csv に保存しました"
    )


if __name__ == "__main__":
    run_batch()