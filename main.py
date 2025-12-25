import telebot
from telebot import types
import sqlite3
import secrets
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8228572975:AAEbORyz21h2bAXBo2G-sSNtvHex10gWtAQ"
bot = telebot.TeleBot(TOKEN)


def get_db_connection():
    conn = sqlite3.connect("Table_of_users.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def get_db_conn_logins():
    connL = sqlite3.connect("Table_of_logins.db", check_same_thread=False)
    connL.execute("PRAGMA journal_mode=WAL")
    return connL


def get_db_conn_folders():
    connF = sqlite3.connect("Table_of_folders.db", check_same_thread=False)
    connF.execute("PRAGMA journal_mode=WAL")
    return connF


def init_db():
    # Таблица пользователей
    db = sqlite3.connect("Table_of_users.db")
    cursor = db.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Table_of_users
                   (
                       telegram_id
                       INTEGER UNIQUE NOT NULL,
                       name
                       TEXT,
                       email
                       TEXT,
                       master_password
                       TEXT
                       NOT
                       NULL
                   )
                   ''')
    db.commit()
    db.close()

    # Таблица логинов
    db = sqlite3.connect("Table_of_logins.db")
    cursor = db.cursor()

    # Удаляем старую таблицу и создаем новую с правильной структурой
    cursor.execute('DROP TABLE IF EXISTS Table_of_logins')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Table_of_logins
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       telegram_id
                       INTEGER
                       NOT
                       NULL,
                       nameoflogin
                       TEXT
                       NOT
                       NULL,
                       nameuser
                       TEXT,
                       password
                       TEXT,
                       folder_id
                       INTEGER
                       DEFAULT
                       0,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')
    db.commit()
    db.close()

    # Таблица папок
    db = sqlite3.connect("Table_of_folders.db")
    cursor = db.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Table_of_folders
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       telegram_id
                       INTEGER
                       NOT
                       NULL,
                       folder_name
                       TEXT
                       NOT
                       NULL,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')
    db.commit()
    db.close()

    # Таблица для хранения статуса 2FA пользователей
    db = sqlite3.connect("Table_of_2fa.db")
    cursor = db.cursor()
    cursor.execute('''
                      CREATE TABLE IF NOT EXISTS Table_loggs
                      (
                          telegram_id INTEGER UNIQUE NOT NULL,
                          ,
                          log_in TEXT,
                          Log_out TEXT,
                          Active TEXT,
                          )
                      )
                      ''')
    db.commit()
    db.close()


init_db()


def Check_id(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT telegram_id FROM Table_of_users WHERE telegram_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result


def generate_password(length=12):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))


@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    result = Check_id(message)
    if result:
        bot.send_message(message.chat.id, "Добро пожаловать обратно")
        start_menu(message)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO Table_of_users(telegram_id, master_password) VALUES (?, ?)',
                       (user_id, ""))
        conn.commit()
        conn.close()
        start_menu(message)


@bot.callback_query_handler(func=lambda call: call.data in ["login", "register"])
def ask_for_name(call):
    result = Check_id(call.message)
    if call.data == "login":
        msg = bot.send_message(call.message.chat.id, 'Введите ваше имя:')
        bot.register_next_step_handler(msg, check_name_for_login)
    elif call.data == "register":
        if result:
            bot.send_message(call.message.chat.id, "У вас уже есть аккаунт. Пожалуйста, выполните вход.")
            start_menu(call.message)
        else:
            msg = bot.send_message(call.message.chat.id, 'Введите имя для регистрации:')
            bot.register_next_step_handler(msg, check_name_for_register)


def check_name_for_login(message):
    user_id = message.from_user.id
    name = message.text.strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM Table_of_users WHERE name = ? AND telegram_id = ?', (name, user_id))
    result = cursor.fetchone()

    if result:
        msg = bot.send_message(message.chat.id, "Введите мастер-пароль:")
        bot.register_next_step_handler(msg, get_pass, user_id)
    else:
        msg = bot.send_message(message.chat.id, "Имя не найдено. Попробуйте снова:")
        bot.register_next_step_handler(msg, check_name_for_login)
    conn.close()


def get_pass(message, user_id):
    password = message.text.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT master_password FROM Table_of_users WHERE master_password = ? AND telegram_id = ?',
                   (password, user_id))
    result = cursor.fetchone()

    if result:
        show_menu(message, "Главное меню")
    else:
        msg = bot.send_message(message.chat.id, "Неверный пароль. Попробуйте снова:")
        bot.register_next_step_handler(msg, get_pass, user_id)
    conn.close()


def check_name_for_register(message):
    user_id = message.from_user.id
    name = message.text.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT name FROM Table_of_users WHERE name = ? AND telegram_id != ?', (name, user_id))
    result = cursor.fetchone()

    if result:
        msg = bot.send_message(message.chat.id, "Имя занято. Введите другое:")
        bot.register_next_step_handler(msg, check_name_for_register)
    else:
        cursor.execute('UPDATE Table_of_users SET name = ? WHERE telegram_id = ?', (name, user_id))
        conn.commit()
        msg = bot.send_message(message.chat.id, "Введите email:")
        bot.register_next_step_handler(msg, get_email, user_id)
    conn.close()


def get_email(message, user_id):
    email = message.text.strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT email FROM Table_of_users WHERE email = ? AND telegram_id != ?', (email, user_id))
    result = cursor.fetchone()

    if result:
        msg = bot.send_message(message.chat.id, "Этот email уже используется. Введите другой:")
        bot.register_next_step_handler(msg, get_email, user_id)
        conn.close()
        return
    else:
        cursor.execute('UPDATE Table_of_users SET email = ? WHERE telegram_id = ?', (email, user_id))
        conn.commit()
        conn.close()
        msg = bot.send_message(message.chat.id, "Придумайте мастер-пароль (минимум 8 символов):")
        bot.register_next_step_handler(msg, passget, user_id)


def passget(message, user_id):
    usepass = message.text.strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    result = Check_id(message)
    if result:
        bot.send_message(message.chat.id, "Добро пожаловать обратно")
        start_menu(message)
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO Table_of_users(telegram_id, master_password) VALUES (?, ?)',
                       (user_id, ""))
        conn.commit()
        conn.close()
        start_menu(message)


@bot.callback_query_handler(func=lambda call: call.data in ["login", "register"])
def ask_for_name(call):
    result = Check_id(call.message)
    if call.data == "login":
        msg = bot.send_message(call.message.chat.id, 'Введите ваше имя:')
        bot.register_next_step_handler(msg, check_name_for_login)
    elif call.data == "register":
        if result:
            bot.send_message(call.message.chat.id, "У вас уже есть аккаунт. Пожалуйста, выполните вход.")
            start_menu(call.message)
        else:
            msg = bot.send_message(call.message.chat.id, 'Введите имя для регистрации:')
            bot.register_next_step_handler(msg, check_name_for_register)


def check_name_for_login(message):
    user_id = message.from_user.id
    name = message.text.strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM Table_of_users WHERE name = ? AND telegram_id = ?', (name, user_id))
    result = cursor.fetchone()

    if result:
        msg = bot.send_message(message.chat.id, "Введите мастер-пароль:")
        bot.register_next_step_handler(msg, get_pass, user_id)
    else:
        msg = bot.send_message(message.chat.id, "Имя не найдено. Попробуйте снова:")
        bot.register_next_step_handler(msg, check_name_for_login)
    conn.close()


def get_pass(message, user_id):
    password = message.text.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT master_password FROM Table_of_users WHERE master_password = ? AND telegram_id = ?',
                   (password, user_id))
    result = cursor.fetchone()

    if result:
        show_menu(message, "Главное меню")
    else:
        msg = bot.send_message(message.chat.id, "Неверный пароль. Попробуйте снова:")
        bot.register_next_step_handler(msg, get_pass, user_id)
    conn.close()


def check_name_for_register(message):
    user_id = message.from_user.id
    name = message.text.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT name FROM Table_of_users WHERE name = ? AND telegram_id != ?', (name, user_id))
    result = cursor.fetchone()

    if result:
        msg = bot.send_message(message.chat.id, "Имя занято. Введите другое:")
        bot.register_next_step_handler(msg, check_name_for_register)
    else:
        cursor.execute('UPDATE Table_of_users SET name = ? WHERE telegram_id = ?', (name, user_id))
        conn.commit()
        msg = bot.send_message(message.chat.id, "Введите email:")
        bot.register_next_step_handler(msg, get_email, user_id)
    conn.close()


def get_email(message, user_id):
    email = message.text.strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT email FROM Table_of_users WHERE email = ? AND telegram_id != ?', (email, user_id))
    result = cursor.fetchone()

    if result:
        msg = bot.send_message(message.chat.id, "Этот email уже используется. Введите другой:")
        bot.register_next_step_handler(msg, get_email, user_id)
        conn.close()
        return
    else:
        cursor.execute('UPDATE Table_of_users SET email = ? WHERE telegram_id = ?', (email, user_id))
        conn.commit()
        conn.close()
        msg = bot.send_message(message.chat.id, "Придумайте мастер-пароль (минимум 8 символов):")
        bot.register_next_step_handler(msg, passget, user_id)


def passget(message, user_id):
    usepass = message.text.strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    if len(usepass) < 8:
        msg = bot.send_message(message.chat.id, "Пароль должен быть не менее 8 символов. Введите другой:")
        bot.register_next_step_handler(msg, passget, user_id)
        conn.close()
        return

    cursor.execute('SELECT master_password FROM Table_of_users WHERE master_password = ? AND telegram_id != ?',
                   (usepass, user_id))
    result = cursor.fetchone()

    if result:
        msg = bot.send_message(message.chat.id, "Этот пароль уже используется. Введите другой:")
        bot.register_next_step_handler(msg, passget, user_id)
        conn.close()
        return
    else:
        cursor.execute('UPDATE Table_of_users SET master_password = ? WHERE telegram_id = ?', (usepass, user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, "Регистрация завершена")
        show_menu(message, "Главное меню")


def start_menu(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Вход", callback_data="login"),
        InlineKeyboardButton("Регистрация", callback_data="register")
    )
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)


def show_menu(message, text):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Создать логин", callback_data='create_login'),
        InlineKeyboardButton("Мои логины", callback_data='my_logins'),
        InlineKeyboardButton("Создать папку", callback_data='create_folder'),
        InlineKeyboardButton("Мои папки", callback_data='my_folders')
    )
    bot.send_message(message.chat.id, text, reply_markup=markup)


# Глобальные переменные для хранения временных данных
temp_data = {}


@bot.callback_query_handler(func=lambda call: True)
def handle_menu(call):
    user_id = call.from_user.id

    if call.data == "create_login":
        msg = bot.send_message(call.message.chat.id, "Введите название логина:")
        bot.register_next_step_handler(msg, create_login)

    elif call.data == "my_logins":
        view_logins(call.message, user_id)

    elif call.data == "create_folder":
        msg = bot.send_message(call.message.chat.id, "Введите название папки:")
        bot.register_next_step_handler(msg, create_folder)

    elif call.data == "my_folders":
        view_folders(call.message, user_id)

    elif call.data.startswith("view_logins_folder_"):
        folder_id = int(call.data.split("_")[-1])
        view_logins_in_folder(call.message, user_id, folder_id)

    elif call.data.startswith("add_login_to_folder_"):
        folder_id = int(call.data.split("_")[-1])
        msg = bot.send_message(call.message.chat.id, "Введите название логина для добавления в папку:")
        bot.register_next_step_handler(msg, add_login_to_folder, folder_id)

    elif call.data.startswith("delete_login_"):
        login_id = int(call.data.split("_")[-1])
        delete_login(call.message, user_id, login_id)

    elif call.data.startswith("delete_folder_"):
        folder_id = int(call.data.split("_")[-1])
        delete_folder(call.message, user_id, folder_id)

    elif call.data == "generate_password":
        gen_password = generate_password()
        msg = bot.send_message(call.message.chat.id,
                               f"Сгенерированный пароль: `{gen_password}`\n\nНажмите 'Продолжить', чтобы использовать его",
                               parse_mode="Markdown")
        # Сохраняем пароль во временные данные
        temp_data[user_id] = {'password': gen_password}
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Продолжить", callback_data="continue_with_generated"))
        bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)
    elif call.data == "continue_with_generated":
        if user_id in temp_data and 'password' in temp_data[user_id]:
            password = temp_data[user_id]['password']
            # Запрашиваем название логина
            msg = bot.send_message(call.message.chat.id, "Введите название логина:")
            bot.register_next_step_handler(msg, create_login_with_password, password)
        else:
            bot.send_message(call.message.chat.id, "Ошибка. Попробуйте снова.")

    elif call.data == "manual_password":
        msg = bot.send_message(call.message.chat.id, "Введите пароль вручную:")
        bot.register_next_step_handler(msg, get_manual_password)

    elif call.data == "back_to_menu":
        show_menu(call.message, "Главное меню")

    elif call.data == "delete_login_menu":
        show_delete_login_menu(call.message, user_id)

    elif call.data == "delete_folder_menu":
        show_delete_folder_menu(call.message, user_id)

def create_login(message):
    user_id = message.from_user.id
    namelogin = message.text.strip()

    if not namelogin:
        msg = bot.send_message(message.chat.id, "Название не может быть пустым. Введите название:")
        bot.register_next_step_handler(msg, create_login)
        return

    # Сохраняем название логина
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]['namelogin'] = namelogin

    msg = bot.send_message(message.chat.id, "Введите имя пользователя:")
    bot.register_next_step_handler(msg, create_login_get_name)

def create_login_with_password(message, password):
    user_id = message.from_user.id
    namelogin = message.text.strip()

    if not namelogin:
        msg = bot.send_message(message.chat.id, "Название не может быть пустым. Введите название:")
        bot.register_next_step_handler(msg, create_login_with_password, password)
        return

    # Сохраняем данные
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]['namelogin'] = namelogin
    temp_data[user_id]['password'] = password

    msg = bot.send_message(message.chat.id, "Введите имя пользователя:")
    bot.register_next_step_handler(msg, create_login_get_name_with_password, password)

def create_login_get_name_with_password(message, password):
    user_id = message.from_user.id
    nameuser = message.text.strip()

    if not nameuser:
        msg = bot.send_message(message.chat.id, "Имя пользователя не может быть пустым. Введите имя:")
        bot.register_next_step_handler(msg, create_login_get_name_with_password, password)
        return

    # Получаем сохраненное название логина
    namelogin = temp_data[user_id].get('namelogin', '')

    # Сохраняем в базу
    save_login_to_db(user_id, namelogin, nameuser, password, message)

    # Очищаем временные данные
    if user_id in temp_data:
        del temp_data[user_id]

def create_login_get_name(message):
    user_id = message.from_user.id
    nameuser = message.text.strip()

    if not nameuser:
        msg = bot.send_message(message.chat.id, "Имя пользователя не может быть пустым. Введите имя:")
        bot.register_next_step_handler(msg, create_login_get_name)
        return

    # Сохраняем имя пользователя
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]['nameuser'] = nameuser

    # Показываем меню выбора пароля
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Сгенерировать пароль", callback_data="generate_password"),
        InlineKeyboardButton("Ввести вручную", callback_data="manual_password")
    )
    bot.send_message(message.chat.id, "Выберите способ создания пароля:", reply_markup=markup)

def get_manual_password(message):
    user_id = message.from_user.id
    password = message.text.strip()

    if not password:
        msg = bot.send_message(message.chat.id, "Пароль не может быть пустым. Введите пароль:")
        bot.register_next_step_handler(msg, get_manual_password)
        return
    # Получаем сохраненные данные
    namelogin = temp_data[user_id].get('namelogin', '')
    nameuser = temp_data[user_id].get('nameuser', '')

    if not namelogin or not nameuser:
        bot.send_message(message.chat.id, "Ошибка данных. Начните заново.")
        show_menu(message, "Главное меню")
        return

    # Сохраняем в базу
    save_login_to_db(user_id, namelogin, nameuser, password, message)

    # Очищаем временные данные
    if user_id in temp_data:
        del temp_data[user_id]

def save_login_to_db(user_id, namelogin, nameuser, password, message):
    conn = get_db_conn_logins()
    cursor = conn.cursor()

    try:
        cursor.execute('''
                       INSERT INTO Table_of_logins (telegram_id, nameoflogin, nameuser, password)
                       VALUES (?, ?, ?, ?)
                       ''', (user_id, namelogin, nameuser, password))
        conn.commit()
        bot.send_message(message.chat.id, f"Логин '{namelogin}' сохранен")
        show_menu(message, "Главное меню")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")
    finally:
        conn.close()

def view_logins(message, user_id):
    conn = get_db_conn_logins()
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT id, nameoflogin, nameuser, password, folder_id
                   FROM Table_of_logins
                   WHERE telegram_id = ?
                   ORDER BY nameoflogin
                   ''', (user_id,))
    logins = cursor.fetchall()

    connF = get_db_conn_folders()
    cursorF = connF.cursor()
    cursorF.execute('SELECT id, folder_name FROM Table_of_folders WHERE telegram_id = ? ORDER BY folder_name',
                    (user_id,))
    folders = cursorF.fetchall()

    if not logins:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Назад", callback_data="back_to_menu"))
        bot.send_message(message.chat.id, "Логины не найдены", reply_markup=markup)
        conn.close()
        connF.close()
        return

    response = "Ваши логины:\n\n"

    # Логины без папки
    for login in logins:
        if login[4] == 0:  # folder_id = 0
            response += f"• {login[1]}\n"
            response += f"  Пользователь: {login[2]}\n"
            response += f"  Пароль: `{login[3]}`\n"
            response += f"  ID: {login[0]}\n\n"

    if folders:
        response += "\nПапки:\n"
        for folder in folders:
            response += f"• {folder[1]}\n"

    markup = InlineKeyboardMarkup(row_width=2)

    for folder in folders:
        folder_id, folder_name = folder
        markup.add(InlineKeyboardButton(folder_name, callback_data=f"view_logins_folder_{folder_id}"))

    markup.add(
        InlineKeyboardButton("Назад", callback_data="back_to_menu"),
        InlineKeyboardButton("Удалить", callback_data="delete_login_menu")
    )

    conn.close()
    connF.close()
    bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)

