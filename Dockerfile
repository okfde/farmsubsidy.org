FROM python:3.6

COPY requirements.txt /code/

WORKDIR /code

RUN cd /code/ && pip install -r requirements.txt

# For identifying commit in sentry
COPY .git /code/.git
COPY manage.py /code/manage.py
COPY farmsubsidy_org /code/farmsubsidy_org
COPY recipients /code/recipients
COPY db.sqlite3 /code/db.sqlite3

RUN python ./manage.py collectstatic --noinput

ENV PYTHONPATH /code

# Run the green unicorn
CMD gunicorn -w 4 -b 0.0.0.0:8040 --name farmsubsidy_gunicorn \
  --log-level info --log-file /var/log/gunicorn.log farmsubsidy_org.wsgi:application
