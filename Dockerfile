FROM python:3.10

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install psycopg2-binary
RUN pip install -r requirements.txt

COPY . .

#RUN mkdir -p /app/static /app/media

ENTRYPOINT ["/bin/sh", "-c" , "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn -b 0.0.0.0:8000 bookit.wsgi"]

