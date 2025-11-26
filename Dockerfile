FROM python:3.11-slim

WORKDIR /app

COPY bot_code ./bot_code
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD sh -c "python3 parse_headers.py && python3 parse_text_articles.py && python3 bot_code/bot.py"