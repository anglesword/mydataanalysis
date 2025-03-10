import yfinance as yf
import pandas as pd

tickers = ["SPY", "QQQ", "JEPQ", "JEPI", "QYLD", "QDTE", "MSTY"]
total_returns = {}

start_date = "2020-01-01"
end_date = "2025-04-15"

for ticker in tickers:
    stock = yf.Ticker(ticker)

    # 获取历史收盘价
    hist = stock.history(start=start_date, end=end_date)["Close"].dropna()
    if len(hist) < 2:
        print(f"{ticker} 数据不足，跳过")
        continue

    start_price = hist.iloc[0]
    end_price = hist.iloc[-1]

    # 获取历史分红并累计
    dividends = stock.dividends[start_date:end_date].sum()

    # 总收益率
    total_return_pct = ((end_price + dividends - start_price) / start_price) * 100

    total_returns[ticker] = {
        "开始日期": hist.index[0].date(),
        "结束日期": hist.index[-1].date(),
        "起始价格 ($)": round(start_price, 2),
        "结束价格 ($)": round(end_price, 2),
        "累计分红 ($)": round(dividends, 2),
        "总收益率 (%)": round(total_return_pct, 2)
    }

# 输出结果表格
df_total = pd.DataFrame(total_returns).T
print("📊 各ETF总收益率（含分红）:")
print(df_total)