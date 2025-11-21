import os
import requests
from bs4 import BeautifulSoup
import json
import uuid
import re

# Создаем основную папку data
os.makedirs('data', exist_ok=True)
# Создаем основные папки
os.makedirs('data/laws', exist_ok=True)
os.makedirs('data/codeks', exist_ok=True)

url = 'https://www.consultant.ru/'  # ваш URL
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    ul_lists = soup.find_all('ul', class_='useful-links__list_dashed')

    results = []

    total_ul = len(ul_lists)

    # Регулярное выражение для извлечения номера из ссылки
    pattern = re.compile(r'/document/cons_doc_LAW_(\d+)/')

    for index, ul in enumerate(ul_lists):
        # Пропускаем последний список
        if index == total_ul - 1:
            continue

        for li in ul.find_all('li'):
            a = li.find('a')
            if a:
                title_raw = a.get_text()
                title_clean = title_raw.replace('\xa0', ' ').strip()
                link = a['href']
                # Попытка извлечь номер из ссылки
                match = pattern.search(link)
                if match:
                    номер = match.group(1)
                else:
                    номер = None

                # Генерируем уникальный ID
                unique_id = str(uuid.uuid4())

                results.append({
                    'id': unique_id,
                    'Название': title_clean,
                    'Ссылка': link,
                    'Номер': номер
                })

    # Делим список пополам
    mid_point = len(results) // 2
    first_half = results[:mid_point]
    second_half = results[mid_point:]

    # Сохраняем в папки laws и codeks
    laws_dir = 'data/laws'
    codeks_dir = 'data/codeks'

    with open(f'{laws_dir}/laws.json', 'w', encoding='utf-8') as f1:
        json.dump(first_half, f1, ensure_ascii=False, indent=4)

    with open(f'{codeks_dir}/codeks.json', 'w', encoding='utf-8') as f2:
        json.dump(second_half, f2, ensure_ascii=False, indent=4)

    print('Данные успешно сохранены в файлы laws.json и codeks.json внутри соответствующих папок.')

    # Создаем папки для каждого номера внутри laws и codeks
    for item in results:
        номер = item['Номер']
        if номер:
            # Определяем, в какую папку сохраняем: laws или codeks
            in_first_half = any(i['id'] == item['id'] for i in first_half)
            folder_name = 'laws' if in_first_half else 'codeks'
            save_dir = os.path.join('data', folder_name, номер)
            os.makedirs(save_dir, exist_ok=True)
            # Можно сохранить файл с информацией
            with open(os.path.join(save_dir, 'info.txt'), 'w', encoding='utf-8') as f:
                f.write(f"Название: {item['Название']}\nСсылка: {item['Ссылка']}\n")
else:
    print(f'Ошибка при загрузке страницы: {response.status_code}')