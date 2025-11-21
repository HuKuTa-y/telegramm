
'''import json
import os
import requests
from bs4 import BeautifulSoup

# Путь к вашему JSON файлу
json_path = 'articles.json'  # замените на ваш путь

# Папка для сохранения файлов
output_dir = 'data'
os.makedirs(output_dir, exist_ok=True)

# Чтение JSON файла
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Обработка каждой записи
for item in data:
    title = item['Название']
    link = item['Ссылка']
    
    try:
        # Получаем страницу
        response = requests.get(link)
        response.raise_for_status()  # проверка ошибок
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим нужный блок
        content_div = soup.find('div', class_='document-page__content document-page_left-padding')
        if content_div:
            content_text = content_div.get_text(separator='\n', strip=True)
        else:
            content_text = 'Контент не найден'
            print(f"Не найден блок на странице: {link}")
        
        # Формируем имя файла
        filename = f"{title}.txt"
        filename = filename.replace('/', '_').replace('\\', '_').replace(':', '_')  # убираем запрещенные символы
        file_path = os.path.join(output_dir, filename)
        
        # Записываем в файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_text)
        
        print(f"Сохранено: {file_path}")
    except Exception as e:
        print(f"Ошибка при обработке {link}: {e}")'''


import json
import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup

json_path = 'articles.json'  # замените на ваш путь

base_dir = 'data'
laws_dir = os.path.join(base_dir, 'laws')
codeks_dir = os.path.join(base_dir, 'codeks')

# Собираем все подпапки внутри 'laws' и 'codeks' в словарь для быстрого поиска
folder_map = {}
for parent_folder in [laws_dir, codeks_dir]:
    if os.path.exists(parent_folder):
        for subfolder in os.listdir(parent_folder):
            subfolder_path = os.path.join(parent_folder, subfolder)
            if os.path.isdir(subfolder_path):
                folder_map[subfolder] = subfolder_path

# Читаем JSON
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
        return None

async def process_article(session, item):
    title = item['Название']
    link = item['Ссылка']
    source_number = str(item['Номер_источника_статьи']).strip()

    html = await fetch(session, link)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        content_div = soup.find('div', class_='document-page__content document-page_left-padding')
        if content_div:
            content_text = content_div.get_text(separator='\n', strip=True)
        else:
            content_text = 'Контент не найден'
            print(f"Не найден блок на странице: {link}")

        target_folder = folder_map.get(source_number)
        if target_folder:
            filename = f"{title}.txt"
            filename = filename.replace('/', '_').replace('\\', '_').replace(':', '_')
            file_path = os.path.join(target_folder, filename)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content_text)
                print(f"Сохранено: {file_path}")
            except Exception as e:
                print(f"Ошибка при сохранении файла {file_path}: {e}")
        else:
            print(f"Папка с номером '{source_number}' не найдена для статьи: {title}")

async def main():
    connector = aiohttp.TCPConnector(limit=20)  # лимит одновременных соединений
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [process_article(session, item) for item in data]
        await asyncio.gather(*tasks)

# Запускаем асинхронную обработку
asyncio.run(main())