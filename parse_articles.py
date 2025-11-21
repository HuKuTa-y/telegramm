'''import os
import requests
from bs4 import BeautifulSoup
import json
import re
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Основная папка для хранения статей
base_folder_path = 'data/codeks'
os.makedirs(base_folder_path, exist_ok=True)

# JSON файлы
json_files = ['laws.json', 'codeks.json']
documents = []

for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        documents.extend(data)

base_url = "https://www.consultant.ru/"
result = []

pattern = re.compile(r'/document/cons_doc_LAW_(\d+)/')

# Максимальное число потоков
MAX_WORKERS = 10

def process_article(a, base_url, pattern, base_folder_path):
    title = a.get_text(strip=True)
    href = a.get('href')
    article_number = None
    href_full = None

    if href:
        if href.startswith("//"):
            href_full = "https:" + href
        elif href.startswith("/"):
            href_full = base_url + href
        elif href.startswith("http"):
            href_full = href
        else:
            href_full = base_url + "/" + href

        match = pattern.search(href_full)
        if match:
            article_number = match.group(1)

        try:
            # Получение содержимого статьи
            response = requests.get(href_full, timeout=10)
            response.raise_for_status()
            article_soup = BeautifulSoup(response.text, 'html.parser')
            content_div = article_soup.find('div', class_='article-content')
            if content_div:
                content_text = content_div.get_text(separator='\n', strip=True)
            else:
                content_text = "Нет содержимого или не найдено."

            # Формируем название файла
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
            filename = f"article_{timestamp}_{uuid.uuid4()}.txt"

            # Создаем папку для статьи, если есть номер
            if article_number:
                target_folder = os.path.join(base_folder_path, article_number)
                os.makedirs(target_folder, exist_ok=True)
                save_path = os.path.join(target_folder, filename)
            else:
                save_path = os.path.join(base_folder_path, filename)

            # Запись файла
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"{title}\n\n{content_text}")

            return {
                "id": str(uuid.uuid4()),
                "Название": title,
                "Ссылка": href_full,
                "Номер_источника_статьи": article_number,
                "файл": save_path
            }
        except requests.RequestException:
            return None
    return None

def process_document(doc):
    relative_link = doc.get("Ссылка")
    if not relative_link:
        return []

    # Формируем полный URL
    if relative_link.startswith("//"):
        url = "https:" + relative_link
    elif relative_link.startswith("/"):
        url = base_url + relative_link
    elif relative_link.startswith("http"):
        url = relative_link
    else:
        url = base_url + "/" + relative_link

    articles_found = []

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        toc_div = soup.find('div', class_='document-page__toc')
        if toc_div:
            a_tags = toc_div.find_all('a')
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(process_article, a, base_url, pattern, base_folder_path) for a in a_tags]
                for future in as_completed(futures):
                    res = future.result()
                    if res:
                        articles_found.append(res)
        else:
            print(f"Div 'document-page__toc' не найден на странице {url}")
    except requests.RequestException as e:
        print(f"Ошибка при запросе {url}: {e}")

    return articles_found

# Обработка всех документов параллельно
all_results = []
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(process_document, doc) for doc in documents]
    for future in as_completed(futures):
        res = future.result()
        all_results.extend(res)
        print(f"Обработано статей: {len(all_results)} из {len(documents)}")

# Сохраняем итоговый JSON
with open('output1.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, ensure_ascii=False, indent=4)'''


import requests
from bs4 import BeautifulSoup
import json
import re
import uuid  # импортируем модуль для генерации UUID

# Пути к вашим JSON файлам
json_files = ['laws.json', 'codeks.json']

# Заготовка для объединения данных из двух файлов
documents = []

# Чтение данных из двух файлов
for json_file in json_files:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        documents.extend(data)

base_url = "https://www.consultant.ru/"
result = []

# Регулярное выражение для извлечения номера статьи
pattern = re.compile('/document/cons_doc_LAW_(//d+)/')

for doc in documents:
    relative_link = doc.get("Ссылка")
    if not relative_link:
        continue

    # Обработка ссылок
    if relative_link.startswith("//"):  # протокол-относительная ссылка
        url = "https:" + relative_link
    elif relative_link.startswith("/"):  # абсолютная внутри сайта
        url = base_url + relative_link
    elif relative_link.startswith("http"):  # полная ссылка
        url = relative_link
    else:
        # возможный случай относительной ссылки без слэша
        url = base_url + "/" + relative_link

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        toc_div = soup.find('div', class_='document-page__toc')
        if toc_div:
            a_tags = toc_div.find_all('a')
            for a in a_tags:
                title = a.get_text(strip=True)
                href = a.get('href')
                article_number = None
                if href:
                    # Обработка href
                    if href.startswith("//"):
                        href_full = "https:" + href
                    elif href.startswith("/"):
                        href_full = base_url + href
                    elif href.startswith("http"):
                        href_full = href
                    else:
                        href_full = base_url + "/" + href

                    # Попытка извлечь номер статьи из href
                    match = pattern.search(href_full)
                    if match:
                        article_number = match.group(1)

                # Генерируем уникальный ID
                unique_id = str(uuid.uuid4())

                result.append({
                    "id": unique_id,  # Уникальный идентификатор
                    "Название": title,
                    "Ссылка": href_full if href else None,
                    "Номер_источника_статьи": article_number
                })
        else:
            print(f"Div 'document-page__toc' не найден на странице {url}")
    except requests.RequestException as e:
        print(f"Ошибка при запросе {url}: {e}")

# Запись результата
with open('output1.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)