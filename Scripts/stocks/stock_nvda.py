import itertools

import plotly.graph_objs as go
import yfinance as yf
import pandas as pd

from plotly.subplots import make_subplots


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
        # xaxis_rangeslider_visible=False,  # 关闭底部的范围滑动条
        template="plotly_dark",  # 主题风格
        height=700
    )

    # 显示图表
    fig.show()


# 成交量+K线
def plot_stock_same_layout() -> None:
    df = yf.download(symbol, start=start_date, end=end_date)
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index,  # 日期
            open=list(itertools.chain(*(df['Open'].values.tolist()))),  # 开盘价
            high=list(itertools.chain(*(df['High'].values.tolist()))),  # 最高价
            low=list(itertools.chain(*(df['Low'].values.tolist()))),  # 最低价
            close=list(itertools.chain(*(df['Close'].values.tolist()))),  # 收盘价
            increasing_line_color='green',  # 涨（收盘价高于开盘价）颜色
            decreasing_line_color='red',  # 跌（收盘价低于开盘价）颜色
            name = "K线"
        )
    )
    # 成交量
    fig.add_trace(go.Bar(
        x=df.index,
        y=list(itertools.chain(*df['Volume'].values.tolist())),
        name="成交量",
        marker=dict(color='blue', opacity=0.5),
        yaxis="y2"  # 必须绑定轴
    ))
    # 更新布局
    fig.update_layout(
        title=f"{symbol} K 线图 + 成交量",
        xaxis_title="日期",
        yaxis_title="价格",
        # 为绑定轴的成交量设定
        yaxis2=dict(
            title='成交量',
            overlaying='y',
            side='right'
        ),
        template="presentation",
        height=700,
        xaxis_rangeslider_visible = False
    )
    fig.show()

# 在同一个页面，不同的layout显示多个图形.
# 在 Plotly 中，可以使用 make_subplots() 在同一页面创建多个独立的图表（如 K 线图、柱状图、折线图等），
# 并通过 subplot_titles 分别命名不同的图表。
def plot_stock_different_layout() -> None:
    df = yf.download(symbol, start=start_date, end=end_date)

    # 创建 2 行 1 列的子图布局
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,  # 共享 X 轴
        vertical_spacing=0.1,  # 上下间距
        subplot_titles=("K 线图", "成交量")  # 子图标题
    )

    # **添加 K 线图**
    fig.add_trace(
        go.Candlestick(
            x=df.index,  # 日期
            open=list(itertools.chain(*(df['Open'].values.tolist()))),  # 开盘价
            high=list(itertools.chain(*(df['High'].values.tolist()))),  # 最高价
            low=list(itertools.chain(*(df['Low'].values.tolist()))),  # 最低价
            close=list(itertools.chain(*(df['Close'].values.tolist()))),  # 收盘价
            increasing_line_color='green',  # 涨（收盘价高于开盘价）颜色
            decreasing_line_color='red',  # 跌（收盘价低于开盘价）颜色
            name="K线"
        ), row=1, col=1  # **第一行**
    )

    # 成交量
    fig.add_trace(go.Bar(
        x=df.index,
        y=list(itertools.chain(*df['Volume'].values.tolist())),
        name="成交量",
        marker=dict(color='blue'),
        # yaxis="y2"  # 必须绑定轴
    ), row=2, col=1) # **第二行**

    # **更新布局**
    fig.update_layout(
        title="股票 K 线图 + 成交量",
        # xaxis_title="日期",
        xaxis2_title="日期",  # 共享 X 轴的标题
        yaxis_title="价格",
        yaxis2_title="成交量",
        showlegend=False,  # 关闭图例
        xaxis_rangeslider_visible=False,
        height=700  # 设置图表高度
    )

    fig.show()
    fig.write_html("../html/plot_nvda.html")

def main():
    # plot_stock()
    # plot_stock_same_layout()
    plot_stock_different_layout()


if __name__ == "__main__":
    main()