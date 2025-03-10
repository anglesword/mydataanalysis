import yfinance as yf
import ta
import pandas as pd
import numpy as np
from pandas import DataFrame
from scipy.signal import argrelextrema

'''
pyinstaller --onefile --icon=ico.ico --add-data "RAW_STOCKES_LIST.xls;." high.py
打包为exe文件命令：
1. 首先使用 PyInstaller 生成默认的 .spec 文件：
    pyinstaller your_script.py
   这会生成一个 your_script.spec 文件和一个 dist/ 目录。
2. 编辑 your_script.spec 文件，在 datas 列表中加入你需要打包的额外文件。例如，如果你有一个 data.txt 文件需要一起打包，可以修改 spec 文件：


pyinstaller --onefile --icon=ico.ico --add-data "RAW_STOCKS_LIST.xls;." high.py
注意：打包的文件名后必须加入---- ;.
'''

# 创建结果文件
def open_file(filename : str, type : str):
    return open(filename, type)

# 读取股票列表，获取股票代码
def list_stocks_from_xls(filename : str) -> list[str]:
    df = pd.read_excel(filename, sheet_name=0)
    num = df['NO'].values.tolist()
    return num

# 获取指定股票数据
def get_stock_data(symbol : str, period="12mo", interval="1d") -> DataFrame:
    stock = yf.Ticker(symbol)
    df = stock.history(period=period, interval=interval)
    return df

# BB_lower 价格支撑和阻力位参数： 权重->0.2
'''
1. 价格在支撑：价格<=下布林带，值为1（买入信号），否则为0
2. 价格在阻力：价格>=上布林带，值为1（卖出信号), 否则为0
'''
def support_score(symbol : str, df : DataFrame, file_obj) -> list[int]:
    score = []
    # 计算布林带
    df['MB'] = df['Close'].rolling(window=20).mean()  # 中轨（20日均线）
    df['STD'] = df['Close'].rolling(window=20).std()  # 标准差
    df['UB'] = df['MB'] + (2 * df['STD'])  # 上轨
    df['LB'] = df['MB'] - (2 * df['STD'])  # 下轨
    # 获取最近一天的数据
    latest_data = df.iloc[-1]
    close_price = float.__round__(latest_data['Close'], 2)
    ub = float.__round__(latest_data['UB'], 2)
    lb = float.__round__(latest_data['LB'], 2)
    # 价格在支撑
    if close_price <= lb:
        score.append(1)
    else:
        score.append(0)
    # 价格在阻力
    if close_price >= ub:
        score.append(1)
    else:
        score.append(0)
    file_obj.write(f"股票代码：{symbol}, 价格支撑和阻力位参数 support_score={score}, 收盘价：{close_price}, 布林上轨：{ub}, 布林下轨：{lb}\n")
    print(f"股票代码：{symbol}, 价格支撑和阻力位参数 support_score={score}, 收盘价：{close_price}, 布林上轨：{ub}, 布林下轨：{lb}")
    return score


# RSI_buy RSI超买和超卖： 权重->0.2
'''
1. RSI<30, 值为1（买入信号），否则为0
2. RSI>70，值为1（卖出信号），否则为0
'''
def rsi_score(symbol : str, df : DataFrame, file_obj) -> list[int]:
    score = []
    # 当下以14日的RSI为计算单位
    df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    latest = df.iloc[-1]
    # RSI<30, 值为1（买入信号），否则为0
    if latest['rsi'] < 30:
        score.append(1)
    else:
        score.append(0)
    # RSI>70，值为1（卖出信号），否则为0
    if latest['rsi'] > 70:
        score.append(1)
    else:
        score.append(0)

    file_obj.write(f"股票代码：{symbol}, RSI超买和超卖 rsi_score={score}, RSI值：{latest['rsi']:.2f}\n")
    print(
        f"股票代码：{symbol}, RSI超买和超卖 rsi_score={score}, RSI值：{latest['rsi']:.2f}")
    return score

# MA_cross 看涨（跌）趋势： 权重->0.3
'''
1. 50日均线>200日均线，值为1（买入信号），否则为0
2. 50日均线<200日均线，值为1（卖出信号），否则为0
'''
def cross_score(symbol : str, df : DataFrame, file_obj) -> list[int]:
    score = []
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    # 记录金叉信号
    df['Golden_Cross_50_200'] = detect_golden_cross(df, 'MA50', 'MA200')
    # 记录死叉信号
    df['Death_Cross_50_200'] = detect_death_cross(df, 'MA50', 'MA200')
    # 获取最新一天的数据
    latest_data = df.iloc[-1]
    # 50日均线>200日均线，值为1（买入信号），否则为0
    if not latest_data['Golden_Cross_50_200']:
        score.append(0)
    else:
        score.append(1)
    # 50日均线<200日均线，值为1（卖出信号），否则为0
    if not latest_data['Death_Cross_50_200']:
        score.append(0)
    else:
        score.append(1)
    file_obj.write(f"股票代码：{symbol}, 50日均线200日均线趋势 cross_score={score}, 金叉信号：{latest_data['Golden_Cross_50_200']}, 死叉信号：{latest_data['Death_Cross_50_200']}\n")
    print(
        f"股票代码：{symbol}, 50日均线200日均线趋势 cross_score={score}, 金叉信号：{latest_data['Golden_Cross_50_200']}, 死叉信号：{latest_data['Death_Cross_50_200']}")
    return score

