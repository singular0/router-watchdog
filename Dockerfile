FROM python:alpine

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install --no-cache-dir -r requirements.txt

COPY *.py /app

CMD ["python", "/app/watchdog.py"]
