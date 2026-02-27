# Binance AI Scalping Bot

Dự án này là một Bot giao dịch thuật toán tự động trên sàn Binance Futures, áp dụng mô hình Machine Learning (Random Forest) kết hợp đa khung thời gian (H1 & M5). AI sẽ phân tích 12 tham số từ các chỉ báo (RSI, MACD, EMA Cross, ATR) và tự động mở/đóng lệnh (Paper Trading) thông qua cơ sở dữ liệu SQLite cục bộ. Giao diện trực quan được xây dựng bằng ReactJS giúp bạn dễ dàng theo dõi lợi nhuận và tình hình thị trường.

---

## Tính Năng Cốt Lõi

1. **Machine Learning 12 Tham Số:** Dự đoán tỷ lệ thắng (% Win Probability) sử dụng thuật toán Random Forest Classifier dựa trên 12 tham số đa dạng, kết hợp giữa Xu hướng chung của BTC và sức mạnh từng Altcoin.
2. **Chiến Thuật Pullback Đa Khung Thời Gian (H1 + M5):** Bot xem xét cả cấu trúc Uptrend/Downtrend dài hạn trên H1 (dựa trên EMA 8/13/21) trước khi tìm vị thế vào lệnh tối ưu tại nến M5 (khi giá chạm EMA 8 và rút râu).
3. **Quản Lý Vốn (Risk Management) Mặc Định:** Tự động tính toán giá Take Profit và Stop Loss dựa trên biên độ dao động nến thật (ATR), chốt Risk/Reward Ratio mặc định là 1:1.5.
4. **Lưu Trữ Bền Vững (Database):** Mọi lệnh đóng mở và biến động lợi nhuận ảo (PNL) sẽ tự phân loại và lưu gọn vào tệp \`trading_bot.db\` SQLite, đảm bảo chống mất dữ liệu khi restart hoặc cúp điện.
5. **Dễ Cài Đặt và Cấu Hình:** Cấu trúc File được chia nhỏ mạch lạc, dễ dang mở rộng chiến thuật.

---

## Hướng Dẫn Cài Đặt Sự Dụng (Development Mode)

Bởi vì Bot gồm có phần Core Backend tính toán bằng Python và phần Giao diện theo dõi Frontend bằng ReactJS, bạn cần chuẩn bị chia Terminal Node ra làm 2 cửa sổ để chạy song song.

### 🐧 Dành Cho Môi Trường MacOS / Linux 🐧

**Bước 1: Chạy Backend (Python)**
Mở Terminal 1 và điều hướng vào thư mục Backend:
```bash
cd backend

# 1. Kích hoạt môi trường ảo (Virtual Environment)
source venv/bin/activate

# 2. Cài đặt các thư viện cần thiết (Chỉ cần làm lần đầu khi giải nén)
pip install -r requirements.txt

# 3. Khởi chạy Server FastAPI
uvicorn main:app --reload
```
Server Python sẽ bắt đầu lắng nghe tại địa chỉ \`http://localhost:8000\`.


**Bước 2: Chạy Frontend (ReactJS)**
Mở Terminal 2 và điều hướng vào thư mục Frontend:
```bash
cd frontend

# 1. Tải về và cấu hình các package NPM (Chỉ làm lần đầu)
npm install

# 2. Khởi chạy UI Web Server của Vite
npm run dev
```
Trình duyệt sẽ tự động mở trang web (hoặc bạn có thể tự truy cập \`http://localhost:5173\`) để theo dõi tình hình Chart và Bot vào lệnh AI.


---


### 🪟 Dành Cho Môi Trường Windows 🪟

**Bước 1: Chạy Backend (Python)**
Mở Command Prompt (hoặc PowerShell) thứ 1 và chuyển đến thư mục Backend:
```cmd
cd backend

# 1. Kích hoạt môi trường ảo (Ghi chú: Cú pháp khác so với Mac)
venv\Scripts\activate

# 2. Cài đặt thư viện (nếu bạn mới giải nén file ZIP)
pip install -r requirements.txt

# 3. Khởi chạy API
uvicorn main:app --reload
```

**Bước 2: Chạy Frontend (ReactJS)**
Mở Command Prompt (hoặc PowerShell) thứ 2 và chuyển đến thư mục Frontend:
```cmd
cd frontend

# 1. Cài đặt toàn bộ thư viện cho React (Vite sẽ tự chép node_modules)
npm install

# 2. Bật trang Web
npm run dev
```

---

## Khắc Phục Lỗi Cơ Bản (Troubleshooting)

- **Lỗi Thiếu Model:** Nếu Frontend báo "Failed to load ML models", nghĩa là bạn chưa khởi tạo file Pickle. Mở terminal tại thư mục \`backend\` (đã active venv) và chạy \`python data_pipeline.py\` để BOT bắt đầu tải nến và tiến hành huấn luyện lấy bằng lái AI. Mất khoảng 30s.
- **Lỗi Port Đã Cầm:** \`[Errno 48] Address already in use\`. Cổng 8000 của Python bị kẹt, hãy đóng terminal hoặc tắt Background Script.
- **Lỗi Trắng Giao Diện:** Nếu chưa \`npm install\` tại \`frontend\` thì \`npm run dev\` sẽ tịt ngòi báo lỗi lỏ.

---

## Lệnh Git Hữu Ích Dành Cho Bạn Taima
Nếu sau này bạn gắn lại được Khóa SSH:
```bash
git add .
git commit -m "Your update message"
git push
```