# MACD_buy 正(负)向动能： 权重->0.2
'''
1. MACD线>信号线，值为1（买入信号），否则为0
2. MACD线<信号线，值为1（卖出信号），否则为0
'''
def macd_score(symbol : str, df : DataFrame, file_obj) -> list[int]:
    score = []
    # 计算MACD及信号线
    macd_object = ta.trend.MACD(df['Close'])
    df['MACD'] = macd_object.macd()
    df['MACD_signal'] = macd_object.macd_signal()
    # 获取最新一天的数据
    latest_data = df.iloc[-1]
    # MACD线>信号线，值为1（买入信号），否则为0
    if latest_data['MACD'] > latest_data['MACD_signal']:
        score.append(1)
    else:
        score.append(0)
    # MACD线<信号线，值为1（卖出信号），否则为0
    if latest_data['MACD'] < latest_data['MACD_signal']:
        score.append(1)
    else:
        score.append(0)
    file_obj.write(f"股票代码：{symbol}, MACD线信号线 macd_score={score}, MACD：{latest_data['MACD']}, MACD信号：{latest_data['MACD_signal']}\n")
    print(
        f"股票代码：{symbol}, MACD线信号线 macd_score={score}, MACD：{latest_data['MACD']}, MACD信号：{latest_data['MACD_signal']}")
    return score

# V_strength 高交易量：权重->0.1
'''
交易量>过去20天的平均交易量，值为1，否则为0
'''
def volume_score(symbol : str, df : DataFrame, file_obj) -> int:
    score = 0
    # 过去20天的平均交易量
    df["MA20"] = df["Volume"].rolling(window=20).mean()
    # 获取最新的成交量和均值
    latest = df.iloc[-1]
    if latest['Volume'] > latest['MA20']:
        score = 1
    file_obj.write(f"股票代码：{symbol}, 交易量 volume_score={score}, 过去20天的平均交易量：{latest['MA20']}, 当前交易量：{latest['Volume']}\n")
    print(
        f"股票代码：{symbol}, 交易量 volume_score={score}, 过去20天的平均交易量：{latest['MA20']}, 当前交易量：{latest['Volume']}")
    return score

# 最终得分：若评分>=0.7,则触发买入或卖出信号
def final_score(symbol : str, df : DataFrame, file_obj) -> list[float]:
    final = []
    # K线形态判断
    '''看涨'''
    isHammer = is_hammer(df, len(df) - 1)  # 判断是否看涨的锤头线
    isSun = is_bullish_sun(df, len(df) - 1) # 判断是否大阳线
    isEngulfing = is_bullish_engulfing(df, len(df) - 1)   # 是否看涨吞没线
    isMorning = is_morning_star(df) # 是否早晨之星
    isPiercing = is_piercing_pattern(df)# 刺透形态
    isGap = is_gap(df)# 跳空缺口
    isWhiteSoldiers = is_three_white_soldiers(df) # 三白兵 短期看涨
    isDouble = is_double_bottom(df) # 双底

    '''看跌'''
    isEvening = is_evening_star(df) # 判断是否黄昏之星
    isBearish = is_bearish_engulfing(df, len(df) - 1)    # 是否看跌吞没
    isHanging = is_hanging_man(df, len(df) - 1)    # 是否吊顶线
    isShooting = is_shooting_star(df)  # 长上影线阴线（Shooting Star） 射击之星
    isBearishMarubozu = is_bearish_marubozu(df)# 大阴线
    isBearishVariant = is_bearish_variant(df)# 两阴夹一阳
    isDoji = is_doji(df)# 十字星
    isGravestoneDoji = is_gravestone_doji(df)# 墓碑线
    isDark = is_dark_cloud_cover(df)# 乌云盖顶
    isBlackCrows = is_three_black_crows(df) # 三只乌鸦
    isHeadShoulders = is_head_and_shoulders_top(df) # 头顶肩

    file_obj.write(f"$$$$$$$$$$$$$$$$$$$${symbol}K线形态判断$$$$$$$$$$$$$$$$$$$$$$$\n")
    file_obj.write(f"$K线（看涨）形态：锤头线:{isHammer}, 大阳线:{isSun}, 看涨吞没线:{isEngulfing}, 早晨之星:{isMorning}, "
               f"刺透形态:{isPiercing}, 向上跳空:{isGap[0]}, 三白兵:{isWhiteSoldiers}, 双底:{isDouble} $\n")
    file_obj.write(f"$K线（看跌）形态：黄昏之星:{isEvening}, 看跌吞没:{isBearish}, 吊顶线:{isHanging}, "
               f"长上影线阴线（Shooting Star） 射击之星:{isShooting}, 大阴线:{isBearishMarubozu},两阴夹一阳:{isBearishVariant},"
               f"十字星:{isDoji}, 墓碑线:{isGravestoneDoji}, 乌云盖顶:{isDark}, 向下跳空：{isGap[1]}, 三只乌鸦:{isBlackCrows}, 头顶肩:{isHeadShoulders} $\n")
    file_obj.write(f"$$$$$$$$$$$$$$$$$$$$$END$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")

    # 辅助指标分数判断
    support = support_score(symbol, df, file_obj)
    rsi = rsi_score(symbol, df, file_obj)
    cross = cross_score(symbol, df, file_obj)
    ma = macd_score(symbol, df, file_obj)
    vol = volume_score(symbol, df, file_obj)
    buy = 0.2 * support[0] + 0.2 * rsi[0] + 0.3 * cross[0] + 0.2 * ma[0] + 0.1 * vol
    sell = 0.2 * support[1] + 0.2 * rsi[1] + 0.3 * cross[1] + 0.2 * ma[1] + 0.1 * vol

    file_obj.write(f"&&&&&&&&&&买入卖出信号&&&&&&&&&&&&&&&&&&&&&&&&&\n")
    file_obj.write(f"&股票代码：{symbol}, 买入信号得分：{buy}, 卖出信号得分：{sell} &\n")
    file_obj.write(f"&&&&&&&&&&&&&&&&&END&&&&&&&&&&&&&&&&&&&&&&&&&\n")

    return final


