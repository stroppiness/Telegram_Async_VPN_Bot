FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . ./worker

CMD ["python", "-m", "worker.get_user_config"]