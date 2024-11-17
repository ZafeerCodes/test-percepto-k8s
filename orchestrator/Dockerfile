FROM python:3.8-slim

WORKDIR /app

# Install telnet and iputils-ping (for ping command)
RUN apt-get update && apt-get install -y \
    telnet \
    iputils-ping \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "orchestrate.py"]