# ------------------K线形态判断---------------------------------------------------
# 判断K线形态是否“早晨之星” -> 看涨
def is_morning_star(df : DataFrame, day=5, extra=False) -> bool:
    if day < 5:
        return False
    # 获取三天的 K 线数据
    open1, close1 = df['Open'].iloc[day - 2], df['Close'].iloc[day - 2]  # 第一天
    open2, close2, high2, low2 = df['Open'].iloc[day - 1], df['Close'].iloc[day - 1], df['High'].iloc[day - 1], \
            df['Low'].iloc[day - 1]  # 第二天
    open3, close3 = df['Open'].iloc[day], df['Close'].iloc[day]  # 第三天

    # 计算短期趋势（前5天是否处于下跌趋势）
    past_5_days = df['Close'].iloc[day - 5:day]  # 过去5天的收盘价
    downtrend = past_5_days.is_monotonic_decreasing  # 判断是否单调递减

    # 早晨之星形态条件
    cond1 = close1 < open1  # 第一日为大阴线
    cond2 = min(open2, close2) > close1  # 第二日低开
    cond3 = abs(close2 - open2) < (close1 - open1) * 0.3  # 第二日实体较小（小K线或十字星）
    cond4 = close3 > open3  # 第三日为大阳线
    cond5 = close3 > (open1 + close1) / 2  # 第三日收盘价高于第一日实体的一半
    cond6 = downtrend  # 额外条件：前5天是下跌趋势

    if not extra:
        return cond1 and cond2 and cond3 and cond4 and cond5
    else:
        return cond1 and cond2 and cond3 and cond4 and cond5 and cond6

# 计算黄昏之星形态 -> 看跌
def is_evening_star(df : DataFrame, day=5) -> bool:
    """ 检测是否为黄昏之星形态，并判断是否出现在上涨趋势顶部 """
    if day < 5:  # 需要至少5天数据
        return False

        # 获取三天的 K 线数据
    open1, close1 = df['Open'].iloc[day - 2], df['Close'].iloc[day - 2]  # 第一天
    open2, close2 = df['Open'].iloc[day - 1], df['Close'].iloc[day - 1]  # 第二天
    open3, close3 = df['Open'].iloc[day], df['Close'].iloc[day]  # 第三天

    # 计算短期趋势（前5天是否处于上涨趋势）
    past_5_days = df['Close'].iloc[day - 5:day]  # 过去5天的收盘价
    uptrend = past_5_days.is_monotonic_increasing  # 判断是否单调递增

    # 黄昏之星形态条件
    cond1 = close1 > open1  # 第一日为大阳线
    cond2 = min(open2, close2) > close1  # 第二日高开
    cond3 = abs(close2 - open2) < (close1 - open1) * 0.3  # 第二日实体较小
    cond4 = close3 < open3  # 第三日为大阴线
    cond5 = close3 < (open1 + close1) / 2  # 第三日收盘价低于第一日实体的一半
    cond6 = uptrend  # 额外条件：前5天是上涨趋势

    return cond1 and cond2 and cond3 and cond4 and cond5 and cond6

# 计算均线金叉
def detect_golden_cross(df : DataFrame, short_ma : str, long_ma : str) -> bool:
    """检测短期均线上穿长期均线（金叉）"""
    return (df[short_ma] > df[long_ma]) & (df[short_ma].shift(1) <= df[long_ma].shift(1))

# 计算未突破的金叉
def golden_cross_not_confirmed(df : DataFrame, short_ma : str, long_ma : str) -> bool:
    """ 金叉形成后短期均线仍未突破长期均线 """
    cross_signal = detect_golden_cross(df, short_ma, long_ma)
    return cross_signal & (df[short_ma] < df[long_ma])  # 短期均线仍低于长期均线

