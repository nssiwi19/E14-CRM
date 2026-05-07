# Sử dụng Python image nhẹ
FROM python:3.12-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (nếu có) cho việc build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài đặt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code vào container
COPY . .

# Mở port mặc định của Streamlit
EXPOSE 8501

# Lệnh kiểm tra sức khỏe của Streamlit container
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Chạy ứng dụng
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
