import os
import sys
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = '8428983493:AAFt66StO-rEbvaALX0Moeq6EukcrTUtOz8'
BASE_PATH = 'data'

bot = telebot.TeleBot(TOKEN)

user_states = {}

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
                                folders.append({'name': title, 'folder_name': folder_name})
                        except:
                            continue
    return folders

def get_articles(folder_name):
    articles = []
    for subdir in ['codeks', 'laws']:
        folder_path = os.path.join(BASE_PATH, subdir, folder_name)
        if os.path.isdir(folder_path):
            try:
                for filename in os.listdir(folder_path):
                    if filename.startswith("Статья") and filename.endswith(".txt"):
                        parts = filename.split()
                        if len(parts) >= 2:
                            full_number = parts[1]
                            articles.append(full_number)
            except:
                continue
    return articles

def sort_articles(articles):
    def sort_key(num):
        try:
            n = int(num)
            if 1 <= n <= 9:
                return (0, n)
            else:
                return (1, n)
        except:
            parts = num.split('.')
            try:
                main = int(parts[0])
            except:
                main = 0
            return (2, main)
    return sorted(articles, key=sort_key)
@bot.message_handler(commands=['help'])
def help_handler(message):
    bot.send_message(
        message.chat.id,
        "Доступные команды:\n"
        "/start — начать работу и выбрать коллекцию\n"
        "/help — показать это сообщение\n\n"
        "Используйте кнопки для навигации по спискам и статьям."
    )
