FROM python:3.10

LABEL org.opencontainers.image.source="https://github.com/singular0/router-watchdog"

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install --no-cache-dir -r requirements.txt

COPY *.py /app/
COPY *.sh /app/

CMD ["/app/app.sh"]
