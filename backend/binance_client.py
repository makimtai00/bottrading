import requests
import json
import asyncio
import websockets
from typing import Callable, Any

class BinanceClient:
    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self.ws_url = "wss://fstream.binance.com/ws"
        # Mặc định theo dõi BTCUSDT
        self.symbols = ["btcusdt"]

    def get_historical_klines(self, symbol: str, interval: str = "1m", limit: int = 500):
        """
        Lấy nến quá khứ qua REST API
        """
        endpoint = f"{self.base_url}/fapi/v1/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        res = requests.get(endpoint, params=params)
        res.raise_for_status()
        data = res.json()
        
        # Format lại dữ liệu dễ đọc cho frontend
        formatted_data = []
        for d in data:
            formatted_data.append({
                "time": int(d[0]) // 1000, # Lightweight charts cần timestamp (s)
                "open": float(d[1]),
                "high": float(d[2]),
                "low": float(d[3]),
                "close": float(d[4]),
                "volume": float(d[5]),
                "close_time": int(d[6])
            })
        return formatted_data

    def get_usdt_futures_symbols(self) -> list[str]:
        """
        Lấy danh sách toàn bộ các đồng Coin Future giao dịch bằng USDT đang Active trên Binance
        """
        try:
            endpoint = f"{self.base_url}/fapi/v1/exchangeInfo"
            res = requests.get(endpoint)
            res.raise_for_status()
            data = res.json()
            
            symbols = []
            for item in data.get("symbols", []):
                # Chỉ lọc các cặp giao dịch ký quỹ bằng USDT, đang TRADING (không bị hủy niêm yết) và là hợp đồng vĩnh cửu (PERPETUAL)
                if (item.get("quoteAsset") == "USDT" and 
                    item.get("status") == "TRADING" and 
                    item.get("contractType") == "PERPETUAL"):
                    symbols.append(item.get("symbol"))
                    
            print(f"Đã tải thành công danh sách {len(symbols)} cặp giao dịch USDT Futures từ Binance.")
            return symbols
        except Exception as e:
            print(f"Lỗi khi lấy danh sách symbol từ Binance: {e}")
            # Trả về list dự phòng nếu API sập
            return [
                "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", 
                "AVAXUSDT", "LINKUSDT", "DOTUSDT", "DOGEUSDT", "SUIUSDT"
            ]

    async def start_streams(self, broadcast_callback: Callable[[dict], Any]):
        """
        Kết nối WebSocket để nhận Kline và Ticker thời gian thực
        """
        # Đăng ký nhận stream nến cho BTC, ETH và miniTicker cho TOÀN BỘ symbol
        streams = [
            "!miniTicker@arr",
            "btcusdt@kline_5m", "btcusdt@kline_15m",
            "ethusdt@kline_5m", "ethusdt@kline_15m"
        ]
        stream_path = "/".join(streams)
        url = f"wss://fstream.binance.com/stream?streams={stream_path}"
        
        while True:
            try:
                print(f"Connecting to Binance WS: {url}")
                async with websockets.connect(url) as ws:
                    print("Connected to Binance WebSocket (Combined Stream)!")
                    while True:
                        msg = await ws.recv()
                        payload = json.loads(msg)
                        
                        data = payload.get("data")
                        if data:
                            if isinstance(data, list):
                                # !miniTicker@arr trả về 1 mảng các ticker
                                for ticker in data:
                                    formatted_ticker = {
                                        "type": "ticker",
                                        "symbol": ticker.get("s"),
                                        "close": float(ticker.get("c", 0))
                                    }
                                    await broadcast_callback(formatted_ticker)
                            else:
                                kline = data.get("k")
                                if kline:
                                   formatted_kline = {
                                       "type": "kline",
                                       "symbol": data.get("s"),
                                       "interval": kline.get("i"), # Lấy interval để frontend lọc
                                       "time": int(kline.get("t")) // 1000,
                                       "open": float(kline.get("o")),
                                       "high": float(kline.get("h")),
                                       "low": float(kline.get("l")),
                                       "close": float(kline.get("c")),
                                       "is_final": kline.get("x")
                                   }
                                   await broadcast_callback(formatted_kline)
                           
            except Exception as e:
                print(f"WebSocket error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

binance_client = BinanceClient()
