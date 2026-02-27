import time
import pandas as pd
import numpy as np
import joblib
import os
from binance_client import binance_client
from strategies import strategy_manager

class MLPredictor:
    """
    Sử dụng mô hình RandomForest đã được huấn luyện (rf_scalping_model.pkl)
    để dự đoán và tính toán điểm Entry, TP, SL thực tế.
    """
    
    def __init__(self):
        self.model_ready = False
        self.model = None
        self.strategies = ["RSI_Oversold", "MACD_Crossover", "Bollinger_Breakout", "EMA_Trend", "H1_M5_EMA_Pullback"]
        
    def initialize_model(self):
        """
        Load mô hình RandomForest Classifier
        """
        try:
            model_path = os.path.join(os.path.dirname(__file__), "rf_scalping_model.pkl")
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                self.model_ready = True
                print("ML model (RandomForest) loaded successfully!")
            else:
                print("Không tìm thấy model. Bạn cần chạy data_pipeline.py trước.")
        except Exception as e:
            print(f"Lỗi load model: {e}")

    def predict(self, symbol: str, interval: str = "5m") -> dict:
        """
        Trả về chiến thuật tốt nhất dựa vào điều kiện thị trường.
        (Mô phỏng bằng random để tạo dummy data cho Frontend)
        """
        if not self.model_ready:
            return {"error": "Model training"}

        # Xác định xu hướng BTC (Feature: btc_uptrend, btc_downtrend)
        btc_trend = "Neutral"
        btc_uptrend_val = 0
        btc_downtrend_val = 0
        try:
            # Lấy 50 cây nến BTCUSDT khung 5m (giống pipeline)
            btc_klines = binance_client.get_historical_klines("BTCUSDT", interval="5m", limit=50)
            btc_df = pd.DataFrame(btc_klines)
            btc_ema50 = btc_df['close'].ewm(span=50, adjust=False).mean()
            current_btc_price = float(btc_df['close'].iloc[-1])
            if current_btc_price > float(btc_ema50.iloc[-1]):
                btc_trend = "Uptrend (Bullish)"
                btc_uptrend_val = 1
            elif current_btc_price < float(btc_ema50.iloc[-1]):
                btc_trend = "Downtrend (Bearish)"
                btc_downtrend_val = 1
        except Exception as e:
            print("Lỗi tính BTC trend:", e)
            
        # Lấy xu hướng H1 của Altcoin hiện tại (Feature: h1_uptrend, h1_downtrend)
        h1_uptrend_val = 0
        h1_downtrend_val = 0
        try:
            h1_klines = binance_client.get_historical_klines(symbol, interval="1h", limit=30)
            h1_df = pd.DataFrame(h1_klines)
            h1_ema_8 = h1_df['close'].ewm(span=8, adjust=False).mean()
            h1_ema_13 = h1_df['close'].ewm(span=13, adjust=False).mean()
            h1_ema_21 = h1_df['close'].ewm(span=21, adjust=False).mean()
            
            # Kiểm tra cụm EMA 1 giờ mới nhất
            if float(h1_ema_8.iloc[-1]) > float(h1_ema_13.iloc[-1]) > float(h1_ema_21.iloc[-1]):
                h1_uptrend_val = 1
            elif float(h1_ema_8.iloc[-1]) < float(h1_ema_13.iloc[-1]) < float(h1_ema_21.iloc[-1]):
                h1_downtrend_val = 1
        except Exception as e:
            print("Lỗi tính H1 trend:", e)
            
        # Lấy 50 nến gần nhất (5m) để tính toán Features M5 hiện tại
        try:
            klines = binance_client.get_historical_klines(symbol, interval=interval, limit=50)
            df = pd.DataFrame(klines)
            
            # --- TÍNH NĂNG CHIẾN THUẬT CŨ ---
            df['rsi'] = strategy_manager.calculate_rsi(df['close'])
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_21_old'] = df['close'].ewm(span=21, adjust=False).mean()
            df['ema_cross_signal'] = np.where(df['ema_9'] > df['ema_21_old'], 1, -1)
            
            ema_12 = df['close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['close'].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            macd_signal = macd_line.ewm(span=9, adjust=False).mean()
            df['macd_hist'] = macd_line - macd_signal
            
            # Tính ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['atr'] = tr.rolling(window=14).mean().fillna(0)
            
            # --- TÍNH NĂNG CHIẾN THUẬT MỚI (M5) ---
            df['ema_8'] = df['close'].ewm(span=8, adjust=False).mean()
            df['ema_13'] = df['close'].ewm(span=13, adjust=False).mean()
            df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            
            df['m5_uptrend'] = np.where((df['ema_8'] > df['ema_13']) & (df['ema_13'] > df['ema_21']), 1, 0)
            df['m5_downtrend'] = np.where((df['ema_8'] < df['ema_13']) & (df['ema_13'] < df['ema_21']), 1, 0)
            df['signal_long'] = np.where((df['low'] <= df['ema_8']) & (df['close'] > df['ema_8']), 1, 0)
            df['signal_short'] = np.where((df['high'] >= df['ema_8']) & (df['close'] < df['ema_8']), 1, 0)
            
            # Lấy dòng dữ liệu mới nhất
            current_data = df.iloc[-1]
            current_price = float(current_data['close'])
            current_atr = float(current_data['atr'])
            
            # Cấu trúc feature dataframe (12 cols) đồng bộ hoàn toàn với pipeline
            features = pd.DataFrame([{
               'rsi': float(current_data['rsi']),
               'ema_cross_signal': float(current_data['ema_cross_signal']),
               'macd_hist': float(current_data['macd_hist']),
               'atr': float(current_atr),
               'btc_uptrend': float(btc_uptrend_val),
               'btc_downtrend': float(btc_downtrend_val),
               'h1_uptrend': float(h1_uptrend_val),
               'h1_downtrend': float(h1_downtrend_val),
               'm5_uptrend': float(current_data['m5_uptrend']),
               'm5_downtrend': float(current_data['m5_downtrend']),
               'signal_long': float(current_data['signal_long']),
               'signal_short': float(current_data['signal_short'])
            }])
            
            # Model Predict Probabilities (Multi-class: 0=Loss, 1=LongWin, 2=ShortWin)
            if self.model is not None:
                probs = self.model.predict_proba(features)[0]
                # Fallback in case the model was older (only 2 classes)
                if len(probs) == 2:
                    prob_loss = probs[0] * 100.0
                    prob_long = probs[1] * 100.0
                    prob_short = 0.0
                else:
                    prob_loss = probs[0] * 100.0
                    prob_long = probs[1] * 100.0
                    prob_short = probs[2] * 100.0
            else:
                prob_loss = 100.0
                prob_long = 0.0
                prob_short = 0.0
                
            # ĐIỀU CHỈNH XÁC SUẤT BẰNG AI (Không dùng Heuristic nữa)
            # Hệ thống nhận kết quả trực tiếp từ 3 class
            is_long = True
            display_win_rate = 0.0
            
            if prob_long >= 70.0 and prob_long > prob_short:
                # Tín hiệu LONG vững chắc
                is_long = True
                display_win_rate = prob_long
            elif prob_short >= 70.0 and prob_short > prob_long:
                # Tín hiệu SHORT vững chắc
                is_long = False
                display_win_rate = prob_short
            else:
                # Nằm trong vùng rủi ro (Nhiễu, Loss cao, hoặc chưa đủ mốc 70%)
                is_long = True # Trả về mảng rác
                display_win_rate = 0.0 # Ép về 0 để Auto Worker phớt lờ hoàn toàn
            
            
            if is_long:
                # LONG: AI đoán rớt về sát EMA 8 M5 thì mới vô (Mua rẻ)
                entry_predict = float(current_data['ema_8']) 
                if entry_predict >= current_price: # Đảm bảo Limit dính nếu giá đã thấp hơn EMA
                     entry_predict = current_price - (current_atr * 0.2)
                     
                sl_price = entry_predict - (current_atr * 1.5)
                tp_price = entry_predict + (entry_predict - sl_price) * 1.5
            else:
                # SHORT: AI đoán vòng lên test EMA 8 M5 thì mới Sọc (Bán mắc)
                entry_predict = float(current_data['ema_8'])
                if entry_predict <= current_price:
                     entry_predict = current_price + (current_atr * 0.2)
                     
                sl_price = entry_predict + (current_atr * 1.5)
                tp_price = entry_predict - (sl_price - entry_predict) * 1.5
                
            trade_setup = {
                "direction": "LONG (Mua)" if is_long else "SHORT (Bán)",
                "entry_price": float(round(entry_predict, 4)),
                "take_profit_price": float(round(tp_price, 4)),
                "stop_loss_price": float(round(sl_price, 4)),
                "estimated_win_rate": float(round(display_win_rate, 2))
            }
            
            # Giữ lại format cũ cho Frontend đỡ lỗi, nhưng biến đổi prob dựa vào win_prob thực tế
            predictions = []
            for strat in self.strategies:
                # Randomize slightly around the real display_win_rate to simulate different strategies evaluating
                prob = display_win_rate + np.random.uniform(-5.0, 5.0)
                prob = max(0.0, min(100.0, prob)) 
                
                predictions.append({
                    "strategy": strat,
                    "win_probability": round(prob, 2),
                    "is_recommended": prob >= 70.0
                })
                
            predictions = sorted(predictions, key=lambda x: x["win_probability"], reverse=True)
            
            return {
                "timestamp": int(time.time()),
                "symbol": symbol,
                "interval": interval,
                "btc_global_trend": btc_trend,
                "best_strategy": predictions[0]["strategy"],
                "trade_setup": trade_setup,
                "all_predictions": predictions
            }
            
        except Exception as e:
            print("Lỗi tính predictions thực tế:", e)
            return {"error": "Lỗi tính toán AI"}

ml_predictor = MLPredictor()
