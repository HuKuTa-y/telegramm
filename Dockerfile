FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD "python parse_headers.py" 
CMD "python parse_text_articles.py" 
CMD "python tg.py"