# 计算均线死叉
def detect_death_cross(df : DataFrame, short_ma : str, long_ma : str) -> bool:
    """检测短期均线上穿长期均线（金叉）"""
    return (df[short_ma] < df[long_ma]) & (df[short_ma].shift(1) >= df[long_ma].shift(1))

# 计算未突破的死叉
def death_cross_not_confirmed(df : DataFrame, short_ma : str, long_ma : str) -> bool:
    """ 金叉形成后短期均线仍未突破长期均线 """
    cross_signal = detect_golden_cross(df, short_ma, long_ma)
    return cross_signal & (df[short_ma] > df[long_ma])  # 短期均线仍低于长期均线


# 定义看涨吞没形态的条件-》看涨
'''
看涨吞没的条件：
第一根K线：必须是阴线（即收盘价低于开盘价）。

第二根K线：必须是阳线（即收盘价高于开盘价）。

第二根K线的开盘价低于第一根K线的收盘价，且第二根K线的收盘价高于第一根K线的开盘价。

第二根K线完全吞没第一根K线的实体，即第二根K线的实体范围完全覆盖第一根K线的实体范围。
'''
def is_bullish_engulfing(df, i):
    # 获取前一天和当天的K线数据
    open_price1 = df['Open'].iloc[i - 1]
    close_price1 = df['Close'].iloc[i - 1]
    open_price2 = df['Open'].iloc[i]
    close_price2 = df['Close'].iloc[i]

    # 看涨吞没的条件
    if close_price1 < open_price1 and close_price2 > open_price2:  # 第一根K线是阴线，第二根K线是阳线
        if open_price2 < close_price1 and close_price2 > open_price1:  # 第二根K线完全覆盖第一根K线的实体
            return True
    return False

# 定义大阳线的条件-》看涨
def is_bullish_sun(df : DataFrame, i : int) -> bool:
    open_price = df['Open'].iloc[i]
    close_price = df['Close'].iloc[i]
    high_price = df['High'].iloc[i]
    low_price = df['Low'].iloc[i]

    # 计算实体长度
    body_length = abs(close_price - open_price)
    # 计算当天的最高价与收盘价之间的差距
    upper_shadow = high_price - close_price

    # 大阳线的条件
    if close_price > open_price and body_length > (high_price - low_price) * 0.5 and upper_shadow < body_length:
        return True
    return False

# 定义锤头线的条件-》看涨
'''
参数i表示：
    len(df) - 1  表示 DataFrame 的最后一行的索引，即最近一天的交易数据
    len(df) - 2  代表 倒数第二行的索引，即 前一天的数据。
'''

def is_hammer(df : DataFrame, i : int) -> bool:
    open_price = df['Open'].iloc[i]
    close_price = df['Close'].iloc[i]
    high_price = df['High'].iloc[i]
    low_price = df['Low'].iloc[i]

    # 计算实体长度
    body_length = abs(close_price - open_price)
    # 计算上下影线长度
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    # 锤头线的条件
    if close_price > open_price:
        if (high_price - low_price) * 0.3 > body_length > upper_shadow and lower_shadow > body_length * 2:
            return True
    return False


# 定义吊颈线的条件 -> 看跌
'''
阴线：Close < Open，即当日是阴线。

下影线：(Low - min(Open, Close)) > 2 * (Open - Close)，下影线大于实体的两倍。

上影线：(High - max(Open, Close)) < (Open - Close)，上影线小于实体的大小。
'''
def is_hanging_man(df, i):
    open_price = df['Open'].iloc[i]
    close_price = df['Close'].iloc[i]
    high_price = df['High'].iloc[i]
    low_price = df['Low'].iloc[i]

    # 计算实体长度
    body_length = abs(close_price - open_price)
    # 计算上下影线长度
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price

    # 吊颈线的条件
    if close_price < open_price:  # 阴线
        if lower_shadow > body_length * 2 and upper_shadow < body_length:
            return True
    return False


# 定义看跌吞没的条件 -> 看跌
'''
第二天是阴线：Close < Open，即第二天收盘价低于开盘价。

第二天的开盘价高于第一天的收盘价，且第二天的收盘价低于第一天的开盘价：即第二天的阴线实体完全覆盖第一天的阳线。
'''
def is_bearish_engulfing(df, i):
    open_price_today = df['Open'].iloc[i]
    close_price_today = df['Close'].iloc[i]
    open_price_yesterday = df['Open'].iloc[i - 1]
    close_price_yesterday = df['Close'].iloc[i - 1]

    # 确保第二天是阴线，第一天是阳线
    if close_price_today < open_price_today and close_price_yesterday > open_price_yesterday:
        # 检查第二天是否完全覆盖第一天的实体
        if open_price_today > close_price_yesterday and close_price_today < open_price_yesterday:
            return True
    return False

