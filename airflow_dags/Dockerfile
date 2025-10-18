# ---- Base image: dùng bản Python 3.9 để tránh bug pathlib ----
FROM apache/airflow:2.11.0-python3.10

USER root

# --- Cài Chrome + dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip fonts-liberation libayatana-appindicator3-1 xdg-utils \
    libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 \
    libxtst6 libnss3 libxrandr2 libasound2 libatk-bridge2.0-0 \
    libgtk-3-0 libgbm-dev libxshmfence1 libdrm2 && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | \
    gpg --batch --yes --no-tty --dearmor -o /usr/share/keyrings/google-linux-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# --- Cài Spark client ---
COPY spark-4.0.1-bin-hadoop3.tgz /tmp/
RUN apt-get update && apt-get install -y openjdk-17-jdk && \
    tar -xzf /tmp/spark-4.0.1-bin-hadoop3.tgz -C /usr/local && \
    mv /usr/local/spark-4.0.1-bin-hadoop3 /usr/local/spark && \
    rm /tmp/spark-4.0.1-bin-hadoop3.tgz
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_HOME=/usr/local/spark
ENV PATH="${PATH}:${SPARK_HOME}/bin"

COPY /config-hadoop/* /opt/hadoop-conf/
ENV HADOOP_CONF_DIR=/opt/hadoop-conf

# --- Cấu hình Chrome headless ---
ENV UDC_CHROME_PATH=/usr/bin/google-chrome
ENV UDC_DATA_DIR=/tmp/undetected_chromedriver
RUN mkdir -p /dev/shm && chmod 1777 /dev/shm

# --- Cài lib cần cho ML ---
RUN apt-get install -y --no-install-recommends \
    build-essential gcc g++ python3-dev libatlas-base-dev && \
    rm -rf /var/lib/apt/lists/*
ENV SPARK_WAREHOUSE_DIR=/tmp/spark-warehouse
RUN mkdir -p $SPARK_WAREHOUSE_DIR && chmod -R 777 $SPARK_WAREHOUSE_DIR
USER airflow
# --- Copy và cài requirements ---
COPY requirements.txt /requirements.txt
RUN pip install xgboost==2.1.4 
RUN pip install --no-cache-dir -r /requirements.txt

# --- (Tùy chọn) Fix Pydantic nếu lỗi version ---
# RUN pip install --no-cache-dir "pydantic>=1.10.12,<2.0"