def view_logins_in_folder(message, user_id, folder_id):
    conn = get_db_conn_logins()
    cursor = conn.cursor()

    connF = get_db_conn_folders()
    cursorF = connF.cursor()
    cursorF.execute('SELECT folder_name FROM Table_of_folders WHERE id = ? AND telegram_id = ?',
                    (folder_id, user_id))
    folder = cursorF.fetchone()

    if not folder:
        bot.send_message(message.chat.id, "Папка не найдена")
        return

    folder_name = folder[0]

    cursor.execute('''
                   SELECT id, nameoflogin, nameuser, password
                   FROM Table_of_logins
                   WHERE telegram_id = ?
                     AND folder_id = ?
                   ORDER BY nameoflogin
                   ''', (user_id, folder_id))
    logins = cursor.fetchall()
    if not logins:
        response = f"Папка: {folder_name}\n\nЛогины не найдены"
    else:
        response = f"Папка: {folder_name}\n\n"
        for login in logins:
            response += f"• {login[1]}\n"
            response += f"  Пользователь: {login[2]}\n"
            response += f"  Пароль: `{login[3]}`\n"
            response += f"  ID: {login[0]}\n\n"

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Добавить логин", callback_data=f"add_login_to_folder_{folder_id}"),
        InlineKeyboardButton("Удалить папку", callback_data=f"delete_folder_{folder_id}")
    )
    markup.add(
        InlineKeyboardButton("Назад к папкам", callback_data="my_folders"),
        InlineKeyboardButton("Главное меню", callback_data="back_to_menu")
    )

    conn.close()
    connF.close()
    bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=markup)


