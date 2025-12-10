FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Проверка наличия файла и прав
RUN ls -l tg.py

COPY . .

RUN python parse_headers.py 
RUN python parse_text_articles.py 
CMD ["python","tg.py"]
