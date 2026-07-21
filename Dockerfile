FROM python:3.12-slim

# WORKDIR /
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

CMD ["python3", "-m", "bot_v2.main"]