# 长上影线阴线（Shooting Star） 射击之星
'''
长上影线阴线（Shooting Star，射击之星）**是一种常见的 K 线形态，通常出现在上升趋势的顶部，可能预示着市场即将反转向下
'''
def is_shooting_star(df : DataFrame) -> bool:
    # 计算上影线、下影线、实体大小
    df['Upper Shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['Lower Shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    df['Body'] = abs(df['Close'] - df['Open'])
    # 识别 Shooting Star 形态
    df['Shooting Star'] = (
            (df['Upper Shadow'] >= 2 * df['Body']) &  # 上影线至少是实体的2倍
            (df['Lower Shadow'] < df['Body']) &  # 下影线较短
            (df['Close'] < df['Open'])  # 收盘价低于开盘价（阴线）
    )
    # 获取数据
    latest = df.iloc[-1]
    print(f"长上影线阴线（Shooting Star） 射击之星:{latest['Shooting Star']}")
    return latest['Shooting Star']

# 大阴线（Bearish Marubozu）
'''
大阴线（Bearish Marubozu） 是技术分析中的一种强烈看跌的 K 线形态，表示卖方完全占据市场主导地位，通常出现在下跌趋势的开始或延续阶段。
'''
def is_bearish_marubozu(df : DataFrame) -> bool:
    # 计算实体部分、上影线和下影线
    df['Body'] = abs(df['Close'] - df['Open'])  # 实体部分
    df['Upper Shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)  # 上影线
    df['Lower Shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']  # 下影线

    # 识别 Bearish Marubozu 形态
    df['Bearish Marubozu'] = (
            (df['Close'] < df['Open']) &  # 阴线（收盘价 < 开盘价）
            (df['Upper Shadow'] <= df['Body'] * 0.1) &  # 上影线几乎没有（小于实体的10%）
            (df['Lower Shadow'] <= df['Body'] * 0.1)  # 下影线几乎没有（小于实体的10%）
    )
    # 获取数据
    latest = df.iloc[-1]
    print(f"大阴线:{latest['Bearish Marubozu']}")
    return latest['Bearish Marubozu']

# 两阴夹一阳（Bearish Three-Line Strike Variant）
'''
反弹失败，空头主导，短期看跌
'''
def is_bearish_variant(df : DataFrame) -> bool:
    # 计算每根K线的类型（阴线或阳线）
    df['Candle Type'] = df.apply(lambda row: 'Bullish' if row['Close'] > row['Open'] else 'Bearish', axis=1)

    # 识别 "两阴夹一阳" 形态
    df['Bearish Three-Line Strike Variant'] = (
            (df['Candle Type'].shift(0) == 'Bearish') &  # 第一根阴线
            (df['Candle Type'].shift(1) == 'Bullish') &  # 第二根阳线
            (df['Candle Type'].shift(2) == 'Bearish') &  # 第三根阴线
            (df['Close'].shift(0) < df['Close'].shift(2))  # 第三根阴线收盘价低于第一根阴线收盘价
    )
    # 获取数据
    latest = df.iloc[-1]
    print(f"两阴夹一阳:{latest['Bearish Three-Line Strike Variant']}")
    return latest['Bearish Three-Line Strike Variant']

# 十字星（Doji）
'''
十字星（Doji） 是一种重要的 K线形态，表示市场买卖力量均衡，可能预示着趋势反转或停滞。
在技术分析中，Doji 形态通常出现在趋势的顶部或底部，反映市场的不确定性。
多空力量平衡，可能是反转或延续信号，需结合前趋势判断：
        上涨后：顶部反转（看跌）。
	◦	下跌后：底部反转（看涨）。
	•	成交量: 高成交量增强信号。
'''
def is_doji(df : DataFrame) -> bool:
    # 计算实体部分（开盘价 - 收盘价的绝对值）
    df['Body'] = abs(df['Close'] - df['Open'])

    # 计算波动范围（最高价 - 最低价）
    df['Range'] = df['High'] - df['Low']

    # 识别 Doji 形态
    df['Doji'] = (df['Body'] <= df['Range'] * 0.1)  # 实体部分小于总波动的 10%

    # 获取数据
    latest = df.iloc[-1]
    print(f"十字星:{latest['Doji']}")
    return latest['Doji']

# 墓碑线（Gravestone Doji）
'''
墓碑线（Gravestone Doji） 是一种 看跌反转K线形态，常出现在 上升趋势的顶部，表示市场尝试上涨但最终被空方压制，收盘价接近开盘价的低点，预示可能的下跌。
	•	含义: 多头冲高后被空头打压至低位，强烈看跌信号。
	•	成交量: 高成交量强化顶部信号。
'''
def is_gravestone_doji(df : DataFrame) -> bool:
    # 计算K线实体部分（开盘价 - 收盘价的绝对值）
    df['Body'] = abs(df['Close'] - df['Open'])

    # 计算影线部分
    df['Upper Shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)  # 上影线 = 最高价 - 最大(开盘价, 收盘价)
    df['Lower Shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']  # 下影线 = 最小(开盘价, 收盘价) - 最低价

    # 识别墓碑线（Gravestone Doji）
    df['Gravestone Doji'] = (
            (df['Body'] <= df['High'] * 0.02) &  # 实体部分接近 0
            (df['Upper Shadow'] >= df['Body'] * 5) &  # 长上影线
            (df['Lower Shadow'] <= df['Body'] * 0.5)  # 无下影线或极短
    )
    # 获取数据
    latest = df.iloc[-1]
    print(f"墓碑线:{latest['Gravestone Doji']}")
    return latest['Gravestone Doji']

# 乌云盖顶（Dark Cloud Cover）
'''
乌云盖顶（Dark Cloud Cover） 是 看跌反转 的 K 线形态，通常出现在 上升趋势的顶部，表明市场买盘减弱，空头开始主导市场。
    •	含义: 空头反攻，短期看跌，可能引发回调。
	•	成交量: 第二日放量更强。
'''
def is_dark_cloud_cover(df : DataFrame) -> bool:
    # 计算前一天的K线数据
    df['Prev Close'] = df['Close'].shift(1)
    df['Prev High'] = df['High'].shift(1)
    df['Prev Open'] = df['Open'].shift(1)

    # 计算K线实体部分
    df['Prev Body'] = df['Prev Close'] - df['Prev Open']  # 前一天的实体
    df['Curr Body'] = df['Close'] - df['Open']  # 当天的实体

    # 计算前一天实体中点
    df['Prev Midpoint'] = df['Prev Open'] + df['Prev Body'] / 2  # 实体中点

    # **标准乌云盖顶**
    df['Dark Cloud Cover (Strict)'] = (
            (df['Open'] > df['Prev High']) &  # **严格要求：当天高开**
            (df['Close'] < df['Prev Midpoint']) &  # 收盘跌破前一天实体的一半
            (df['Curr Body'] < 0)  # 当天是阴线
    )

    # **宽松版乌云盖顶**
    df['Dark Cloud Cover (Loose)'] = (
            (df['Open'] > df['Prev Close']) &  # **宽松版：当天开盘价高于前一天收盘价**
            (df['Close'] < df['Prev Midpoint']) &  # 收盘跌破前一天实体的一半
            (df['Curr Body'] < 0)  # 当天是阴线
    )

    # 获取数据
    latest = df.iloc[-1]
    print(f"乌云盖顶:{latest['Dark Cloud Cover (Strict)']}")
    return latest['Dark Cloud Cover (Strict)']

# 刺透形态（Piercing Pattern）
'''
刺透形态（Piercing Pattern） 是一种 看涨反转 的 K 线形态，通常出现在 下降趋势的底部，表示市场可能由空头转向多头。
	•	含义: 买盘反攻，短期看涨，可能反弹。
	•	成交量: 第二日放量更可靠。
'''
def is_piercing_pattern(df : DataFrame) -> bool:
    # 计算前一天的K线数据
    df['Prev Close'] = df['Close'].shift(1)
    df['Prev Open'] = df['Open'].shift(1)
    df['Prev Low'] = df['Low'].shift(1)

    # 计算K线实体部分
    df['Prev Body'] = df['Prev Close'] - df['Prev Open']  # 前一天的实体
    df['Curr Body'] = df['Close'] - df['Open']  # 当天的实体

    # 计算前一天实体的中点
    df['Prev Midpoint'] = df['Prev Open'] + df['Prev Body'] / 2  # 实体中点

    # 识别刺透形态（Piercing Pattern）
    df['Piercing Pattern'] = (
            (df['Prev Body'] < 0) &  # 前一天必须是阴线
            (df['Curr Body'] > 0) &  # 当天必须是阳线
            (df['Open'] < df['Prev Low']) &  # 当天低开
            (df['Close'] > df['Prev Midpoint'])  # 收盘价高于前一天实体中点
    )
    # 获取数据
    latest = df.iloc[-1]
    print(f"刺透形态:{latest['Piercing Pattern']}")
    return latest['Piercing Pattern']

# 跳空缺口（Gap Up/Down）
'''
跳空缺口（Gap） 是指 当前K线的最低价（或最高价）与前一K线的最高价（或最低价）之间出现价格断层，即市场未发生交易而直接跳开。
    1️⃣ 向上跳空（Gap Up）
    当前K线的 最低价高于前一K线的最高价。
    
    市场买盘强劲，可能预示上涨。
    
    2️⃣ 向下跳空（Gap Down）
    当前K线的 最高价低于前一K线的最低价。
    
    市场卖盘强劲，可能预示下跌。
    ◦	跳空高开后回落（阴线）：看跌，顶部压力。
	◦	跳空低开后反弹（阳线）：看涨，底部支撑。
	•	成交量: 高成交量确认趋势。
'''
def is_gap(df : DataFrame) -> list[bool]:
    # 计算前一天的K线数据
    df['Prev High'] = df['High'].shift(1)
    df['Prev Low'] = df['Low'].shift(1)

    # 识别 **向上跳空（Gap Up）**
    df['Gap Up'] = df['Low'] > df['Prev High']

    # 识别 **向下跳空（Gap Down）**
    df['Gap Down'] = df['High'] < df['Prev Low']
    # 获取数据
    latest = df.iloc[-1]
    print(f"跳空缺口->向上跳空:{latest['Gap Up']}, 向下跳空->{latest['Gap Down']}")
    result = [latest['Gap Up'], latest['Gap Down']]
    return result

# 三只乌鸦（Three Black Crows）
'''
	•	特征: 连续三根阴线，每日收盘低于前日低点，出现在上升趋势后。
	•	含义: 强烈卖压，短期持续下跌。
	•	成交量: 逐步放大更强。
成交量放大（可选）：
如果 成交量增加，则该形态更具参考价值。
'''
def is_three_black_crows(df : DataFrame) -> bool:
    # 计算 K 线实体
    df['Body1'] = df['Close'].shift(1) - df['Open'].shift(1)  # 前一天实体
    df['Body2'] = df['Close'].shift(2) - df['Open'].shift(2)  # 前二天实体
    df['Body3'] = df['Close'].shift(3) - df['Open'].shift(3)  # 前三天实体

    # 计算三天的开盘和收盘价
    df['Open1'] = df['Open'].shift(1)
    df['Open2'] = df['Open'].shift(2)
    df['Open3'] = df['Open'].shift(3)

    df['Close1'] = df['Close'].shift(1)
    df['Close2'] = df['Close'].shift(2)
    df['Close3'] = df['Close'].shift(3)

    # 计算前 5 天的趋势（判断是否为上涨趋势）
    df['Trend'] = df['Close'].shift(5) < df['Close']

    # 计算移动平均线
    df['SMA5'] = df['Close'].rolling(window=5).mean()  # 5 日均线
    df['SMA10'] = df['Close'].rolling(window=10).mean()  # 10 日均线

    # 识别 **三只乌鸦（Three Black Crows）**
    df['Three Black Crows'] = (
            (df['Body3'] < 0) & (df['Body2'] < 0) & (df['Body1'] < 0) &  # 连续 3 天阴线
            (df['Open2'] < df['Close3']) & (df['Open1'] < df['Close2']) &  # 开盘价在前一天实体内
            (df['Close2'] < df['Close3']) & (df['Close1'] < df['Close2']) &  # 收盘价逐步走低
            (df['Trend']) &  # 前期为上升趋势
            (df['SMA5'] > df['SMA10'])  # 短期均线 > 长期均线（确认上涨趋势）
    )
    # 获取数据
    latest = df.iloc[-1]
    print(f"三只乌鸦:{latest['Three Black Crows']}")
    return latest['Three Black Crows']

# 三白兵（Three White Soldiers）
'''
    特征: 连续三根阳线，每日收盘高于前日高点，出现在下跌趋势后。
	•	含义: 买盘持续增强，短期上涨。
	•	成交量: 逐步放大更可靠。
'''
def is_three_white_soldiers(df : DataFrame) -> bool:
    # 🔹 计算 K 线形态
    df['Green1'] = df['Close'] > df['Open']  # 第 1 天阳线
    df['Green2'] = df['Close'].shift(1) > df['Open'].shift(1)  # 第 2 天阳线
    df['Green3'] = df['Close'].shift(2) > df['Open'].shift(2)  # 第 3 天阳线

    # 🔹 确保每根 K 线的开盘价在前一天实体部分之内
    df['Open2 in Body1'] = df['Open'].shift(1) > df['Open'].shift(2)  # 第 2 天开盘 > 第 1 天开盘
    df['Open3 in Body2'] = df['Open'] > df['Open'].shift(1)  # 第 3 天开盘 > 第 2 天开盘

    # 🔹 确保收盘价接近最高价（上影线短）
    df['Small Upper Shadow1'] = (df['High'] - df['Close']) < (df['Close'] - df['Open']) * 0.2
    df['Small Upper Shadow2'] = (df['High'].shift(1) - df['Close'].shift(1)) < (
                df['Close'].shift(1) - df['Open'].shift(1)) * 0.2
    df['Small Upper Shadow3'] = (df['High'].shift(2) - df['Close'].shift(2)) < (
                df['Close'].shift(2) - df['Open'].shift(2)) * 0.2

    # 🔹 形态必须出现在下降趋势后
    df['Downtrend'] = df['Close'].shift(5) > df['Close']

    # 🔹 计算三白兵信号
    df['Three White Soldiers'] = (
            df['Green1'] & df['Green2'] & df['Green3'] &  # 三连阳
            df['Open2 in Body1'] & df['Open3 in Body2'] &  # 开盘价在前日实体部分内
            df['Small Upper Shadow1'] & df['Small Upper Shadow2'] & df['Small Upper Shadow3'] &  # 上影线短
            df['Downtrend']  # 之前是下跌趋势
    )
    # 获取数据
    latest = df.iloc[-1]
    print(f"三白兵:{latest['Three White Soldiers']}")
    return latest['Three White Soldiers']

# 头肩顶（Head and Shoulders Top）-> 短期看跌
'''
    通常出现在上升趋势的末端
	•	特征: 三段走势：左肩（阳线高点）、头（更高高点）、右肩（低于头的高点），颈线（两低点连线）跌破后确认。
	•	含义: 顶部反转，短期看跌，跌幅约头部到颈线的距离。
	•	成交量: 左肩和头放量，右肩缩量。
'''
def is_head_and_shoulders_top(df : DataFrame) -> bool:
    # 🔹 计算简单移动平均线（SMA）
    df['SMA5'] = df['Close'].rolling(window=5).mean()  # 5日简单移动平均线
    df['SMA20'] = df['Close'].rolling(window=20).mean()  # 20日简单移动平均线

    # 🔹 判断是否处于上升趋势
    # 如果 5日均线高于 20日均线，并且最近的价格也在上升趋势中，则认为是上升趋势
    in_uptrend = df['SMA5'].iloc[-1] > df['SMA20'].iloc[-1]  # 当前 SMA5 大于 SMA20
    if not in_uptrend:
        print("当前未处于上升趋势中...")
        return False
    else:
        # 🔹 计算局部极大值（局部高点）
        local_max_idx = argrelextrema(df['High'].values, np.greater, order=5)[0]  # 获取索引位置
        local_max_dates = df.index[local_max_idx]  # 转换为日期索引

        # 🔹 赋值局部极大值
        df.loc[local_max_dates, 'Local Max'] = df.loc[local_max_dates, 'High']

        # 🔹 识别头肩顶模式（左肩、头部、右肩）
        peaks = df.dropna(subset=['Local Max'])  # 去掉缺失值的行，获取有效的局部极大值
        if len(peaks) >= 3:
            for i in range(1, len(peaks) - 1):
                left_shoulder = peaks.iloc[i - 1]
                head = peaks.iloc[i]
                right_shoulder = peaks.iloc[i + 1]

                # 条件：头部高于左肩和右肩，左右肩高点相近
                if (head['High'] > left_shoulder['High']) and (head['High'] > right_shoulder['High']) and \
                        (abs(left_shoulder['High'] - right_shoulder['High']) / left_shoulder['High'] < 0.05):

                    # 计算颈线（连接左肩和右肩回落点）
                    neckline_level = (left_shoulder['Low'] + right_shoulder['Low']) / 2

                    # 确保价格跌破颈线
                    if df['Close'].iloc[-1] < neckline_level:
                        df['Head and Shoulders'] = df.index.isin([left_shoulder.name, head.name, right_shoulder.name])
                        print(f"⚠️  发现头肩顶信号！可能出现下跌趋势。")
                        return True

    return False

# 双底（Double Bottom） -> 短期看涨
'''
    •	特征: 两个低点（W形），颈线（中间高点）突破后确认，出现在下跌趋势后。
	•	含义: 底部反转，短期看涨，涨幅约底部到颈线的距离。
	•	成交量: 第二个底放量更强。
'''
def is_double_bottom(df : DataFrame) -> bool:
    # 🔹 计算局部极小值（局部低点）
    # 🔹 计算局部极大值（局部高点）
    local_min_idx = argrelextrema(df['Low'].values, np.greater, order=5)[0]  # 获取索引位置
    local_min_dates = df.index[local_min_idx]  # 转换为日期索引

    # 🔹 赋值局部极大值
    df.loc[local_min_dates, 'Local Min'] = df.loc[local_min_dates, 'Low']

    # 🔹 找出双底模式（两个相近的低点）
    bottoms = df.dropna(subset=['Local Min'])

    if len(bottoms) >= 2:
        for i in range(1, len(bottoms)):
            first_bottom = bottoms.iloc[i - 1]
            second_bottom = bottoms.iloc[i]

            # 条件：两个低点相近（误差不超过 5%）
            if abs(first_bottom['Low'] - second_bottom['Low']) / first_bottom['Low'] < 0.05:

                # 计算颈线（两个底部之间的最高点）
                neckline_level = df.loc[first_bottom.name:second_bottom.name, 'High'].max()

                # 确保价格突破颈线
                if df['Close'].iloc[-1] > neckline_level:
                    df['Double Bottom'] = df.index.isin([first_bottom.name, second_bottom.name])
                    print(f"✅  发现双底信号！可能出现上涨趋势。")
                    return True

    return False

# 处理Excel文件中定义的股票代码
def deal_from_excel():
    stocks = list_stocks_from_xls("RAW_STOCKES_LIST.xls")
    file_obj = open_file('result.txt', 'w')
    #df = get_stock_data("PPL.TO")
    #print(df)

    for name in stocks:
        df = get_stock_data(name)
        if df is None or len(df)==0:
            file_obj.write(f"--------------{name}无数据-----------------------\n")
            continue
        file_obj.write(f"*******************{name}股票数据分析*********************\n")
        final_score(name, df, file_obj)
        file_obj.write(f"********************************************************\n")
        file_obj.write(f"\n")

    file_obj.close()

def test_k_pattern():
    stocks = list_stocks_from_xls("RAW_STOCKES_LIST.xls")
    for name in stocks:
        df = get_stock_data(name)
        # is_shooting_star(df)
        # is_bearish_marubozu(df)
        # is_bearish_variant(df)
        # is_doji(df)
        # is_gravestone_doji(df)
        # is_dark_cloud_cover(df)
        # is_piercing_pattern(df)
        # is_gap(df)
        is_three_black_crows(df)
        is_three_white_soldiers(df)
        is_head_and_shoulders_top(df)
        is_double_bottom(df)
        break

def main() -> None:
    deal_from_excel()
    # test_k_pattern()


if __name__ == "__main__":
    main()