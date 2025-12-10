FROM python:3.12-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
USER root

WORKDIR /app

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python parse_headers.py 
RUN python parse_text_articles.py 
CMD ["python","tg.py"]