def create_folder(message):
    user_id = message.from_user.id
    folder_name = message.text.strip()

    if not folder_name:
        msg = bot.send_message(message.chat.id, "Название не может быть пустым. Введите название:")
        bot.register_next_step_handler(msg, create_folder)
        return

    conn = get_db_conn_folders()
    cursor = conn.cursor()

    cursor.execute('SELECT folder_name FROM Table_of_folders WHERE telegram_id = ? AND folder_name = ?',
                   (user_id, folder_name))
    existing = cursor.fetchone()

    if existing:
        msg = bot.send_message(message.chat.id, "Папка с таким именем уже существует. Введите другое название:")
        bot.register_next_step_handler(msg, create_folder)
        conn.close()
        return

    cursor.execute('INSERT INTO Table_of_folders (telegram_id, folder_name) VALUES (?, ?)', (user_id, folder_name))
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, f"Папка '{folder_name}' создана")
    show_menu(message, "Главное меню")


def view_folders(message, user_id):
    conn = get_db_conn_folders()
    cursor = conn.cursor()

    cursor.execute('SELECT id, folder_name FROM Table_of_folders WHERE telegram_id = ? ORDER BY folder_name',
                   (user_id,))
    folders = cursor.fetchall()

    if not folders:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Назад", callback_data="back_to_menu"))
        bot.send_message(message.chat.id, "Папки не найдены", reply_markup=markup)
        conn.close()
        return

    response = "Ваши папки:\n\n"
    for folder in folders:
        response += f"• {folder[1]}\n"

    markup = InlineKeyboardMarkup(row_width=2)

    for folder in folders:
        folder_id, folder_name = folder
        markup.add(InlineKeyboardButton(folder_name, callback_data=f"view_logins_folder_{folder_id}"))

    markup.add(
        InlineKeyboardButton("Назад", callback_data="back_to_menu"),
        InlineKeyboardButton("Удалить", callback_data="delete_folder_menu")
    )

    conn.close()
    bot.send_message(message.chat.id, response, reply_markup=markup)


