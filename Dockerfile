FROM python:alpine

LABEL org.opencontainers.image.source="https://github.com/singular0/router-watchdog"

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install --no-cache-dir -r requirements.txt

COPY *.py /app/

CMD ["python", "/app/watchdog.py"]
