from typing import Optional

import plotly.graph_objs as go
import matplotlib.pyplot as plt
import plotly.offline
import yfinance as yf
from pandas import DataFrame
import time

# download {NVDA} stock data from yfinance
def fetch_stock_data(symbol, start_date, end_date) -> Optional[DataFrame]:
    data = yf.download(symbol, start=start_date, end=end_date)
    # print(time.strftime('%Y/%m/%d', time.strptime(str(data.index[0]), '%Y-%m-%d %H:%M:%S')))
    # print(data.iloc[0]['Close'])
    # print(data.iat[0, 0])
    # for i in range(0, len(data)):
        # print(f"date1={data.index[i]}, price1={data['Close']}")
    return data

# clean data
def clean_data(data : Optional[DataFrame]) -> None:
    # handing miss value
    data.dropna(inplace=True)


# transform data : Calculate 20-day and 50-day moving averages
def calculate_moving_averages(data : Optional[DataFrame], short_window=20, long_window=50) -> Optional[DataFrame]:
    data['MA20'] = data['Close'].rolling(window=short_window).mean()
    data['MA50'] = data['Close'].rolling(window=long_window).mean()
    return data

# display result by plt: plotting closing prices and moving averages
def plot_stock_data(data : Optional[DataFrame], symbol, annotate_interval=3) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data["Close"], label="Close Price", color="blue", alpha=0.6)
    plt.plot(data.index, data["MA20"], label="20-day MA", color="red", linestyle="--")
    plt.plot(data.index, data["MA50"], label="50-day MA", color="green", linestyle="--")

    # 查找股票连续下跌天数超过2天，然后股价回升，并标注价格
    cnt = 0
    price1 = None
    price2 = None
    date1 = None
    date2 = None
    for i in range(0, len(data)):
        if price1 is None:
            # date1 = time.strftime('%Y/%m/%d', time.strptime(str(data.index[i]), '%Y-%m-%d %H:%M:%S'))
            date1 = data.index[i]
            price1 = round(data.iat[i, 0], 2)
            continue
        else:
            # date2 = time.strftime('%Y/%m/%d', time.strptime(str(data.index[i]), '%Y-%m-%d %H:%M:%S'))
            date2 = data.index[i]
            price2 = round(data.iat[i, 0], 2)
            if price1 > price2:
                date1 = date2
                price1 = price2
                cnt = cnt + 1
            else:
                if cnt >= annotate_interval:
                    # 此时表示当前价格已经连续下跌要求的间隔天数，需要在图中标注
                    print(f"cnt={cnt}, date1={date1}, price1={price1}, date2={date2} ,price2={price2}")
                    plt.annotate(f"{price1}",
                                 xy=(date1, price1),
                                 #xytext=(-10, 5),
                                 #textcoords='offset points',
                                 fontsize=8, color='black', rotation=0)
                date1 = date2
                price1 = price2
                cnt = 0

    plt.title(f"{symbol} Stock Price and Moving Averages")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.legend()
    plt.grid()
    plt.show()

# display result by go
def plot_stock_data_go(data : Optional[DataFrame], symbol, annotate_interval=3) -> None:
    fig = go.Figure()

    # 添加收盘价曲线
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"],
                             mode='lines', name='Close Price',
                             line=dict(color='blue')))

    # 添加 20 天均线
    fig.add_trace(go.Scatter(x=data.index, y=data["MA20"],
                             mode='lines', name='20-day MA',
                             line=dict(color='red', dash='dash')))

    # 添加 50 天均线
    fig.add_trace(go.Scatter(x=data.index, y=data["MA50"],
                             mode='lines', name='50-day MA',
                             line=dict(color='green', dash='dash')))


    # 配置交互功能
    fig.update_layout(
        title=f"{symbol} Stock Price & Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis=dict(rangeslider=dict(visible=True)),  # 启用时间轴缩放
        hovermode="x unified",  # 鼠标悬停时显示所有数值
        template="plotly_dark"  # 黑色主题，可改成 "plotly_white"
    )

    fig.show()  # 显示交互式图表
    # plotly.offline.plot(fig)

# Entry
def main():
    symbol = "NVDA"
    start_date = "2023-01-01"
    end_date = "2025-03-01"

    data = fetch_stock_data(symbol, start_date, end_date)
    clean_data(data)
    data = calculate_moving_averages(data)
    plot_stock_data_go(data, symbol)


if __name__ == "__main__":
    main()