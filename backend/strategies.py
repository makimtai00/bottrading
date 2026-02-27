import pandas as pd
import numpy as np

class StrategyManager:
    """
    Chứa logic các hệ thống giao dịch Scalping
    """
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def moving_average_crossover(short_prices: pd.Series, long_prices: pd.Series) -> int:
        """
        Hệ thống MA Cross. Trả về 1 (Buy), -1 (Sell), 0 (Neutral)
        """
        if short_prices.iloc[-1] > long_prices.iloc[-1] and short_prices.iloc[-2] <= long_prices.iloc[-2]:
            return 1
        elif short_prices.iloc[-1] < long_prices.iloc[-1] and short_prices.iloc[-2] >= long_prices.iloc[-2]:
            return -1
        return 0
        
    @staticmethod
    def evaluate_strategies(df: pd.DataFrame) -> dict:
        """
        Đánh giá nhanh tình trạng hiện tại của nhiều chiến dịch
        """
        if len(df) < 50:
            return {"status": "insufficient_data"}
            
        close_prices = df['close']
        
        # 1. RSI
        rsi = StrategyManager.calculate_rsi(close_prices)
        current_rsi = rsi.iloc[-1]
        
        rsi_signal = "Neutral"
        if current_rsi < 30:
            rsi_signal = "Buy (Oversold)"
        elif current_rsi > 70:
            rsi_signal = "Sell (Overbought)"
            
        # 2. EMA
        ema9 = close_prices.ewm(span=9, adjust=False).mean()
        ema21 = close_prices.ewm(span=21, adjust=False).mean()
        
        ema_signal_val = StrategyManager.moving_average_crossover(ema9, ema21)
        ema_signal = "Neutral"
        if ema_signal_val == 1:
            ema_signal = "Buy (Bullish Cross)"
        elif ema_signal_val == -1:
             ema_signal = "Sell (Bearish Cross)"
             
        # Tổng hợp
        return {
            "RSI": {"value": round(current_rsi, 2), "signal": rsi_signal},
            "EMA_Cross": {"signal": ema_signal}
        }

strategy_manager = StrategyManager()
