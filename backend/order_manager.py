import sqlite3
import time
from typing import Dict, List
import uuid

DB_NAME = "trading_bot.db"

class OrderManager:
    def __init__(self):
        self._init_db()
        # In-memory cache để Web đọc nhanh và Update PNL không cần chọc DB liên tục (giảm I/O)
        self.pending_orders: Dict[str, dict] = {}
        self.open_orders: Dict[str, dict] = {}
        self.closed_orders: List[dict] = []
        self._load_from_db()
        
    def _get_conn(self):
        # sqlite3 yêu cầu check_same_thread=False nếu gọi từ nhiều luồng async FastAPI
        return sqlite3.connect(DB_NAME, check_same_thread=False)
        
    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS open_orders (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    direction TEXT,
                    entry_price REAL,
                    take_profit_price REAL,
                    stop_loss_price REAL,
                    estimated_win_rate REAL,
                    open_time INTEGER,
                    status TEXT,
                    pnl REAL,
                    expiration_time INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS closed_orders (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    direction TEXT,
                    entry_price REAL,
                    take_profit_price REAL,
                    stop_loss_price REAL,
                    estimated_win_rate REAL,
                    open_time INTEGER,
                    status TEXT,
                    close_reason TEXT,
                    close_price REAL,
                    final_pnl REAL,
                    close_time INTEGER,
                    expiration_time INTEGER
                )
            """)
            
            try:
                cursor.execute("ALTER TABLE open_orders ADD COLUMN expiration_time INTEGER")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE closed_orders ADD COLUMN expiration_time INTEGER")
            except sqlite3.OperationalError:
                pass
                
            conn.commit()

    def _load_from_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Load Open & Pending Orders
            cursor.execute("SELECT * FROM open_orders")
            cols = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                order = dict(zip(cols, row))
                if order['status'] == 'PENDING':
                    self.pending_orders[order['id']] = order
                else:
                    self.open_orders[order['id']] = order
                
            # Load Closed Orders (Chỉ lấy 100 dòng mới nhất)
            cursor.execute("SELECT * FROM closed_orders ORDER BY close_time DESC LIMIT 100")
            cols = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                self.closed_orders.append(dict(zip(cols, row)))

    def open_new_order(self, symbol: str, direction: str, entry_price: float, tp_price: float, sl_price: float, win_prob: float):
        """Mở một lệnh ảo mới nếu chưa có lệnh nào đang chạy chữ cho symbol đó"""
        
        # Kiểm tra trùng lặp trong memory
        # Nếu đang có lệnh PENDING hoặc OPEN cho symbol này thì không tạo thêm nới
        for order in self.open_orders.values():
            if order['symbol'] == symbol:
                return 
        for order in self.pending_orders.values():
            if order['symbol'] == symbol:
                return
                
        order_id = str(uuid.uuid4())
        now = int(time.time())
        
        new_order = {
            "id": order_id,
            "symbol": symbol,
            "direction": direction,
            "entry_price": float(round(entry_price, 4)),
            "take_profit_price": float(round(tp_price, 4)),
            "stop_loss_price": float(round(sl_price, 4)),
            "estimated_win_rate": float(round(win_prob, 2)),
            "open_time": now,
            "status": "PENDING", # Luôn bắt đầu bằng PENDING
            "pnl": 0.0,
            "expiration_time": now + 20 * 60
        }
        
        # Lưu vào DB
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO open_orders 
                (id, symbol, direction, entry_price, take_profit_price, stop_loss_price, estimated_win_rate, open_time, status, pnl, expiration_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_order['id'], new_order['symbol'], new_order['direction'], 
                new_order['entry_price'], new_order['take_profit_price'], 
                new_order['stop_loss_price'], new_order['estimated_win_rate'],
                new_order['open_time'], new_order['status'], new_order['pnl'], new_order['expiration_time']
            ))
            conn.commit()
            
        # Thêm vào Cache RAM PENDING
        self.pending_orders[order_id] = new_order
        print(f"[AUTO-TRADE] Đã đặt LỆNH CHỜ (PENDING) {direction} cho {symbol} điểm vào {entry_price}")
        
    def check_pending_orders(self, symbol: str, current_price: float):
        """Kiểm tra xem giá Live có khớp giá Entry của các lệnh PENDING không"""
        orders_to_open = []
        orders_to_cancel = []
        now = int(time.time())
        
        for order_id, order in list(self.pending_orders.items()):
            if order['status'] != 'PENDING':
                continue
                
            # Mới: Check hết hạn 20 phút
            expiration_time = order.get('expiration_time')
            if expiration_time and now >= expiration_time:
                orders_to_cancel.append(order_id)
                continue
                
            if order['symbol'] != symbol:
                continue
                
            entry = order['entry_price']
            direction = order['direction']
            
            # Logic cắn Entry: Nếu Long giá rớt xuống Entry, Nếu Short giá móc lên Entry
            is_entry_hit = False
            if "LONG" in direction and current_price <= entry:
                is_entry_hit = True
            elif "SHORT" in direction and current_price >= entry:
                is_entry_hit = True
                
            if is_entry_hit:
                orders_to_open.append(order_id)
                
        if orders_to_cancel or orders_to_open:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                for order_id in orders_to_cancel:
                    canceled_order = self.pending_orders.pop(order_id)
                    canceled_order['status'] = "CANCELED"
                    canceled_order['close_reason'] = "EXPIRED"
                    canceled_order['close_price'] = current_price
                    canceled_order['final_pnl'] = 0.0
                    canceled_order['close_time'] = now
                    
                    self.closed_orders.insert(0, canceled_order)
                    if len(self.closed_orders) > 100:
                        self.closed_orders.pop()
                        
                    cursor.execute("DELETE FROM open_orders WHERE id = ?", (order_id,))
                    cursor.execute("""
                        INSERT INTO closed_orders 
                        (id, symbol, direction, entry_price, take_profit_price, stop_loss_price, estimated_win_rate, open_time, status, close_reason, close_price, final_pnl, close_time, expiration_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        canceled_order['id'], canceled_order['symbol'], canceled_order['direction'], 
                        canceled_order['entry_price'], canceled_order['take_profit_price'], 
                        canceled_order['stop_loss_price'], canceled_order['estimated_win_rate'],
                        canceled_order['open_time'], canceled_order['status'],
                        canceled_order['close_reason'], canceled_order['close_price'],
                        canceled_order['final_pnl'], canceled_order['close_time'], canceled_order.get('expiration_time')
                    ))
                    print(f"[AUTO-TRADE] Hủy bỏ lệnh PENDING {canceled_order['symbol']} do quá 20 phút không khớp.")
                    
                for order_id in orders_to_open:
                    opened_order = self.pending_orders.pop(order_id)
                    opened_order['status'] = "OPEN"
                    # Reset lại thời gian mở thành thời gian khớp lệnh thực tế
                    opened_order['open_time'] = int(time.time())
                    
                    self.open_orders[order_id] = opened_order
                    
                    # Cập nhật Status trong DB
                    cursor.execute("""
                        UPDATE open_orders 
                        SET status = ?, open_time = ?
                        WHERE id = ?
                    """, ("OPEN", opened_order['open_time'], order_id))
                    
                    print(f"[AUTO-TRADE] Khớp lệnh! {opened_order['symbol']} đã chuyển từ PENDING -> OPEN tại giá {current_price}")
                conn.commit()
        
    def check_orders(self, symbol: str, current_price: float):
        """Kiểm tra SL/TP qua websocket."""
        orders_to_close = []
        
        for order_id, order in self.open_orders.items():
            if order['symbol'] != symbol:
                continue
                
            entry = order['entry_price']
            tp = order['take_profit_price']
            sl = order['stop_loss_price']
            direction = order['direction']
            
            # Cập nhật PNL ảo (Chỉ update RAM, KHÔNG update SQLite để đỡ nghẽn ổ cứng)
            if "LONG" in direction:
                pnl_percent = ((current_price - entry) / entry) * 100
                is_tp_hit = current_price >= tp
                is_sl_hit = current_price <= sl
            else: # SHORT
                pnl_percent = ((entry - current_price) / entry) * 100
                is_tp_hit = current_price <= tp
                is_sl_hit = current_price >= sl
                
            order['pnl'] = float(round(float(pnl_percent), 2))
            
            if is_tp_hit or is_sl_hit:
                close_reason = "TAKE_PROFIT" if is_tp_hit else "STOP_LOSS"
                orders_to_close.append((order_id, close_reason, current_price, order['pnl']))
                
        # Nếu có lệnh chốt
        if orders_to_close:
            with self._get_conn() as conn:
                cursor = conn.cursor()
                for order_id, reason, close_price, final_pnl in orders_to_close:
                    closed_order = self.open_orders.pop(order_id)
                    closed_order['status'] = "CLOSED"
                    closed_order['close_reason'] = reason
                    closed_order['close_price'] = close_price
                    closed_order['final_pnl'] = final_pnl
                    closed_order['close_time'] = int(time.time())
                    
                    # Cập nhật Cache
                    self.closed_orders.insert(0, closed_order)
                    if len(self.closed_orders) > 100:
                        self.closed_orders.pop()
                        
                    # 1. Xóa khỏi bảng open_orders
                    cursor.execute("DELETE FROM open_orders WHERE id = ?", (order_id,))
                    
                    # 2. Thêm vào bảng closed_orders
                    cursor.execute("""
                        INSERT INTO closed_orders 
                        (id, symbol, direction, entry_price, take_profit_price, stop_loss_price, estimated_win_rate, open_time, status, close_reason, close_price, final_pnl, close_time, expiration_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        closed_order['id'], closed_order['symbol'], closed_order['direction'], 
                        closed_order['entry_price'], closed_order['take_profit_price'], 
                        closed_order['stop_loss_price'], closed_order['estimated_win_rate'],
                        closed_order['open_time'], closed_order['status'],
                        closed_order['close_reason'], closed_order['close_price'],
                        closed_order['final_pnl'], closed_order['close_time'],
                        closed_order.get('expiration_time')
                    ))
                    
                    print(f"[AUTO-TRADE] Đã đóng lệnh {closed_order['symbol']} do chạm {reason}. PNL: {final_pnl}%")
                conn.commit()
                
    def get_pending_orders(self) -> List[dict]:
        return list(self.pending_orders.values())

    def get_open_orders(self) -> List[dict]:
        return list(self.open_orders.values())
        
    def get_closed_orders(self) -> List[dict]:
        return self.closed_orders

order_manager = OrderManager()
