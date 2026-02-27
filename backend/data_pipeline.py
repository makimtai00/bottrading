import os
import time
import pandas as pd
import numpy as np
from binance_client import binance_client
from strategies import strategy_manager
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

class DataPipeline:
    def __init__(self):
        self.symbols = [
            "PNUTUSDT", "MANAUSDT", "KAITOUSDT", "NEARUSDT", "GMTUSDT", "TONUSDT", "GOATUSDT",
            "PONKEUSDT", "SAFEUSDT", "AVAUSDT", "TOKENUSDT", "MOCAUSDT", "PEOPLEUSDT", "SOLUSDT",
            "SUIUSDT", "DOGEUSDT", "ENAUSDT", "MOVEUSDT", "ADAUSDT", "TURBOUSDT", "NEIROUSDT",
            "AVAXUSDT", "DOTUSDT", "XRPUSDT", "NEIROETHUSDT", "LINKUSDT", "XLMUSDT", "ZECUSDT",
            "ATOMUSDT", "BATUSDT", "NEOUSDT", "QTUMUSDT"
        ]
        self.intervals = ["5m"] # Pullback Strategy này tập trung đánh scalping 5m
        self.limit = 1000 # Số lượng nến thu thập để train
        
    def fetch_data(self) -> pd.DataFrame:
        """Thu thập Kline lịch sử cho tất cả Altcoin và ghép thành 1 DataFrame tổng"""
        all_data = []
        print(f"Bắt đầu thu thập {self.limit} nến cho {len(self.symbols)} dự án...")
        
        for symbol in self.symbols:
            for interval in self.intervals:
                try:
                    # Lấy dữ liệu qua REST API đã viết sẵn trong binance_client
                    klines = binance_client.get_historical_klines(symbol, interval, self.limit)
                    df = pd.DataFrame(klines)
                    
                    # Thêm các cột định danh
                    df['symbol'] = symbol
                    df['interval'] = interval
                    
                    all_data.append(df)
                    print(f" ✓ Đã lấy xong {symbol} ({interval}) - {len(df)} nến")
                    # Rate limit protection (Binance IP ban avoidance)
                    time.sleep(0.1) 
                except Exception as e:
                    print(f" x Lỗi khi lấy {symbol} ({interval}): {e}")
                    
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Tính toán các chỉ báo kỹ thuật để làm Feature cho mô hình học máy"""
        print("Đang tính toán Features (H1+M5 Pullback, BTC Trend...)...")
        
        # 1. Fetch BTC 5m trend
        try:
            btc_klines = binance_client.get_historical_klines("BTCUSDT", "5m", self.limit)
            btc_df = pd.DataFrame(btc_klines)
            btc_df['btc_ema_50'] = btc_df['close'].ewm(span=50, adjust=False).mean()
            btc_df['btc_uptrend'] = np.where(btc_df['close'] > btc_df['btc_ema_50'], 1, 0)
            btc_df['btc_downtrend'] = np.where(btc_df['close'] < btc_df['btc_ema_50'], 1, 0)
            btc_features = btc_df[['time', 'btc_uptrend', 'btc_downtrend']]
            
            df = pd.merge(df, btc_features, on='time', how='left')
            # Forward fill trong trường hợp thiếu nến
            df['btc_uptrend'] = df['btc_uptrend'].ffill().fillna(0)
            df['btc_downtrend'] = df['btc_downtrend'].ffill().fillna(0)
        except Exception as e:
            print("Lỗi tính BTC Trend:", e)
            df['btc_uptrend'] = 0
            df['btc_downtrend'] = 0

        def calculate_indicators(group):
            group = group.sort_values('time')
            
            # --- CHIẾN THUẬT CŨ ---
            # RSI
            group['rsi'] = strategy_manager.calculate_rsi(group['close'])
            
            # EMA Cross Cũ
            group['ema_9'] = group['close'].ewm(span=9, adjust=False).mean()
            group['ema_21_old'] = group['close'].ewm(span=21, adjust=False).mean()
            group['ema_cross_signal'] = np.where(group['ema_9'] > group['ema_21_old'], 1, -1)
            
            # MACD
            ema_12 = group['close'].ewm(span=12, adjust=False).mean()
            ema_26 = group['close'].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            macd_signal = macd_line.ewm(span=9, adjust=False).mean()
            group['macd_hist'] = macd_line - macd_signal
            
            # --- CHIẾN THUẬT MỚI ---
            # Tính M5 EMAs
            group['ema_8'] = group['close'].ewm(span=8, adjust=False).mean()
            group['ema_13'] = group['close'].ewm(span=13, adjust=False).mean()
            group['ema_21'] = group['close'].ewm(span=21, adjust=False).mean()
            
            # M5 Trend (Tách nhau ra)
            group['m5_uptrend'] = np.where((group['ema_8'] > group['ema_13']) & (group['ema_13'] > group['ema_21']), 1, 0)
            group['m5_downtrend'] = np.where((group['ema_8'] < group['ema_13']) & (group['ema_13'] < group['ema_21']), 1, 0)
            
            # Tính M5 Pullback Signal
            group['signal_long'] = np.where((group['low'] <= group['ema_8']) & (group['close'] > group['ema_8']), 1, 0)
            group['signal_short'] = np.where((group['high'] >= group['ema_8']) & (group['close'] < group['ema_8']), 1, 0)
            
            # Resample sang H1 để tính Trend H1 
            group['datetime'] = pd.to_datetime(group['time'], unit='s')
            temp = group.set_index('datetime')
            
            # Grouping theo 1H
            h1_df = temp.resample('1h').agg({'close': 'last'}).dropna()
            if not h1_df.empty:
                h1_df['h1_ema_8'] = h1_df['close'].ewm(span=8, adjust=False).mean()
                h1_df['h1_ema_13'] = h1_df['close'].ewm(span=13, adjust=False).mean()
                h1_df['h1_ema_21'] = h1_df['close'].ewm(span=21, adjust=False).mean()
                
                h1_df['h1_uptrend'] = np.where((h1_df['h1_ema_8'] > h1_df['h1_ema_13']) & (h1_df['h1_ema_13'] > h1_df['h1_ema_21']), 1, 0)
                h1_df['h1_downtrend'] = np.where((h1_df['h1_ema_8'] < h1_df['h1_ema_13']) & (h1_df['h1_ema_13'] < h1_df['h1_ema_21']), 1, 0)
                
                # Shift 1h để không dính Lookahead bias
                h1_df['h1_uptrend'] = h1_df['h1_uptrend'].shift(1).fillna(0)
                h1_df['h1_downtrend'] = h1_df['h1_downtrend'].shift(1).fillna(0)
                
                # Merge lại vào M5 bằng merge_asof
                h1_features = h1_df[['h1_uptrend', 'h1_downtrend']]
                group = pd.merge_asof(group, h1_features, left_on='datetime', right_index=True)
            else:
                group['h1_uptrend'] = 0
                group['h1_downtrend'] = 0
            
            # Tính ATR dùng cho Stoploss
            high_low = group['high'] - group['low']
            high_close = np.abs(group['high'] - group['close'].shift())
            low_close = np.abs(group['low'] - group['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            group['atr'] = tr.rolling(window=14).mean().fillna(0)
            
            return group
            
        return df.groupby(['symbol', 'interval']).apply(calculate_indicators).reset_index(drop=True)

    def generate_labels(self, df: pd.DataFrame, rr_ratio: float = 1.5, n_bars: int = 15) -> pd.DataFrame:
        """
        Tạo nhãn (Target Label): 
        Kiểm tra xem giá trong tương lai có chạm Take Profit trước Stop Loss hay không.
        - Nếu chạm TP trước -> Label 1 (Win)
        - Nếu chạm SL hoặc hết n_bars mà chưa tới TP -> Label 0 (Loss)
        """
        print("Đang tạo nhãn (Labeling) - Backtest mô phỏng...")
        
        # Label đa mảng (Multi-class Classification)
        # Label 1: LONG_WIN (Giá Lên cắn TP trước SL dựa trên nến hiện tại)
        # Label 2: SHORT_WIN (Giá Xuống cắn TP của lệnh Short trước SL)
        # Label 0: LOSS hoặc SIDEWAY (Quá thời gian n_bars không chạy tới đâu hoặc cắn SL)
        
        df = df.copy()
        df['target'] = np.nan
        
        # Duyệt qua từng group để đảm bảo không nhìn tương lai xuyên qua coin khác
        def label_group(group):
            closes = group['close'].values
            highs = group['high'].values
            lows = group['low'].values
            atrs = group['atr'].values
            
            targets = np.zeros(len(group)) # Mặc định là 0 (LOSS)
            
            for i in range(len(group) - n_bars):
                if np.isnan(atrs[i]):
                    continue
                    
                entry_price = closes[i]
                atr_val = atrs[i]
                
                # Setup định mức rủi ro
                long_sl = entry_price - (atr_val * 1.5)
                long_tp = entry_price + ((entry_price - long_sl) * rr_ratio)
                
                short_sl = entry_price + (atr_val * 1.5)
                short_tp = entry_price - ((short_sl - entry_price) * rr_ratio)
                
                # Check target in the next n_bars
                for j in range(1, n_bars + 1):
                    future_high = highs[i + j]
                    future_low = lows[i + j]
                    
                    # Logic: Giả sử cùng một thời điểm mở cả lệnh Long và lệnh Short 
                    # thằng nào chạm TP trước (mà chưa dính SL của nó) thì dán Label thằng đó.
                    
                    # KIỂM TRA LONG TRƯỚC
                    if future_low <= long_sl:
                        # LONG chết, thử tiếp xem SHORT có sống không
                        pass
                    elif future_high >= long_tp:
                        targets[i] = 1 # LONG WIN
                        break
                        
                    # KIỂM TRA SHORT
                    if future_high >= short_sl:
                        # SHORT chết
                        pass
                    elif future_low <= short_tp:
                        targets[i] = 2 # SHORT WIN
                        break
                        
            group['target'] = targets
            return group

        return df.groupby(['symbol', 'interval']).apply(label_group).reset_index(drop=True)

    def train_model(self):
        """Pipeline chính: Tải dữ liệu -> Tạo tính năng -> Label -> Train RandomForest"""
        raw_data = self.fetch_data()
        feature_data = self.generate_features(raw_data)
        labeled_data = self.generate_labels(feature_data)
        
        # Bỏ đi giá trị NaNs ở khúc đầu (do rolling/EMA) và đuôi (do labeling tương lai)
        clean_df = labeled_data.dropna()
        # Tập hợp the Full Features cho ML. Bao gồm tất cả indicator vừa xây.
        features = [
            'rsi', 'ema_cross_signal', 'macd_hist', 'atr', # Cũ
            'btc_uptrend', 'btc_downtrend', # Mới
            'h1_uptrend', 'h1_downtrend',
            'm5_uptrend', 'm5_downtrend',
            'signal_long', 'signal_short'
        ]
        
        # Chỉ giữ lại các hàng có đủ tín hiệu (tranh nhiễu do thời điểm ban đầu EMA chưa kịp warm-up)
        X = clean_df[features]
        y = clean_df['target']
        
        print(f"\nPhân bố nhãn (0=Loss, 1=Win):\n{y.value_counts()}")
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print("Đang huấn luyện mô hình RandomForestClassifier...")
        model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        print(f"Độ chính xác trên tập Test: {acc*100:.2f}%")
        print("Báo cáo phân loại:\n", classification_report(y_test, preds))
        
        # Lưu mô hình ra file tĩnh
        joblib.dump(model, "rf_scalping_model.pkl")
        print("Đã lưu mô hình vào: backend/rf_scalping_model.pkl")

if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.train_model()
