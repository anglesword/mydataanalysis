import itertools

import plotly.graph_objs as go
import yfinance as yf
import pandas as pd

symbol = "NVDA"
start_date = "2024-01-01"
end_date = "2024-12-31"

# pd.set_option('display.max_columns', None)

# 例子
def plot_instance() -> None:
    # 示例数据
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
    open_prices = [180, 185, 182, 188]
    high_prices = [190, 195, 189, 200]
    low_prices = [175, 180, 178, 185]
    close_prices = [185, 182, 188, 195]

    # 创建 K 线图
    fig = go.Figure(data=[
        go.Candlestick(
            x=dates,
            open=open_prices,
            high=high_prices,
            low=low_prices,
            close=close_prices,
            increasing_line_color='red',  # 上涨颜色
            decreasing_line_color='green'  # 下跌颜色
        )
    ])

    # 更新布局
    fig.update_layout(
        title="示例 K 线图",
        xaxis_title="日期",
        yaxis_title="价格",
        xaxis_rangeslider_visible=False  # 关闭底部的范围滑动条
    )

    # 显示图表
    fig.show()

# 理解DataFrame数据结构
def plot_dataframe() -> None:
    data = yf.download(symbol, start=start_date, end=end_date)
    dates = data.index
    open_prices = data["Open"].values.tolist()
    high_prices = data["High"]
    low_prices = data["Low"]
    close_prices = data["Close"]
    print(list(itertools.chain(*open_prices)))

# 获取数据并显示
def plot_stock() -> None:
    df = yf.download(symbol, start=start_date, end=end_date)
    print(df)
    # 创建蜡烛图
    fig = go.Figure(data=[
        go.Candlestick(
            x=df.index,  # 日期
            open=list(itertools.chain(*(df['Open'].values.tolist()))),  # 开盘价
            high=list(itertools.chain(*(df['High'].values.tolist()))),  # 最高价
            low=list(itertools.chain(*(df['Low'].values.tolist()))),  # 最低价
            close=list(itertools.chain(*(df['Close'].values.tolist()))),  # 收盘价
            increasing_line_color='green',  # 涨（收盘价高于开盘价）颜色
            decreasing_line_color='red'  # 跌（收盘价低于开盘价）颜色
        )
    ])

    # 设置布局
    fig.update_layout(
        title=f"{symbol} 股票 K 线图",
        xaxis_title="日期",
        yaxis_title="价格 (USD)",
        xaxis_rangeslider_visible=False,  # 关闭底部的范围滑动条
        template="plotly_dark",  # 主题风格
    )

    # 显示图表
    fig.show()

def main():
    plot_stock()


if __name__ == "__main__":
    main()