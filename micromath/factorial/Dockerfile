FROM python:3.6-alpine

RUN apk add --update --no-cache py-pip

WORKDIR /app/
COPY server.py /app/server.py
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN python -c 'import os; print(os.urandom(16))' > flask_secret_key

ENTRYPOINT ["gunicorn"]
CMD ["-w 4", "-b 0.0.0.0:8083", "server:app"]
