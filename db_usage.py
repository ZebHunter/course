import psycopg2
from psycopg2._psycopg import cursor
from sshtunnel import SSHTunnelForwarder


def execute_open_package(connect: cursor, player_id: int, package_id: int) -> list:
    connect.execute('SELECT "CardID" FROM "Package_Card" WHERE "PackageID" = %s;', (package_id,))
    card_ids = connect.fetchall()

    if not card_ids:
        print("Package not found or no cards in the package.")
        return []

    cards_info = []
    for card_id in card_ids:

        connect.execute('SELECT "CardID", "Name", "Attack", "Health", "CategoryID" FROM "Card" '
                        'WHERE "CardID" = %s;', (card_id[0],))
        card_info = connect.fetchone()
        if card_info:
            cards_info.append(card_info)
        else:
            print(f"Card with ID {card_id[0]} not found.")

    return cards_info


def print_player_promocodes(connect: cursor, player_id: int ):
    connect.execute('SELECT "Promocode"."PromocodeID", "Promocode"."Code"'
                    'FROM "Promocode"'
                    'JOIN "Player_Promo" ON "Promocode"."PromocodeID" = "Player_Promo"."PromocodeID"'
                    'WHERE "Player_Promo"."PlayerID" = %s;',
                    (player_id,))

    result = connect.fetchall()
    print(result)
    return result


def show_shop_packages(connect: cursor):
    connect.execute('SELECT "Package"."PackageID", "Package"."Name", "Package"."Cost"'
                    'FROM "Package"'
                    'JOIN "Shop" ON "Package"."PackageID" = "Shop"."PackageID";'
                    )
    result = connect.fetchall()

    print(result)

    return result


def print_wallet(connect: cursor, player_id: int):
    connect.execute('SELECT "Money"."MoneyID", "Money"."Gold", "Money"."Paper", "Money"."Gems"'
                    'FROM "Money"'
                    'JOIN "Player" ON "Money"."MoneyID" = "Player"."MoneyID"'
                    'WHERE "Player"."PlayerID" = %s;', (player_id,))
    result = connect.fetchall()
    print(result)
    return result


def print_cards_from_inventory(connect: cursor, player_id: int) -> None:
    connect.execute('SELECT "Card"."CardID", "Card"."Name", "Card"."Attack", "Card"."Health", "Card"."CategoryID"'
                    'FROM "Card"'
                    'JOIN "Deck" ON "Card"."CardID" = "Deck"."CardID"'
                    'JOIN "Inventory" ON "Deck"."DeckID" = "Inventory"."DeckID"'
                    'JOIN "Player" ON "Inventory"."InventoryID" = "Player"."InventoryID"'
                    'WHERE "Player"."PlayerID" = %s;',
                    (player_id,))

    results = connect.fetchall()

    for row in results:
        print(f"CardID: {row[0]}, Name: {row[1]}, Attack: {row[2]}, Health: {row[3]}, CategoryID: {row[4]}")
    return results


def buy_package(connect: cursor, player_id: int, package_id: int) -> list:
    connect.execute('SELECT "Gold" FROM "Money" WHERE "MoneyID" = '
                    '(SELECT "MoneyID" FROM "Player" WHERE "PlayerID" = %s);',
                    (player_id,))
    gold_balance = connect.fetchone()[0]

    if gold_balance < 100:
        print("Недостаточно Gold для покупки пакета.")
        return None

    # Снимаем 100 единиц Gold
    connect.execute(
        'UPDATE "Money" SET "Gold" = "Gold" - 100 '
        'WHERE "MoneyID" = (SELECT "MoneyID" FROM "Player" WHERE "PlayerID" = %s);',
        (player_id,))

    connect.execute('SELECT "ZakazID" FROM "Player" WHERE "PlayerID" = %s;', (player_id,))
    zakaz_id = connect.fetchone()[0]

    if zakaz_id:
        # Обновляем PackageID в таблице Zakaz, используя полученный ZakazID
        connect.execute('UPDATE "Zakaz" SET "PackageID" = %s WHERE "ZakazID" = %s RETURNING "ZakazID";',
                        (package_id, zakaz_id))
        updated_zakaz_id = connect.fetchone()[0]
        return [updated_zakaz_id]
    else:
        print("ZakazID не найден для данного игрока.")
        return None


def connection(db_operation, *args, **kwargs):
    try:
        with SSHTunnelForwarder(
                ('helios.se.ifmo.ru', 2222),
                ssh_username="s335134",
                ssh_password="caau#2135",
                remote_bind_address=('pg', 5432)) as server:
            server.start()
            print("server connected")

            conn = psycopg2.connect(dbname="studs",
                                    user="s335134",
                                    password="RdK6ljdUUmNJnR7T",
                                    host="127.0.0.1",
                                    port=server.local_bind_port)
            conn.autocommit = True
            print("database connected")

            # Создаем курсор
            cursor = conn.cursor()

            result = db_operation(cursor, *args, **kwargs)

            # Закрываем курсор и соединение
            cursor.close()
            conn.close()
            print("database disconnected")
            return result  # Возвращаем результаты выполнения запросов
    except Exception as e:
        print(f"Disconnect: {e}")
        return None  # Возвращаем None в случае ошибки
