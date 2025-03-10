import yfinance as yf

# 计算卖出收益 + 分红收入（不含复利收入）
'''
ticker: 股票或 ETF 代码（如 QYLD）
buy_price: 买入价格
shares: 买入股数（整数或浮点）
sell_price: 卖出价格
start_date, end_date: 持有期间
'''
def calculate_total_return_basic(ticker, buy_price, shares, sell_price, start_date, end_date):
    stock = yf.Ticker(ticker)

    # 计算总买入金额
    buy_amount = buy_price * shares

    # 分红记录（Series，每股）
    dividends = stock.dividends[start_date:end_date]
    total_dividends = dividends.sum()
    total_dividend_income = total_dividends * shares

    # 卖出总收入
    sell_amount = sell_price * shares

    # 总收益
    total_profit = sell_amount + total_dividend_income - buy_amount
    total_return_pct = (total_profit / buy_amount) * 100

    print(f"\n📈 {ticker}（基础总收益）:")
    print(f"买入价格：${buy_price:.2f}，买入股数：{shares}，买入成本：{shares*buy_price:.2f}")
    print(f"卖出价格：${sell_price:.2f}，卖出金额：{shares*sell_price}")
    print(f"期间每股分红累计：${total_dividends:.4f}，总分红：${total_dividend_income:.2f}")
    print(f"总收益：${total_profit:.2f}")
    print(f"总收益率：{total_return_pct:.2f}%")

    return {
        "总收益": total_profit,
        "总收益率(%)": total_return_pct,
        "分红收入": total_dividend_income
    }

# 计算总收入：包含复利计算（每次分红再投资为新股）
def calculate_total_return_with_reinvestment(ticker, buy_price, shares, sell_price, start_date, end_date):
    stock = yf.Ticker(ticker)

    prices = stock.history(start=start_date, end=end_date)["Close"]
    dividends = stock.dividends[start_date:end_date]

    # 初始持股
    total_shares = shares
    reinvested_dividends = 0.0

    for date, dividend_per_share in dividends.items():
        if date not in prices:
            continue
        close_price = prices.loc[date]
        dividend_total = dividend_per_share * total_shares
        reinvested_shares = dividend_total / close_price
        total_shares += reinvested_shares
        reinvested_dividends += dividend_total

    # 最终卖出金额（所有股份）
    sell_amount = total_shares * sell_price
    initial_cost = buy_price * shares
    total_profit = sell_amount - initial_cost
    total_return_pct = (total_profit / initial_cost) * 100

    print(f"\n🔁 {ticker}（复利收益）:")
    print(f"初始买入股数：{shares}，买入成本：${initial_cost:.2f}")
    print(f"复投资分红再购入股数：{total_shares - shares:.4f}")
    print(f"最终总股数：{total_shares:.4f}")
    print(f"总卖出金额：${sell_amount:.2f}")
    print(f"总收益（含再投资）：${total_profit:.2f}")
    print(f"总收益率：{total_return_pct:.2f}%")

    return {
        "最终股数": total_shares,
        "再投资增加股数": total_shares - shares,
        "总收益": total_profit,
        "总收益率(%)": total_return_pct
    }