@bot.message_handler(commands=['start'])
def start_handler(message):
    folders = get_folders()
    if not folders:
        bot.send_message(message.chat.id, "Нет доступных папок.")
        return
    keyboard = InlineKeyboardMarkup()
    for folder in folders:
        keyboard.add(InlineKeyboardButton(folder['name'], callback_data=f"folder_{folder['folder_name']}"))
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=keyboard)
    user_states[message.chat.id] = {'stage': 'waiting_folder', 'folders_list': folders}

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    data = call.data

    if data == "back_to_folders":
        start_handler(call.message)
        bot.answer_callback_query(call.id)
        return

    elif data.startswith("folder_"):
        folder_name = data[len("folder_"):]
        # Сохраняем состояние как "на уровне папки"
        user_states[user_id] = {
            'stage': 'waiting_article_or_keywords',
            'folder_name': folder_name,
            'prev_state': 'folder_list'
        }
        articles = get_articles(folder_name)
        if not articles:
            bot.answer_callback_query(call.id, "Нет статей для этой папки.")
            return
        try:
            articles_sorted = sort_articles(articles)
        except:
            articles_sorted = sorted(articles)
        keyboard = InlineKeyboardMarkup()
        for a in articles_sorted:
            display_name = a.rstrip('.')
            keyboard.add(InlineKeyboardButton(f"Статья {display_name}", callback_data=f"article_{a}_{folder_name}"))
        # Убрана кнопка "Назад"
        bot.edit_message_text("Выберите номер статьи:",
                              chat_id=user_id,
                              message_id=call.message.message_id,
                              reply_markup=keyboard)

    elif data.startswith("article_"):
        parts = data.split('_')
        if len(parts) >= 3:
            article_number = parts[1]
            folder_name = parts[2]
            # Загружаем статью
            file_content = None
            folder_paths = [
                os.path.join(BASE_PATH, 'codeks', folder_name),
                os.path.join(BASE_PATH, 'laws', folder_name)
            ]
            file_found = False
            for folder_path in folder_paths:
                if os.path.isdir(folder_path):
                    try:
                        for filename in os.listdir(folder_path):
                            if f"Статья {article_number}" in filename:
                                with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                                file_found = True
                                break
                        if file_found:
                            break
                    except:
                        continue
            if file_found:
                max_length = 4000
                parts_content = [file_content[i:i+max_length] for i in range(0, len(file_content), max_length)]
                for part in parts_content:
                    bot.send_message(user_id, part)
                bot.send_message(user_id, "Для возврата к списку статей введите /start или повторите выбор папки.")
            else:
                bot.send_message(user_id, f"Статья {article_number} не найдена.")

        elif len(parts) == 4 and parts[0] == 'next':
            current_number = parts[1]
            folder_name = parts[2]
            articles = get_articles(folder_name)
            sorted_articles = sort_articles(articles)
            try:
                index = sorted_articles.index(current_number)
                next_article = sorted_articles[index + 1]
            except (ValueError, IndexError):
                bot.answer_callback_query(call.id, "Нет следующей статьи.")
                return
            call.data = f"article_{next_article}_{folder_name}"
            callback_handler(call)

        elif len(parts) == 3 and parts[0] == 'back':
            folder_name = parts[1]
            user_states[user_id] = {
                'stage': 'waiting_article_or_keywords',
                'folder_name': folder_name,
                'prev_state': 'article_view'
            }
            # Возврат к списку статей
            articles = get_articles(folder_name)
            if not articles:
                bot.answer_callback_query(call.id, "Нет статей для этой папки.")
                return
            try:
                articles_sorted = sort_articles(articles)
            except:
                articles_sorted = sorted(articles)
            keyboard = InlineKeyboardMarkup()
            for a in articles_sorted:
                display_name = a.rstrip('.')
                keyboard.add(InlineKeyboardButton(f"Статья {display_name}", callback_data=f"article_{a}_{folder_name}"))
            bot.edit_message_text("Выберите номер статьи или введите ключевые слова:",
                                  chat_id=user_id,
                                  message_id=call.message.message_id,
                                  reply_markup=keyboard)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_id = message.chat.id
    state = user_states.get(user_id, {})
    stage = state.get('stage')

    if stage == 'waiting_article_or_keywords':
        text = message.text.strip()
        if text.startswith("Статья"):
            pass
        else:
            keywords = text.lower().split()
            folder_name = state.get('folder_name')
            if not folder_name:
                bot.send_message(user_id, "Ошибка: не выбрана папка. Введите /start.")
                return
            found_content = []
            for folder_path in [os.path.join(BASE_PATH, 'codeks', folder_name), os.path.join(BASE_PATH, 'laws', folder_name)]:
                if os.path.isdir(folder_path):
                    try:
                        for filename in os.listdir(folder_path):
                            if filename.endswith('.txt'):
                                with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    if all(k in content.lower() for k in keywords):
                                        found_content.append((filename, content))
                    except:
                        continue
            if found_content:
                for filename, content in found_content:
                    max_length = 4000
                    parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]
                    for part in parts:
                        bot.send_message(user_id, f"Результат из файла {filename}:\n{part}")
            else:
                bot.send_message(user_id, "По ключевым словам ничего не найдено.")
            user_states.pop(user_id, None)
            bot.send_message(user_id, "Введите /start для нового поиска.", reply_markup=None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("back_"))
def handle_back(call):
    user_id = call.message.chat.id
    data = call.data
    # Обработка возврата
    if data == "back_to_folders":
        start_handler(call.message)
        bot.answer_callback_query(call.id)
    elif data.startswith("back_to_articles_"):
        # Возврат к списку статей выбранной папки
        parts = data.split('_', 3)
        if len(parts) == 4:
            folder_name = parts[3]
            user_states[user_id] = {
                'stage': 'waiting_article_or_keywords',
                'folder_name': folder_name,
                'prev_state': 'article_list'
            }
            articles = get_articles(folder_name)
            if not articles:
                bot.answer_callback_query(call.id, "Нет статей для этой папки.")
                return
            try:
                articles_sorted = sort_articles(articles)
            except:
                articles_sorted = sorted(articles)
            keyboard = InlineKeyboardMarkup()
            for a in articles_sorted:
                display_name = a.rstrip('.')
                keyboard.add(InlineKeyboardButton(f"Статья {display_name}", callback_data=f"article_{a}_{folder_name}"))
            bot.edit_message_text("Выберите номер статьи:",
                                  chat_id=user_id,
                                  message_id=call.message.message_id,
                                  reply_markup=keyboard)
        else:
            bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id)

# Запускаем бота бесконечно
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка: {e}")
               
