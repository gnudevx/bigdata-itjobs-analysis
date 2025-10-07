FROM apache/airflow:2.9.2-python3.12

USER root

# Cài Chrome + dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg unzip fonts-liberation libappindicator3-1 xdg-utils \
    libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 \
    libxtst6 libnss3 libxrandr2 libasound2 libatk-bridge2.0-0 \
    libgtk-3-0 libgbm-dev libxshmfence1 libdrm2 && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Cấu hình Chrome headless cho môi trường container
ENV UDC_CHROME_PATH=/usr/bin/google-chrome
ENV UDC_DATA_DIR=/tmp/undetected_chromedriver

RUN mkdir -p /dev/shm && chmod 1777 /dev/shm

USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
