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

    async def start_streams(self, broadcast_callback: Callable[[dict], Any]):
        """
        Kết nối WebSocket để nhận Kline thời gian thực (Multi-stream 5m, 15m)
        """
        # Đăng ký nhận stream nến 5m và 15m cho BTC và ETH
        streams = [
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
                        
                        # Payload stream tổng hợp có dạng {"stream": "...", "data": {"k": ...}}
                        data = payload.get("data")
                        if data:
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
