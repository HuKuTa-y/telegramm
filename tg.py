import psycopg2
from psycopg2.extras import RealDictCursor
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Токен вашего бота
TOKEN = '8428983493:AAFt66StO-rEbvaALX0Moeq6EukcrTUtOz8'
bot = telebot.TeleBot(TOKEN)

# Параметры подключения к PostgreSQL
conn_params = {
    'dbname': 'telegram',
    'user': 'patient',
    'password': '111',
    'host': 'localhost',
    'port': 5432
}

# --- Функции работы с базой данных ---

def get_folders():
    """Получает список папок из таблиц laws и coseks"""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT DISTINCT Nomer FROM laws")
            laws_folders = cur.fetchall()
            cur.execute("SELECT DISTINCT Nomer FROM coseks")
            coseks_folders = cur.fetchall()
    folder_names = set()
    for f in laws_folders + coseks_folders:
        folder_names.add(f['Nomer'])
    return [{'name': n, 'folder_name': n} for n in folder_names]

def get_articles(folder_name):
    """Получает список статей для папки"""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT Nomer_источника_статьи FROM articles WHERE Nomer_источника_статьи=%s", (folder_name,))
            articles = cur.fetchall()
    return [a['Nomer_источника_статьи'] for a in articles]

def get_article_content(folder_name, article_number):
    """Получает название и содержание статьи"""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT название, контент FROM texts WHERE название ILIKE %s", (f"%{article_number}%",))
            result = cur.fetchone()
            if result:
                return result[0], result[1]
            else:
                return None, None

def search_in_content(keyword):
    """Поиск по содержимому статей по ключевому слову"""
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT название, контент FROM texts WHERE контент ILIKE %s", (f"%{keyword}%",))
            return cur.fetchall()

# --- Обработчики команд и callback ---

@bot.message_handler(commands=['help'])
def help_handler(message):
    bot.send_message(
        message.chat.id,
        "Доступные команды:\n"
        "/start — выбрать категорию\n"
        "/help — помощь\n\n"
        "Используйте кнопки для навигации."
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("folder_"))
def handle_folder_callback(call):
    folder_name = call.data[len("folder_"):]
    articles = get_articles(folder_name)
    if not articles:
        bot.answer_callback_query(call.id, "Нет статей для этой папки.")
        return
    articles_sorted = sorted(articles, key=lambda x: int(x) if x.isdigit() else x)
    keyboard = InlineKeyboardMarkup()
    for a in articles_sorted:
        display_name = a.rstrip('.')
        keyboard.add(InlineKeyboardButton(f"Статья {display_name}", callback_data=f"article_{a}_{folder_name}"))
    bot.edit_message_text("Выберите номер статьи:",
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("article_"))
def handle_article_callback(call):
    parts = call.data.split('_')
    if len(parts) >= 3:
        article_number = parts[1]
        folder_name = parts[2]
        title, content = get_article_content(folder_name, article_number)
        if content:
            max_length = 4000
            parts_content = [content[i:i+max_length] for i in range(0, len(content), max_length)]
            for part in parts_content:
                bot.send_message(call.message.chat.id, part)
        else:
            bot.send_message(call.message.chat.id, "Статья не найдена.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip().lower()
    if text.startswith("искать") or text.startswith("поиск"):
        keyword = text.replace("искать", "").replace("поиск", "").strip()
        results = search_in_content(keyword)
        if results:
            for title, content in results:
                max_length = 4000
                parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]
                for part in parts:
                    bot.send_message(message.chat.id, f"{title}:\n{part}")
        else:
            bot.send_message(message.chat.id, "Ничего не найдено по ключевому слову.")
    else:
        bot.send_message(message.chat.id, "Введите команду или ключевое слово для поиска.")

# --- Запуск бота ---
if __name__ == '__main__':
    bot.polling(none_stop=True)
