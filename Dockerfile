FROM python:3.9-slim

WORKDIR /app

# 设置pip源为国内镜像
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 首先复制依赖文件
COPY requirements.txt .
RUN python -m pip install --upgrade pip

# 分步安装依赖
RUN pip install --no-cache-dir fastapi==0.103.2 uvicorn pydantic==1.10.12 python-multipart==0.0.6
RUN pip install --no-cache-dir ddddocr==1.4.7
RUN pip install --no-cache-dir pillow==9.5.0
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有文件
COPY . .

# 确保模型目录和静态文件目录存在
RUN mkdir -p models static

# 使用环境变量设置端口
ENV PORT=8080

CMD ["python", "main.py"]
