FROM python:3.11-slim

WORKDIR /app

COPY telegramm ./tg.py
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD "python parse_headers.py" 
CMD "python parse_text_articles.py" 
CMD "python telegramm/tg.py"