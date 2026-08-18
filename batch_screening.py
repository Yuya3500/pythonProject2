import pandas as pd
import yfinance as yf

# 監視銘柄リストの定義 (主要銘柄または全銘柄リスト)
# ※全銘柄にする場合は、リストに全ティッカーを追加するか、CSVから読み込みます
US_TICKERS = ["AAPL", "NVDA", "TSLA", "AMD", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "INTC"]
JP_TICKERS = ["7203.T", "8306.T", "6758.T", "9984.T", "6861.T", "7267.T", "8035.T", "9432.T", "6501.T", "7751.T"]

ALL_TICKERS = US_TICKERS + JP_TICKERS


def run_batch():
    results = []

    def get_signal_symbol(df, index_offset):
        if len(df) < abs(index_offset):
            return "-"
        close = df['Close'].iloc[index_offset]
        open_p = df['Open'].iloc[index_offset]
        if close > open_p * 1.05:
            return "▲"  # オレンジ買シグナル候補
        elif close < open_p * 0.95:
            return "▼"  # 黄売シグナル候補
        return "-"

    for symbol in ALL_TICKERS:
        try:
            stock = yf.Ticker(symbol)
            df_m = stock.history(period="1y", interval="1mo")
            df_w = stock.history(period="6m", interval="1wk")
            df_d = stock.history(period="1m", interval="1d")

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
        except Exception:
            continue

    df_res = pd.DataFrame(results)
    df_res.to_csv("results.csv", index=False, encoding="utf-8-sig")
    print("スクリーニング完了: results.csv に保存しました")


if __name__ == "__main__":
    run_batch()