from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from dotenv import load_dotenv

from binance_client import binance_client
from ml_predictor import ml_predictor
from order_manager import order_manager

load_dotenv()

app = FastAPI(title="Binance Futures Scalping API")

# Setup CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong thực tế nên giới hạn domain của frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Websocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")

manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    # Khởi động việc theo dõi Binance stream
    
    async def process_websocket_message(message: dict):
        # Gọi OrderManager check TP/SL và Khớp lệnh Pending liên tục theo luồng giá Live
        symbol = message.get("symbol")
        current_close = float(message.get("close", 0))
        
        if symbol and current_close > 0:
            order_manager.check_pending_orders(symbol, current_close)
            order_manager.check_orders(symbol, current_close)

        # Broadcast cho UI (Chỉ gửi kline để tránh làm nặng frontend với toàn bộ ticker)
        if message.get("type") == "kline":
            await manager.broadcast(message)

    asyncio.create_task(binance_client.start_streams(process_websocket_message))
    
    # Huấn luyện mô hình cơ bản nều cần (giả lập)
    print("Backend started... Initializing ML model...")
    ml_predictor.initialize_model()
    
    # Khởi động Background Task Auto-Trade cho 32 Coin
    asyncio.create_task(auto_trade_worker())

async def auto_trade_worker():
    """Bot tự động quét 32 đồng coin mỗi 5 phút (300s). Nếu WinRate >= 70% thì tự mở lệnh Pending"""
    print("[AUTO-WORKER] Bắt đầu luồng kiểm tra điểm vào lệnh Tự Động (Limit)...")
    # Lấy toàn bộ danh sách Coin Future đang Active trên Binance
    print("[AUTO-WORKER] Đang tải danh sách USDT Futures từ Binance...")
    symbols = binance_client.get_usdt_futures_symbols()
    print(f"[AUTO-WORKER] Đã nạp {len(symbols)} đồng coin vào danh sách theo dõi.")
    
    while True:
        if not ml_predictor.model_ready:
            await asyncio.sleep(10)
            continue
            
        print("[AUTO-WORKER] Đang quét thị trường tìm cơ hội Limit...")
        for sym in symbols:
            try:
                # Dùng khung 5m làm tín hiệu scalping siêu ngắn
                prediction_data = ml_predictor.predict(sym, interval="5m")
                
                if "error" not in prediction_data and "trade_setup" in prediction_data:
                    setup = prediction_data["trade_setup"]
                    win_rate = setup["estimated_win_rate"]
                    
                    if win_rate >= 70.0:
                        order_manager.open_new_order(
                            symbol=sym,
                            direction=setup["direction"],
                            entry_price=setup["entry_price"],
                            tp_price=setup["take_profit_price"],
                            sl_price=setup["stop_loss_price"],
                            win_prob=win_rate
                        )
                # Ngủ ngắn giữa các coin để tránh Rate Limit Binance REST API
                await asyncio.sleep(2)
            except Exception as e:
                print(f"[AUTO-WORKER] Lỗi quét {sym}: {e}")
                
        # Ngủ 5 phút rồi lặp lại
        await asyncio.sleep(300)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Binance Futures Scalping API is running"}

@app.get("/api/v1/symbols")
def get_symbols():
    """
    Trả về danh sách tất cả các cặp tỷ giá Futures giao dịch bằng USDT
    """
    try:
        symbols = binance_client.get_usdt_futures_symbols()
        return {"data": symbols}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/klines/{symbol}")
def get_historical_klines(symbol: str, interval: str = "1m", limit: int = 500):
    """
    Lấy dữ liệu nến lịch sử từ Binance Futures
    """
    try:
        klines = binance_client.get_historical_klines(symbol, interval, limit)
        return {"symbol": symbol, "data": klines}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/ml/predict/{symbol}")
def get_ml_prediction(symbol: str, interval: str = "5m"):
    """
    Trả về dự đoán chiến thuật có tính đến xu hướng BTC
    """
    prediction = ml_predictor.predict(symbol, interval)
    return {"symbol": symbol, "prediction": prediction}

@app.get("/api/v1/orders/pending")
def get_pending_orders():
    return {"data": order_manager.get_pending_orders()}

@app.get("/api/v1/orders/open")
def get_open_orders():
    return {"data": order_manager.get_open_orders()}

@app.get("/api/v1/orders/closed")
def get_closed_orders():
    return {"data": order_manager.get_closed_orders()}

@app.websocket("/ws/market_data")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Chờ nhận dữ liệu từ client nếu có (vd ping)
            data = await websocket.receive_text()
            if data == "ping":
                 await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
