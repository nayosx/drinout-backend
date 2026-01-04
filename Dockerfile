FROM python:3.11

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
