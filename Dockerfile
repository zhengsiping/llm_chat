# 1. 使用 Python 3.13.2 官方镜像
FROM python:3.13.2-slim

# 2. 设置工作目录
WORKDIR /

# 3. 复制代码到容器
COPY . .

# 4. 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 5. 运行 Uvicorn 服务器
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]