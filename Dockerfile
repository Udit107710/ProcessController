FROM python:alpine3.9
COPY app.py /application/
COPY requirements.txt /application/
WORKDIR /application/
RUN apk add gcc musl-dev linux-headers postgresql-dev openssl-dev libffi-dev
COPY worker.key /etc/ssl/private/
COPY worker.pem /etc/ssl/certs/
RUN pip install -r requirements.txt
ENV FLASK_APP='app.py'
ENV FLASK_RUN_HOST='0.0.0.0'
ENV FLASK_ENV='development'
ENV PYTHONUNBUFFERED='true'
EXPOSE 5000
CMD ["flask", "run"]