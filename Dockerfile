FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY research_assistant ./research_assistant
COPY reindex.py .

RUN mkdir -p papers

EXPOSE 8000

CMD uvicorn research_assistant.api:app --host 0.0.0.0 --port ${PORT:-8000}
