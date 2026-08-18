import time
import pandas as pd
import yfinance as yf

# 米国株・日本株の主要指数構成銘柄リスト
TARGET_TICKERS = [
    # --- 米国株 (S&P500 / NASDAQ100 / DOW 主要銘柄) ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "JPM", "XOM", "V", "PG", "MA", "HD", "CVX", "MRK", "ABBV", "PEP", "COST",
    "ADBE", "MCD", "WMT", "CSCO", "ACN", "TMO", "ABT", "DHR", "NFLX", "AMD",
    "DIS", "ORCL", "INTC", "CMCSA", "PFE", "AMGN", "TXN", "HON", "IBM", "QCOM",
    "GE", "CAT", "BA", "SBUX", "GS", "MS", "BLK", "NOW", "INTU", "ISRG", "BKNG",

    # --- 日本株 (日経225 / TOPIX 主要銘柄) ---
    "7203.T", "8306.T", "6758.T", "9984.T", "6861.T", "7267.T", "8035.T", "9432.T",
    "6501.T", "7751.T", "8316.T", "6098.T", "4063.T", "8058.T", "8031.T", "3382.T",
    "6367.T", "4568.T", "6920.T", "6902.T", "7974.T", "9020.T", "2914.T", "4519.T",
    "6503.T", "6981.T", "8001.T", "8002.T", "8591.T", "8766.T", "9101.T", "9104.T"
]


def run_batch():
    all_tickers = list(set(TARGET_TICKERS))
    print(f"取得対象銘柄数: {len(all_tickers)} 銘柄")

    results = []

    def get_signal_symbol(df, index_offset):
        if len(df) < abs(index_offset):
            return "-"
        close = df['Close'].iloc[index_offset]
        open_p = df['Open'].iloc[index_offset]
        if close > open_p * 1.05:
            return "▲"
        elif close < open_p * 0.95:
            return "▼"
        return "-"

    for symbol in all_tickers:
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
            time.sleep(0.1)

        except Exception as e:
            print(f"Error {symbol}: {e}")
            continue

    df_res = pd.DataFrame(results)

    # データが存在する場合のみ書き出し
    if not df_res.empty:
        df_res.to_csv("results.csv", index=False, encoding="utf-8-sig")
        print(f"スクリーニング完了: {len(df_res)} 銘柄を results.csv に保存しました")
    else:
        print("エラー: 取得データがゼロです")


if __name__ == "__main__":
    run_batch()