# Use uma versão específica do Python (3.9 é mais estável para este caso)
FROM python:3.9-slim

# Instale as dependências do sistema
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libusb-1.0-0 \
    v4l-utils \
    udev \
    python3-distutils \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Configure o diretório de trabalho
WORKDIR /app

# Atualize pip
RUN python -m pip install --upgrade pip

# Copie os arquivos necessários
COPY requirements.txt .
COPY app.py .

# Instale as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta que o Streamlit usa
EXPOSE 8501

# Configure variáveis de ambiente
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Comando para executar o aplicativo
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]