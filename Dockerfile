FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY citybikes_ingest.py .

CMD ["python", "citybikes_ingest.py"]
