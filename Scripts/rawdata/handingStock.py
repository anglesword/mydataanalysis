from typing import Optional

import plotly.graph_objs as go
import plotly.offline as pyo
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mplcursors
import yfinance as yf
from pandas import DataFrame
import time

# download {NVDA} stock data from yfinance
def fetch_stock_data(symbol, start_date, end_date) -> Optional[DataFrame]:
    data = yf.download(symbol, start=start_date, end=end_date)
    return data

# clean data
def clean_data(data : Optional[DataFrame]) -> None:
    # handing miss value
    data.dropna(inplace=True)
    data.bfill()


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


def plot_stock_data_ext(data : Optional[DataFrame], symbol) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))

    # 画折线图
    ax.plot(data.index, data["Close"], label="Close Price", color="blue", linewidth=2)

    # 格式化 x 轴日期
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # 自动调整日期显示
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # 设置日期格式
    plt.xticks(rotation=45)  # 旋转 x 轴日期

    # 鼠标悬停时显示收盘价
    cursor = mplcursors.cursor(ax, hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(
        f"日期: {data.index[sel.index].strftime('%Y-%m-%d')}\n收盘价: {data['Close'][sel.index]:.2f}"
    ))

    # 允许鼠标滚轮缩放
    def on_scroll(event):
        scale_factor = 1.2 if event.step > 0 else 0.8  # 鼠标滚轮方向
        xlim = ax.get_xlim()
        x_center = (xlim[0] + xlim[1]) / 2
        new_xlim = [x_center + (x - x_center) * scale_factor for x in xlim]
        ax.set_xlim(new_xlim)
        fig.canvas.draw()

    fig.canvas.mpl_connect("scroll_event", on_scroll)  # 绑定滚轮事件

    # 设置标题
    ax.set_title(f"{symbol} 股票收盘价", fontsize=14)
    ax.set_xlabel("日期")
    ax.set_ylabel("价格（USD）")
    ax.legend()

    plt.show()

# display result by go
def plot_stock_data_go(data : Optional[DataFrame], symbol, annotate_interval=3) -> None:
    fig = go.Figure()
    # pyo.init_notebook_mode(connected=True)

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

    fig.show() # 显示交互式图表
    # fig.write_html("stock_chart.html")
    # plotly.offline.plot(fig)

# Entry
def main():
    symbol = "NVDA"
    start_date = "2023-01-01"
    end_date = "2025-03-01"

    data = fetch_stock_data(symbol, start_date, end_date)
    clean_data(data)
    data = calculate_moving_averages(data)
    plot_stock_data_ext(data, symbol)


if __name__ == "__main__":
    main()