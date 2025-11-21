import os
import telebot

TOKEN = '8428983493:AAFt66StO-rEbvaALX0Moeq6EukcrTUtOz8'
BASE_PATH = 'data'  # Путь к папке, где хранятся 'codeks' и 'laws'

bot = telebot.TeleBot(TOKEN)

user_states = {}  # Хранение состояний пользователей

def parse_info_block(info_path):
    title = None
    link = None
    try:
        with open(info_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("Название:"):
                    title = line[len("Название:"):].strip()
                elif line.startswith("Ссылка:"):
                    link = line[len("Ссылка:"):].strip()
    except Exception as e:
        print(f"Ошибка при чтении {info_path}: {e}")
    return title, link

def get_folders():
    # Возвращает список словарей: [{'name': 'Название', 'folder_name': 'номер_папки'}, ...]
    folders = []
    for subdir in ['codeks', 'laws']:
        path = os.path.join(BASE_PATH, subdir)
        if os.path.exists(path):
            for folder_name in os.listdir(path):
                folder_path = os.path.join(path, folder_name)
                if os.path.isdir(folder_path):
                    info_path = os.path.join(folder_path, 'info.txt')
                    if os.path.isfile(info_path):
                        try:
                            title, link = parse_info_block(info_path)
                            if title:
                                folders.append({
                                    'name': title,
                                    'folder_name': folder_name
                                })
                        except:
                            continue
    return folders

def get_articles(folder_number):
    # Возвращает список номеров статей в папке
    articles = []
    for subdir in ['codeks', 'laws']:
        folder_path = os.path.join(BASE_PATH, subdir, folder_number)
        if os.path.isdir(folder_path):
            try:
                for filename in os.listdir(folder_path):
                    if filename.startswith("Статья") and filename.endswith(".txt"):
                        parts = filename.split()
                        if len(parts) >= 2:
                            full_number = parts[1]  # например "6" или "6.1"
                            articles.append(full_number)
            except:
                continue
    return articles

def sort_articles(articles):
    def sort_key(num):
        try:
            n = int(num)
            if 1 <= n <= 9:
                return (0, n)  # сначала 1-9
            else:
                return (1, n)  # остальные
        except:
            # Для номеров с точками типа "6.1" или некорректных
            parts = num.split('.')
            try:
                main = int(parts[0])
            except:
                main = 0
            return (2, main)
    return sorted(articles, key=sort_key)

@bot.message_handler(commands=['start'])
def start_handler(message):
    folders = get_folders()
    if not folders:
        bot.send_message(message.chat.id, "Нет доступных папок.")
        return
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for folder in folders:
        markup.add(telebot.types.KeyboardButton(folder['name']))
    bot.send_message(message.chat.id, "Выберите название коллекции:", reply_markup=markup)
    user_states[message.chat.id] = {'stage': 'waiting_folder', 'folders_list': folders}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    state = user_states.get(user_id, {})
    stage = state.get('stage')

    if stage == 'waiting_folder':
        selected_name = message.text.strip()
        folders = user_states[user_id]['folders_list']
        folder_info = next((f for f in folders if f['name'] == selected_name), None)
        if not folder_info:
            bot.send_message(user_id, "Пожалуйста, выберите название из списка.")
            return
        user_states[user_id]['folder_name'] = folder_info['folder_name']
        articles = get_articles(folder_info['folder_name'])
        if not articles:
            bot.send_message(user_id, "Нет статей для этой папки. Попробуйте другую.")
            return
        # Сортируем список статей по возрастанию
        try:
            articles_sorted = sort_articles(articles)
        except:
            articles_sorted = sorted(articles)
        # Разделяем статьи на две группы: 1-9 и остальные
        articles_1_9 = [a for a in articles_sorted if a.isdigit() and 1 <= int(a) <= 9]
        articles_rest = [a for a in articles_sorted if not (a.isdigit() and 1 <= int(a) <= 9)]
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        # Добавляем кнопки с 1 по 9
        for article in articles_1_9:
            display_name = article
            if display_name.endswith('.'):
                display_name = display_name[:-1]
            markup.add(telebot.types.KeyboardButton(f"Статья {display_name}"))
        # Добавляем остальные
        for article in articles_rest:
            display_name = article
            if display_name.endswith('.'):
                display_name = display_name[:-1]
            markup.add(telebot.types.KeyboardButton(f"Статья {display_name}"))
        bot.send_message(user_id, "Выберите номер статьи:", reply_markup=markup)
        user_states[user_id]['stage'] = 'waiting_article'
    elif stage == 'waiting_article':
        text = message.text.strip()
        if not text.startswith("Статья"):
            bot.send_message(user_id, "Пожалуйста, выберите номер статьи из списка.")
            return
        article_number = text.split()[-1]
        # Убираем точку в конце номера, если есть
        article_display = article_number
        if article_display.endswith('.'):
            article_display = article_display[:-1]
        folder_number = user_states.get(user_id, {}).get('folder_name')
        if not folder_number:
            bot.send_message(user_id, "Ошибка: номер папки не найден. Начинайте заново командой /start.")
            return

        folder_paths = [
            os.path.join(BASE_PATH, 'codeks', folder_number),
            os.path.join(BASE_PATH, 'laws', folder_number)
        ]

        file_found = False
        content = ""

        for folder_path in folder_paths:
            if os.path.isdir(folder_path):
                try:
                    for filename in os.listdir(folder_path):
                        if f"Статья {article_number}" in filename:
                            file_path = os.path.join(folder_path, filename)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            file_found = True
                            break
                    if file_found:
                        break
                except:
                    continue

        if file_found:
            max_length = 4000
            parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]
            for part in parts:
                bot.send_message(user_id, part)
        else:
            bot.send_message(user_id, f"Статья {article_display} не найдена в выбранной папке.")

        # После ответа сбрасываем состояние
        bot.send_message(user_id, "Если хотите продолжить, введите /start", reply_markup=telebot.types.ReplyKeyboardRemove())
        user_states.pop(user_id, None)
    else:
        bot.send_message(user_id, "Пожалуйста, используйте команду /start для начала.")

bot.polling()