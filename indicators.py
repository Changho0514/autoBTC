from ta.utils import dropna
from ta.volatility import BollingerBands
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.trend import MACD


def add_indicators(df_day, df_hour):

    # NaN 값 제거
    df_day = dropna(df_day)
    df_hour = dropna(df_hour)

    # Bollinger Bands (일봉)
    indicator_bb_day = BollingerBands(close=df_day["close"], window=20, window_dev=2)
    df_day['bb_bbm'] = indicator_bb_day.bollinger_mavg()  # 중앙값 (Moving Average)
    df_day['bb_bbh'] = indicator_bb_day.bollinger_hband()  # 상단 밴드
    df_day['bb_bbl'] = indicator_bb_day.bollinger_lband()  # 하단 밴드
    df_day['bb_bbw'] = indicator_bb_day.bollinger_wband()  # 밴드 폭

    # Bollinger Bands (시간봉)
    indicator_bb_hour = BollingerBands(close=df_hour["close"], window=20, window_dev=2)
    df_hour['bb_bbm'] = indicator_bb_hour.bollinger_mavg()
    df_hour['bb_bbh'] = indicator_bb_hour.bollinger_hband()
    df_hour['bb_bbl'] = indicator_bb_hour.bollinger_lband()
    df_hour['bb_bbw'] = indicator_bb_hour.bollinger_wband()

    # Simple Moving Average (SMA) 추가 (일봉)
    sma_indicator_day = SMAIndicator(close=df_day["close"], window=14)
    df_day['sma_14'] = sma_indicator_day.sma_indicator()

    # Exponential Moving Average (EMA) 추가 (일봉)
    ema_indicator_day = EMAIndicator(close=df_day["close"], window=14)
    df_day['ema_14'] = ema_indicator_day.ema_indicator()

    # Simple Moving Average (SMA) 추가 (시간봉)
    sma_indicator_hour = SMAIndicator(close=df_hour["close"], window=14)
    df_hour['sma_14'] = sma_indicator_hour.sma_indicator()

    # Exponential Moving Average (EMA) 추가 (시간봉)
    ema_indicator_hour = EMAIndicator(close=df_hour["close"], window=14)
    df_hour['ema_14'] = ema_indicator_hour.ema_indicator()

    # RSI (일봉)
    rsi_day = RSIIndicator(close=df_day["close"], window=14)
    df_day['rsi_14'] = rsi_day.rsi()

    # RSI (시간봉)
    rsi_hour = RSIIndicator(close=df_hour["close"], window=14)
    df_hour['rsi_14'] = rsi_hour.rsi()

    # MACD (일봉)
    macd_day = MACD(close=df_day["close"])
    df_day['macd'] = macd_day.macd()
    df_day['macd_signal'] = macd_day.macd_signal()
    df_day['macd_diff'] = macd_day.macd_diff()

    # MACD (시간봉)
    macd_hour = MACD(close=df_hour["close"])
    df_hour['macd'] = macd_hour.macd()
    df_hour['macd_signal'] = macd_hour.macd_signal()
    df_hour['macd_diff'] = macd_hour.macd_diff()

    return df_day, df_hour