def add_login_to_folder(message, folder_id):
    user_id = message.from_user.id
    login_name = message.text.strip()

    conn = get_db_conn_logins()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM Table_of_logins WHERE telegram_id = ? AND nameoflogin = ? AND folder_id = 0',
                   (user_id, login_name))
    login = cursor.fetchone()

    if not login:
        bot.send_message(message.chat.id, f"Логин '{login_name}' не найден")
        conn.close()
        return

    login_id = login[0]

    try:
        cursor.execute('UPDATE Table_of_logins SET folder_id = ? WHERE id = ?', (folder_id, login_id))
        conn.commit()
        bot.send_message(message.chat.id, f"Логин '{login_name}' добавлен в папку")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")
    finally:
        conn.close()

    view_folders(message, user_id)


def show_delete_login_menu(message, user_id):
    conn = get_db_conn_logins()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nameoflogin FROM Table_of_logins WHERE telegram_id = ? ORDER BY nameoflogin',
                   (user_id,))
    logins = cursor.fetchall()

    if not logins:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Назад", callback_data="my_logins"))
        bot.send_message(message.chat.id, "Логины не найдены", reply_markup=markup)
        conn.close()
        return

    markup = InlineKeyboardMarkup(row_width=2)

    for login in logins:
        login_id, nameoflogin = login
        markup.add(InlineKeyboardButton(nameoflogin, callback_data=f"delete_login_{login_id}"))

    markup.add(InlineKeyboardButton("Назад", callback_data="my_logins"))

    conn.close()
    bot.send_message(message.chat.id, "Выберите логин для удаления:", reply_markup=markup)


