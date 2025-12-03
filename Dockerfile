FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python parse_headers.py 
RUN python parse_text_articles.py 
CMD ["python","tg.py"]