from db_usage import *
import telebot
from telebot import types

bot = telebot.TeleBot('6049690859:AAEXKrZV3i6qQtWBPzO7Tm8J9RzuMImSrIs')

store_id = 1
command = ''


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Обработчик команды /start. Запрашивает у пользователя имя, фамилию и ник.
    """
    bot.send_message(message.chat.id, "Привет! Пожалуйста, введите ваше имя, фамилию и ник.")
    bot.register_next_step_handler(message, process_name)


def process_name(message):
    """
    Обработчик ввода имени пользователем.
    """
    name = message.text
    bot.send_message(message.chat.id, "Отлично! Теперь, пожалуйста, введите вашу фамилию.")
    bot.register_next_step_handler(message, process_surname, name=name)


def process_surname(message, name):
    """
    Обработчик ввода фамилии пользователем.
    """
    surname = message.text
    bot.send_message(message.chat.id, "Спасибо! И последнее - введите ваш ник.")
    bot.register_next_step_handler(message, process_nickname, name=name, surname=surname)


def process_nickname(message, name, surname):
    """
    Обработчик ввода ника пользователем.
    """
    nickname = message.text
    curs = connection()
    # Сохраняем данные пользователя в базу данных
    save_user_data(name, surname, nickname, curs)

    bot.send_message(message.chat.id, "Ваши данные успешно сохранены!")


def save_user_data(name: str, surname: str, nickname: str, connect: cursor) -> None:
    """
    Функция для сохранения данных пользователя в базу данных.
    """
    try:
        print("Вставляем данные пользователя в таблицу Login...")
        connect.execute('INSERT INTO "Login" ("Login", "Password") VALUES (%s, %s) RETURNING "ClientID";',
                        (nickname, 'default_password'))
        client_id = connect.fetchone()[0]
        print(f"ClientID: {client_id}")

        print("Вставляем данные пользователя в таблицу Player...")
        connect.execute('INSERT INTO "Player" ("Nickname", "Name", "Surname", "ClientID") VALUES (%s, %s, %s, %s);',
                        (nickname, name, surname, client_id))

        print("Создаем записи в таблицах Money, Inventory, Zakaz для нового пользователя...")
        connect.execute('INSERT INTO "Money" ("Gold", "Paper", "Gems") VALUES (100, 100, 100) RETURNING "MoneyID";')
        money_id = connect.fetchone()[0]
        print(f"MoneyID: {money_id}")

        connect.execute('INSERT INTO "Inventory" ("DeckID", "CardID") VALUES (NULL, NULL);')
        inventory_id = connect.fetchone()[0]
        print(f"InventoryID: {inventory_id}")

        connect.execute('INSERT INTO "Zakaz" ("PackageID") VALUES (NULL);')
        zakaz_id = connect.fetchone()[0]
        print(f"ZakazID: {zakaz_id}")

        print("Обновляем таблицу Player с ID Money, Inventory, Zakaz...")
        connect.execute('UPDATE "Player" SET "MoneyID" = %s, "InventoryID" = %s, "ZakazID" = %s WHERE "ClientID" = %s;',
                        (money_id, inventory_id, zakaz_id, client_id))

        print("Завершаем транзакцию...")
        connect.connection.commit()
        print("Транзакция завершена.")
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователя: {e}")
        connect.connection.rollback()
        print("Транзакция отменена.")


@bot.message_handler(commands=['open_package'])
def open_package(message):
    player_id = message.chat.id  # Предполагаем, что ID игрока совпадает с ID чата
    package_id = 1  # Замените на логику получения ID пакета
    connect = connection()
    if connect:
        execute_open_package(player_id, package_id, connect)
        connect.close()
    else:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")


# Обработчик команды /buy_package
@bot.message_handler(commands=['buy_package'])
def buy_package_command(message):
    player_id = message.chat.id  # Предполагаем, что ID игрока совпадает с ID чата
    package_id = 1
    connect = connection()
    if connect:
        buy_package(player_id, package_id, connect)
        connect.close()
    else:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных.")


if __name__ == "__main__":
    cur = connection()
    cur.execute('INSERT INTO "Login" ("Login", "Password") VALUES (\'cringe\', \'cringe\') RETURNING "ClientID";')
    client_id = cur.fetchone()[0]
    print(f"ClientID: {client_id}")