def delete_login(message, user_id, login_id):
    conn = get_db_conn_logins()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM Table_of_logins WHERE id = ? AND telegram_id = ?', (login_id, user_id))
        conn.commit()
        bot.send_message(message.chat.id, "Логин удален")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {str(e)}")
    finally:
        conn.close()

    view_logins(message, user_id)


def show_delete_folder_menu(message, user_id):
    conn = get_db_conn_folders()
    cursor = conn.cursor()

    cursor.execute('SELECT id, folder_name FROM Table_of_folders WHERE telegram_id = ? ORDER BY folder_name',
                   (user_id,))
    folders = cursor.fetchall()

    if not folders:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Назад", callback_data="my_folders"))
        bot.send_message(message.chat.id, "Папки не найдены", reply_markup=markup)
        conn.close()
        return

    markup = InlineKeyboardMarkup(row_width=2)

    for folder in folders:
        folder_id, folder_name = folder
        markup.add(InlineKeyboardButton(folder_name, callback_data=f"delete_folder_{folder_id}"))

    markup.add(InlineKeyboardButton("Назад", callback_data="my_folders"))

    conn.close()
    bot.send_message(message.chat.id, "Выберите папку для удаления:", reply_markup=markup)


def delete_folder(message, user_id, folder_id):
    conn = get_db_conn_folders()
    cursor = conn.cursor()

    cursor.execute('SELECT folder_name FROM Table_of_folders WHERE id = ? AND telegram_id = ?', (folder_id, user_id))
    folder = cursor.fetchone()

    if not folder:
        bot.send_message(message.chat.id, "Папка не найдена")
        return

    folder_name = folder[0]

    cursor.execute('DELETE FROM Table_of_folders WHERE id = ? AND telegram_id = ?', (folder_id, user_id))
    conn.commit()
    conn.close()

    connL = get_db_conn_logins()
    cursorL = connL.cursor()
    cursorL.execute('UPDATE Table_of_logins SET folder_id = 0 WHERE telegram_id = ? AND folder_id = ?',
                    (user_id, folder_id))
    connL.commit()
    connL.close()

    bot.send_message(message.chat.id, f"Папка '{folder_name}' удалена")
    view_folders(message, user_id)


bot.polling(none_stop=True)