from db_usage import *
import telebot
from telebot import types

bot = telebot.TeleBot('6049690859:AAEXKrZV3i6qQtWBPzO7Tm8J9RzuMImSrIs')

store_id = 1
command = ''
player_id: int


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
    # Сохраняем данные пользователя в базу данных
    connection(save_user_data, name, surname, nickname)

    bot.send_message(message.chat.id, "Ваши данные успешно сохранены!")

def save_user_data(connect: cursor, name: str, surname: str, nickname: str) -> int:
    """
    Функция для сохранения данных пользователя в базу данных.
    """
    try:
        print("Вставляем данные пользователя в таблицу Login...")
        connect.execute('INSERT INTO "Login" ("Login", "Password") VALUES (%s, %s) RETURNING "ClientID";',
                        (nickname, 'default_password'))
        client_id = connect.fetchone()[0]
        print(f"ClientID: {client_id}")

        print("Создаем записи в таблицах Money, Inventory, Zakaz для нового пользователя...")
        connect.execute('INSERT INTO "Money" ("Gold", "Paper", "Gems") VALUES (100, 100, 100) RETURNING "MoneyID";')
        money_id = connect.fetchone()[0]
        print(f"MoneyID: {money_id}")

        connect.execute('INSERT INTO "Zakaz" ("PackageID") VALUES (NULL) RETURNING "ZakazID";')
        zakaz_id = connect.fetchone()[0]
        print(f"ZakazID: {zakaz_id}")

        # Вставляем карту с ID 1 в инвентарь пользователя
        connect.execute('INSERT INTO "Deck" ("Name", "CardID") VALUES (\'default\', 1) RETURNING "DeckID";')
        deck_id = connect.fetchone()[0]
        connect.execute('INSERT INTO "Inventory" ("DeckID", "CardID") VALUES (%s, 1) RETURNING "InventoryID";', (deck_id,))
        inventory_id = connect.fetchone()[0]
        print(f"InventoryID: {inventory_id}")

        print("Вставляем данные пользователя в таблицу Player...")
        connect.execute('INSERT INTO "Player" '
                        '("Nickname", "Name", "Surname", "ClientID", "InventoryID", "ZakazID", "MoneyID")'
                        ' VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING "PlayerID";',
                        (nickname, name, surname, client_id, inventory_id, zakaz_id, money_id))
        global player_id
        player_id = connect.fetchone()[0]
        print(f"PlayerID: {player_id}")

        # Вставляем промокод с ID 1
        connect.execute('INSERT INTO "Player_Promo" ("PlayerID", "PromocodeID") VALUES (%s, 1);', (player_id,))
        print("Промокод добавлен.")

        print("Завершаем транзакцию...")
        connect.connection.commit()
        print("Транзакция завершена.")
    except Exception as e:
        print(f"Ошибка при сохранении данных пользователя: {e}")
        connect.connection.rollback()
        print("Транзакция отменена.")



@bot.message_handler(commands=['open_package'])
def open_package(message):
    package_id = 1
    cards_info = connection(execute_open_package, player_id, package_id)
    if cards_info:
        for card_info in cards_info:
            bot.send_message(message.chat.id, f"CardID: {card_info[0]}, Name: {card_info[1]}, Attack: {card_info[2]}, Health: {card_info[3]}, CategoryID: {card_info[4]}")
    else:
        bot.send_message(message.chat.id, "Карты не найдены.")



# Обработчик команды /buy_package
@bot.message_handler(commands=['buy_package'])
def buy_package_command(message):
    package_id = 1
    result = connection(buy_package, player_id, package_id)
    if result:
        zakaz_id = result[0]
        bot.send_message(message.chat.id, f"Пакет успешно куплен. ID Zakaz: {zakaz_id}")
    else:
        bot.send_message(message.chat.id, "Ошибка при покупке пакета.")

@bot.message_handler(commands=['promocodes'])
def print_player_promocodes_command(message):
    result = connection(print_player_promocodes, player_id)
    if result:
        for row in result:
            bot.send_message(message.chat.id, f"PromocodeID: {row[0]}, Code: {row[1]}")
    else:
        bot.send_message(message.chat.id, "Промокоды не найдены.")

@bot.message_handler(commands=['shop_packages'])
def show_shop_packages_command(message):
    result = connection(show_shop_packages)
    if result:
        for row in result:
            bot.send_message(message.chat.id, f"PackageID: {row[0]}, Name: {row[1]}, Cost: {row[2]}")
    else:
        bot.send_message(message.chat.id, "Пакеты в магазине не найдены.")

@bot.message_handler(commands=['wallet'])
def print_wallet_command(message):
    result = connection(print_wallet, player_id)
    if result:
        for row in result:
            bot.send_message(message.chat.id, f"MoneyID: {row[0]}, Gold: {row[1]}, Paper: {row[2]}, Gems: {row[3]}")
    else:
        bot.send_message(message.chat.id, "Информация о кошельке не найдена.")

@bot.message_handler(commands=['cards_from_inventory'])
def print_cards_from_inventory_command(message):
    result = connection(print_cards_from_inventory, player_id)
    if result:
        for row in result:
            bot.send_message(message.chat.id, f"CardID: {row[0]}, Name: {row[1]}, Attack: {row[2]}, Health: {row[3]}, CategoryID: {row[4]}")
    else:
        bot.send_message(message.chat.id, "Карты в инвентаре не найдены.")


if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except:
            pass

