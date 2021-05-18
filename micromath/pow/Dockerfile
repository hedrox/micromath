FROM python:3.9-alpine

RUN apk add --update --no-cache py-pip

WORKDIR /app/
COPY . .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN python -c 'import os; print(os.urandom(16))' > flask_secret_key
RUN coverage run -m pytest && coverage report -m

ENTRYPOINT ["gunicorn"]
CMD ["-w 4", "-b 0.0.0.0:8081", "server:app"]
