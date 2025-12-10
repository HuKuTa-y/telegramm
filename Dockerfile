FROM python:3.11-slim

WORKDIR /src

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Проверка наличия файла и прав


COPY . .

RUN python parse_headers.py 
RUN python parse_text_articles.py 
CMD ["python","tg.py"]
